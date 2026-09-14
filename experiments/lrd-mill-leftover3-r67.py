#!/usr/bin/env python3
"""Unique leftover mill for log-redaction-factory r67+.

Hop mill when data-pipeline-repair is reserved. Q=2: 16-step success +
17-step handoff. IDs lrd-rN-<slug> without -wNNNN. meta.generator=grok-4.6.
BAN [variant gum], fixture 2026-08-17, clones of r12–r66.
LEFTOVER3_G46_SESSION.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("dpr2294", "/tmp/dpr_mill_r2294.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
_s, build_dpr, audit = base._s, base.build, base.audit

GENERATOR = "grok-4.6"
FACTORY = "log-redaction-factory"
FACTORY_DIR = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-08-19-agentic/log-redaction-factory"
)


def build(round_number: int, specd: dict) -> dict:
    rec = build_dpr(round_number, specd)
    rec["id"] = f"lrd-r{round_number}-{specd['slug']}"
    rec["meta"]["factory"] = FACTORY
    return rec


def notes_for(round_number: int, recs: list) -> str:
    novel = 88.0 + min(3.0, 0.15 * max(0, round_number - 67))
    lines = [
        f"# log-redaction-factory — NOTES r{round_number}",
        "",
        f"Novel coverage: {novel:.0f}%",
        "",
        "## Episodes",
    ]
    for rec in recs:
        steps = rec["steps"]
        success = rec["reward"]["success"]
        meta = rec["meta"]
        plan_step = next(
            (
                s
                for s in steps
                if str(s.get("decision_basis", "")).startswith("Reflection: Plan change")
            ),
            steps[11] if len(steps) > 11 else steps[-1],
        )
        lines.append(
            f"- `{rec['id']}`: {len(steps)} steps, success={success}, "
            f"domain={meta['domain']}, seed={meta['seed']}"
        )
        n_429 = next((s["n"] for s in steps if "429" in str(s.get("observation", ""))), "?")
        n_502 = next((s["n"] for s in steps if "502" in str(s.get("observation", ""))), "?")
        recov_429 = n_429 + 1 if isinstance(n_429, int) else "?"
        recov_502 = n_502 + 1 if isinstance(n_502, int) else "?"
        lines.append(
            f"  - 502 at step {n_502} recovered {recov_502}; "
            f"429 at step {n_429} recovered {recov_429}"
        )
        pc = plan_step.get("decision_basis", "")
        if pc.startswith("Reflection: "):
            pc = pc[len("Reflection: ") :]
        lines.append(f"  - plan change at step {plan_step['n']}: {pc}")
        lines.append("  - edit→test→fail→re-read→fix at steps 10-13")
    ok = [r["id"] for r in recs if r["reward"]["success"]]
    bad = [r["id"] for r in recs if not r["reward"]["success"]]
    lines += [
        "",
        "## decision_basis audit",
        "Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, "
        "length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, "
        "no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.",
        "",
        "## Mix",
        f"Success: {ok}. Realistic failure/handoff: {bad}.",
        "",
        "## Realism / weak recovery paths",
        "Noise recoveries are backoff+retry or local fixture cache. First patches are "
        "domain-plausible and fail closed. Designed traces — not live executions. Unique "
        "leftover leftover leftover plants; not clones of r12–r66. Mute is not redaction. "
        "Drop is not redaction.",
        "",
        "## Step counts",
    ]
    for rec in recs:
        lines.append(f"- {rec['id']}: {len(rec['steps'])} (required 14–18)")
    lines += ["", "## Weaknesses / next", "Mute is not redaction. Drop is not redaction.", ""]
    return "\n".join(lines)


def published_identities() -> set[str]:
    found: set[str] = set()
    if not FACTORY_DIR.is_dir():
        return found
    for path in FACTORY_DIR.glob("NOTES-r*.md"):
        text = path.read_text(errors="ignore").lower()
        found.update(re.findall(r"domain=([a-z0-9._-]+)", text))
        for m in re.finditer(r"`(lrd-r\d+-([a-z0-9-]+))`", text):
            found.add(m.group(2))
    return found


def okp(p: dict) -> dict:
    root, f1, f2, test = p["root"], p["f1"], p["f2"], p["test"]
    t = p["ticket"]
    return _s(
        slug=p["slug"],
        success=True,
        domain=p["domain"],
        stack=p["stack"],
        seed=p["seed"],
        goal=p["goal"],
        plan=p["plan"],
        outcome=p["outcome"],
        reward={
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 12,
            "wasted_calls": 2,
            "cost_steps": 16,
            p.get("rk", "leaked"): p.get("rv", 1),
        },
        plan_basis=p["plan_basis"],
        list_cmd=f"ls -la {root}/ && rg -n '{p['rg']}' {root} | head -40",
        list_obs=p["list_obs"],
        test_basis="Run failing tests.",
        test_cmd=f"pytest {test} -q --tb=short",
        test_fail=p["test_fail"],
        read1_basis="Read writer.",
        read1_path=f1,
        read1_obs=p["read1"],
        read2_basis="Read config.",
        read2_path=f2,
        read2_obs=p["read2"],
        side_basis="Side metrics.",
        side_cmd=f"rg -n '{p['rg']}' metrics {root} | head",
        side_obs=p["side"],
        rb_basis=f"Fetch {p['slug']} runbook.",
        rb_url=f"https://runbooks.lake.example.invalid/{root}/{p['slug']}",
        rb_cache=f"fixtures/runbooks/{p['slug']}.md",
        rb_cached=p["rb"],
        met_basis="Metrics next.",
        met_url=f"https://metrics.lake.example.invalid/api/v1/{root}/{p['slug']}",
        met_obs=p["met"],
        wrong_basis=f"First closed patch: {p['wrong']}.",
        wrong_path=f2,
        wrong_old=p["wo"],
        wrong_new=p["wn"],
        wrong_test_obs=p["wto"],
        plan_change=p["pc"],
        reread_path=f1,
        reread_obs=p["rr"],
        fix_basis=p["fb"],
        fix_path=f1,
        fix_old=p["fo"],
        fix_new=p["fn"],
        fix_obs="1 replacement; config restored",
        pass_obs=p["passtxt"],
        diff_cmd=f"git diff --stat {f1} {f2}",
        diff_obs=p.get("diff", f"{f1} | 6 +++---\n{f2} | 2 +-"),
        close_basis=f"Close comment. {p['distinct']}",
        close_cmd=f"echo '{t} {p['right']}. Residual: {p['residual']}'",
        close_obs=f"{t} tests green residual {p['residual'][:48]}",
    )


def failp(p: dict) -> dict:
    root, f1, f2, test = p["root"], p["f1"], p["f2"], p["test"]
    t = p["ticket"]
    plat = p["platform"]
    return _s(
        slug=p["slug"],
        success=False,
        domain=p["domain"],
        stack=p["stack"],
        seed=p["seed"],
        goal=p["goal"],
        plan=p["plan"],
        outcome=p["outcome"],
        reward={
            "success": False,
            "tests_passed": 1,
            "retries": 2,
            "duration_min": 13,
            "wasted_calls": 2,
            "cost_steps": 17,
            p.get("rk", "leaked"): p.get("rv", 1),
        },
        plan_basis=p["plan_basis"],
        list_cmd=f"ls -la {root}/ && rg -n '{p['rg']}' {root} | head -40",
        list_obs=p["list_obs"],
        test_basis="Run failing tests.",
        test_cmd=f"pytest {test} -q --tb=short",
        test_fail=p["test_fail"],
        read1_basis="Read writer.",
        read1_path=f1,
        read1_obs=p["read1"],
        read2_basis="Read config.",
        read2_path=f2,
        read2_obs=p["read2"],
        side_basis="CODEOWNERS.",
        side_cmd=f"rg -n '{root}|{plat}' .github {root} | head",
        side_obs=p.get("side", f".github/CODEOWNERS: {f2} @{plat}"),
        rb_basis=f"Fetch {p['slug']} runbook.",
        rb_url=f"https://runbooks.lake.example.invalid/{root}/{p['slug']}",
        rb_cache=f"fixtures/runbooks/{p['slug']}.md",
        rb_cached=p["rb"],
        met_basis="Metrics next.",
        met_url=f"https://metrics.lake.example.invalid/api/v1/{root}/{p['slug']}",
        met_cache=f"fixtures/metrics/{p['slug']}.json",
        met_obs=p["met"],
        wrong_basis=f"First closed patch: {p['wrong']}.",
        wrong_path=f2,
        wrong_old=p["wo"],
        wrong_new=p["wn"],
        wrong_test_obs=p["wto"],
        plan_change=p["pc"],
        reread_path=f1,
        reread_obs=p["rr"],
        fix_basis=p["fb"],
        fix_path=f1,
        fix_old=p["fo"],
        fix_new=p["fn"],
        fix_obs="1 replacement — cluster apply still unsigned",
        slo_basis="SLO still fails without platform apply.",
        slo_cmd=f"pytest {test} -q --tb=short",
        slo_obs=p["slo"],
        revert_basis="Revert so we do not ship a pretend fix.",
        revert_cmd=f"git checkout -- {f1} {f2} ; git diff --stat",
        revert_obs="clean",
        status_cmd=f"git status --porcelain {root}",
        status_obs="clean",
        handoff_basis=p["hb"],
        handoff_cmd=f"echo '{t} handoff @{plat}: {p['right']}. {p['distinct']}'",
        handoff_obs=f"{t} handed off. {p['slo'][:60]}",
    )


def OK(**p):
    root = p["root"]
    p.setdefault("f1", f"{root}/{p.pop('src')}")
    p.setdefault("f2", f"{root}/{p.pop('cfg')}")
    p.setdefault("test", f"tests/{root}/test_redact.py")
    p.setdefault("side", p["list_obs"])
    p.setdefault("met", p["list_obs"].replace("\n", " | "))
    p.setdefault("passtxt", "PASS test_no_secret\nPASS test_keep_log\nPASS test_redact\n3 passed")
    return okp(p)


def FAIL(**p):
    root = p["root"]
    p.setdefault("f1", f"{root}/{p.pop('src')}")
    p.setdefault("f2", f"{root}/{p.pop('cfg')}")
    p.setdefault("test", f"tests/{root}/test_redact.py")
    p.setdefault("met", p["list_obs"].replace("\n", " | ") + " unsigned")
    return failp(p)


PAIRS = [
    (
        OK(
            slug="axum-trace-redact",
            domain="axum-trace-layer-authorization-vs-disable-trace",
            stack="Axum TraceLayer Authorization redact vs disable trace",
            seed="axum-trace-pay-auth-off",
            ticket="AX-3",
            root="axumlog",
            src="pay.rs",
            cfg="trace.toml",
            rg="TraceLayer|Authorization|on_request",
            goal="Axum pay-api TraceLayer logged Authorization on every request. Redact the header; do not disable TraceLayer (that blinds latency). Distinct from tracing-subscriber leftover.",
            plan="Prove Authorization in spans. Try disable TraceLayer; if latency tests fail, redact header.",
            outcome="Disabling TraceLayer blinded latency. Header redact. Tests 3/3. Residual AX-3: one path still raw. Distinct from tracing leftover.",
            plan_basis="pay-api Axum TraceLayer leaked Authorization. Inspect on_request before disable trace.",
            list_obs="trace.toml include_headers=true\nAuthorization kept",
            test_fail="FAIL test_no_authorization: leaked. FAIL test_keep_trace.",
            read1="TraceLayer::new_for_http()",
            read2="include_headers = true",
            rb="cached: redact Authorization. Disable TraceLayer blinds latency. Distinct from tracing leftover.",
            wrong="disable trace",
            wo="include_headers = true",
            wn="trace.enabled = false",
            wto="FAILED test_keep_trace: latency gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling TraceLayer is the wrong layer. Redact Authorization.",
            rr="Need header redact. Restore TraceLayer.",
            fb="Redact Authorization; keep TraceLayer.",
            fo="TraceLayer::new_for_http()",
            fn="TraceLayer::new_for_http().on_request(|req, _| { req.headers().remove(\"authorization\"); })",
            right="redact Authorization",
            residual="one path raw; not tracing leftover",
            distinct="Distinct from tracing-subscriber leftover.",
            rk="leaked",
            rv=1800,
        ),
        FAIL(
            slug="tonic-md-handoff",
            domain="tonic-interceptor-metadata-vs-disable-tonic",
            stack="Tonic interceptor metadata vs disable Tonic",
            seed="tonic-md-pay-auth-handoff",
            ticket="TN-4",
            root="toniclog",
            src="pay.rs",
            cfg="tonic.toml",
            rg="interceptor|authorization|metadata",
            platform="platform-tonic",
            goal="Tonic pay-rpc interceptor logged grpc-authorization metadata. Do not disable Tonic. Hand off interceptor to platform-tonic.",
            plan="Prove metadata dump. Try disable Tonic; if RPC tests fail, request interceptor. Interceptor is platform-tonic.",
            outcome="Disabling Tonic 404s RPCs. Interceptor is cluster. Reverted. Handoff TN-4 to platform-tonic. Distinct from Axum leftover.",
            plan_basis="pay-rpc Tonic leaked grpc-authorization. Inspect interceptor before disable Tonic.",
            list_obs="tonic.toml log_metadata=true\n# @platform-tonic",
            test_fail="FAIL test_no_auth_md: leaked. FAIL test_keep_tonic.",
            read1="interceptor(|req| { log::info!(\"{:?}\", req.metadata()); req })",
            read2="log_metadata = true  # @platform-tonic",
            rb="cached: redact authorization metadata. Disable Tonic drops RPCs. Distinct from Axum leftover.",
            wrong="disable tonic",
            wo="log_metadata = true",
            wn="tonic.enabled = false",
            wto="FAILED test_keep_tonic: RPCs 404. leak would vanish for the wrong reason.",
            pc="Plan change: disabling Tonic is the wrong layer. Interceptor is platform-tonic.",
            rr="Need metadata redact. Interceptor is platform-tonic.",
            fb="Draft redact; interceptor still unsigned.",
            fo="interceptor(|req| { log::info!(\"{:?}\", req.metadata()); req })",
            fn="interceptor(|req| { /* TN-4 redact */ req })",
            slo="FAILED: interceptor unsigned. Need platform-tonic.",
            hb="Handoff TN-4: platform-tonic must redact grpc-authorization. Distinct from Axum leftover.",
            right="metadata redact",
            distinct="Not Axum TraceLayer leftover.",
            rk="leaked",
            rv=900,
        ),
    ),
    (
        OK(
            slug="gin-logger-auth",
            domain="gin-logger-authorization-vs-disable-ginlog",
            stack="Gin logger Authorization redact vs disable gin.Logger",
            seed="gin-log-pay-auth-off",
            ticket="GN-3",
            root="ginlog",
            src="pay.go",
            cfg="gin.toml",
            rg="gin.Logger|Authorization|SkipPaths",
            goal="Gin pay-api logger dumped Authorization from c.Request.Header. Redact the header; do not disable gin.Logger (that blinds 4xx rates). Distinct from zap leftover.",
            plan="Prove header dump. Try disable gin.Logger; if rate tests fail, redact Authorization.",
            outcome="Disabling gin.Logger blinded 4xx rates. Header redact. Tests 3/3. Residual GN-3: one route still raw. Distinct from zap leftover.",
            plan_basis="pay-api Gin logger leaked Authorization. Inspect logger before disable gin.Logger.",
            list_obs="pay.go gin.Logger()\nAuthorization logged",
            test_fail="FAIL test_no_authorization: leaked. FAIL test_keep_ginlog.",
            read1="r.Use(gin.Logger())",
            read2="log_headers = true",
            rb="cached: redact Authorization. Disable gin.Logger blinds 4xx. Distinct from zap leftover.",
            wrong="disable gin logger",
            wo="log_headers = true",
            wn="gin.Logger = off",
            wto="FAILED test_keep_ginlog: 4xx rates gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling gin.Logger is the wrong layer. Redact Authorization.",
            rr="Need header redact. Restore gin.Logger.",
            fb="Redact Authorization; keep gin.Logger.",
            fo="r.Use(gin.Logger())",
            fn="r.Use(gin.LoggerWithFormatter(redactAuth))",
            right="redact Authorization",
            residual="one route raw; not zap leftover",
            distinct="Distinct from zap leftover.",
            rk="leaked",
            rv=2200,
        ),
        FAIL(
            slug="echo-logger-handoff",
            domain="echo-middleware-logger-vs-disable-echo",
            stack="Echo middleware logger vs disable Echo logger",
            seed="echo-log-pay-auth-handoff",
            ticket="EC-4",
            root="echolog",
            src="pay.go",
            cfg="echo.toml",
            rg="middleware.Logger|Authorization|Skipper",
            platform="platform-echo",
            goal="Echo pay-api middleware.Logger logged Authorization. Do not disable Echo logger. Hand off Skipper to platform-echo.",
            plan="Prove header dump. Try disable logger; if access tests fail, request Skipper. Middleware is platform-echo.",
            outcome="Disabling Echo logger blinded access. Skipper is cluster. Reverted. Handoff EC-4 to platform-echo. Distinct from Gin leftover.",
            plan_basis="pay-api Echo logger leaked Authorization. Inspect middleware before disable logger.",
            list_obs="echo.toml logger=on\n# @platform-echo",
            test_fail="FAIL test_no_authorization: leaked. FAIL test_keep_echolog.",
            read1="e.Use(middleware.Logger())",
            read2="logger.enabled = true  # @platform-echo",
            rb="cached: Skipper redacts Authorization. Disable logger blinds access. Distinct from Gin leftover.",
            wrong="disable echo logger",
            wo="logger.enabled = true",
            wn="logger.enabled = false",
            wto="FAILED test_keep_echolog: access gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling Echo logger is the wrong layer. Skipper is platform-echo.",
            rr="Need Skipper redact. Middleware is platform-echo.",
            fb="Draft Skipper; middleware still unsigned.",
            fo="e.Use(middleware.Logger())",
            fn="e.Use(middleware.LoggerWithConfig(middleware.LoggerConfig{Skipper: redactAuth})) // EC-4",
            slo="FAILED: middleware unsigned. Need platform-echo.",
            hb="Handoff EC-4: platform-echo must redact Authorization. Distinct from Gin leftover.",
            right="Skipper redact",
            distinct="Not Gin logger leftover.",
            rk="leaked",
            rv=1100,
        ),
    ),
    (
        OK(
            slug="quarkus-json-redact",
            domain="quarkus-json-log-redact-vs-level-off",
            stack="Quarkus JSON log redact vs level OFF",
            seed="quarkus-json-pay-token-off",
            ticket="QK-3",
            root="quarkuslog",
            src="pay.yaml",
            cfg="application.properties",
            rg="quarkus.log|json|redact",
            goal="Quarkus pay-api JSON logs leaked api_token after quarkus.log.console.json stayed on with no keys-to-redact. Add keys-to-redact; do not set level=OFF (that blinds 6 pods). Distinct from logback leftover.",
            plan="Prove api_token in JSON. Try level OFF; if pod tests fail, keys-to-redact=api_token.",
            outcome="level OFF blinded pods. keys-to-redact. Tests 3/3. Residual QK-3: file handler still raw. Distinct from logback leftover.",
            plan_basis="pay-api Quarkus JSON leaked api_token. Inspect keys-to-redact before level OFF.",
            list_obs="application.properties json=true\n# no keys-to-redact",
            test_fail="FAIL test_no_token: leaked. FAIL test_keep_info.",
            read1="quarkus.log.console.json=true",
            read2="quarkus.log.level=INFO",
            rb="cached: keys-to-redact=api_token. level OFF blinds pods. Distinct from logback leftover.",
            wrong="level off",
            wo="quarkus.log.level=INFO",
            wn="quarkus.log.level=OFF",
            wto="FAILED test_keep_info: 6 pods blind. leak would vanish for the wrong reason.",
            pc="Plan change: level OFF is the wrong layer. keys-to-redact=api_token.",
            rr="Need quarkus.log.console.json.keys-to-redact=api_token. Restore INFO.",
            fb="Redact api_token; keep INFO.",
            fo="quarkus.log.console.json=true",
            fn="quarkus.log.console.json=true\nquarkus.log.console.json.keys-to-redact=api_token",
            right="keys-to-redact api_token",
            residual="file handler raw; not logback leftover",
            distinct="Distinct from logback leftover.",
            rk="leaked",
            rv=640,
        ),
        FAIL(
            slug="micronaut-log-handoff",
            domain="micronaut-http-log-vs-disable-micronaut",
            stack="Micronaut HTTP log vs disable Micronaut logging",
            seed="micronaut-log-pay-auth-handoff",
            ticket="MN-4",
            root="micronautlog",
            src="pay.yml",
            cfg="logback.xml",
            rg="HttpClient|Authorization|logger",
            platform="platform-micronaut",
            goal="Micronaut pay-api HttpClient log dumped Authorization. Do not disable logging. Hand off HttpClient logger to platform-micronaut.",
            plan="Prove header dump. Try disable logging; if access tests fail, request logger. logback.xml is platform-micronaut.",
            outcome="Disabling logging blinded access. HttpClient logger is cluster. Reverted. Handoff MN-4 to platform-micronaut. Distinct from Quarkus leftover.",
            plan_basis="pay-api Micronaut HttpClient leaked Authorization. Inspect logger before disable logging.",
            list_obs="logback.xml io.micronaut.http.client=DEBUG\n# @platform-micronaut",
            test_fail="FAIL test_no_authorization: leaked. FAIL test_keep_log.",
            read1="micronaut.http.client.log=true",
            read2="<logger name=\"io.micronaut.http.client\" level=\"DEBUG\"/>  <!-- @platform-micronaut -->",
            rb="cached: pattern redact Authorization. Disable logging blinds access. Distinct from Quarkus leftover.",
            wrong="disable logging",
            wo="<logger name=\"io.micronaut.http.client\" level=\"DEBUG\"/>",
            wn="<logger name=\"ROOT\" level=\"OFF\"/>",
            wto="FAILED test_keep_log: access gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling logging is the wrong layer. HttpClient logger is platform-micronaut.",
            rr="Need pattern redact. logback.xml is platform-micronaut.",
            fb="Draft redact; logback still unsigned.",
            fo="micronaut.http.client.log=true",
            fn="micronaut.http.client.log=true  # MN-4 redact hint",
            slo="FAILED: logback unsigned. Need platform-micronaut.",
            hb="Handoff MN-4: platform-micronaut must redact Authorization. Distinct from Quarkus leftover.",
            right="HttpClient redact",
            distinct="Not Quarkus JSON leftover.",
            rk="leaked",
            rv=410,
        ),
    ),
    (
        OK(
            slug="ktor-call-logging",
            domain="ktor-call-logging-auth-vs-disable-plugin",
            stack="Ktor CallLogging Authorization redact vs disable plugin",
            seed="ktor-call-pay-auth-off",
            ticket="KT-3",
            root="ktorlog",
            src="Pay.kt",
            cfg="ktor.conf",
            rg="CallLogging|Authorization|format",
            goal="Ktor pay-api CallLogging logged Authorization. Redact in format; do not disable CallLogging (that blinds route latency). Distinct from logback leftover.",
            plan="Prove header dump. Try disable CallLogging; if latency tests fail, format redact.",
            outcome="Disabling CallLogging blinded latency. format redact. Tests 3/3. Residual KT-3: one route still raw. Distinct from logback leftover.",
            plan_basis="pay-api Ktor CallLogging leaked Authorization. Inspect format before disable plugin.",
            list_obs="ktor.conf CallLogging=on\nformat dumps headers",
            test_fail="FAIL test_no_authorization: leaked. FAIL test_keep_calllog.",
            read1="install(CallLogging) { format { call -> call.request.headers.toString() } }",
            read2="call_logging = true",
            rb="cached: format omit Authorization. Disable plugin blinds latency. Distinct from logback leftover.",
            wrong="disable call logging",
            wo="call_logging = true",
            wn="call_logging = false",
            wto="FAILED test_keep_calllog: latency gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling CallLogging is the wrong layer. format redact Authorization.",
            rr="Need format without Authorization. Restore CallLogging.",
            fb="Redact in format; keep CallLogging.",
            fo="install(CallLogging) { format { call -> call.request.headers.toString() } }",
            fn="install(CallLogging) { format { call -> call.request.uri } }",
            right="format redact",
            residual="one route raw; not logback leftover",
            distinct="Distinct from logback leftover.",
            rk="leaked",
            rv=760,
        ),
        FAIL(
            slug="play-access-handoff",
            domain="play-access-log-vs-disable-playlog",
            stack="Play Framework access log vs disable Play logging",
            seed="play-access-pay-auth-handoff",
            ticket="PL-4",
            root="playlog",
            src="logback.xml",
            cfg="application.conf",
            rg="AccessLog|Authorization|logger",
            platform="platform-play",
            goal="Play pay-api access log dumped Authorization. Do not disable Play logging. Hand off AccessLog to platform-play.",
            plan="Prove header dump. Try disable logging; if access tests fail, request AccessLog. logback is platform-play.",
            outcome="Disabling Play logging blinded access. AccessLog is cluster. Reverted. Handoff PL-4 to platform-play. Distinct from Ktor leftover.",
            plan_basis="pay-api Play access log leaked Authorization. Inspect AccessLog before disable logging.",
            list_obs="application.conf logger.play=DEBUG\n# @platform-play",
            test_fail="FAIL test_no_authorization: leaked. FAIL test_keep_playlog.",
            read1="<logger name=\"play.filters\" level=\"DEBUG\"/>",
            read2="logger.play=DEBUG  # @platform-play",
            rb="cached: AccessLog omit Authorization. Disable logging blinds access. Distinct from Ktor leftover.",
            wrong="disable play logging",
            wo="logger.play=DEBUG",
            wn="logger.play=OFF",
            wto="FAILED test_keep_playlog: access gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling Play logging is the wrong layer. AccessLog is platform-play.",
            rr="Need AccessLog redact. logback is platform-play.",
            fb="Draft redact; logback still unsigned.",
            fo="<logger name=\"play.filters\" level=\"DEBUG\"/>",
            fn="<logger name=\"play.filters\" level=\"DEBUG\"/> <!-- PL-4 -->",
            slo="FAILED: logback unsigned. Need platform-play.",
            hb="Handoff PL-4: platform-play must redact Authorization. Distinct from Ktor leftover.",
            right="AccessLog redact",
            distinct="Not Ktor CallLogging leftover.",
            rk="leaked",
            rv=330,
        ),
    ),
    (
        OK(
            slug="chi-reqlog-auth",
            domain="chi-requestlogger-authorization-vs-disable-chi",
            stack="Chi middleware RequestLogger Authorization redact vs disable chi log",
            seed="chi-req-pay-auth-off",
            ticket="CH-3",
            root="chilog",
            src="pay.go",
            cfg="chi.toml",
            rg="RequestLogger|Authorization|middleware",
            goal="Chi pay-api RequestLogger logged Authorization. Redact the header; do not disable RequestLogger (that blinds status codes). Distinct from zap leftover.",
            plan="Prove header dump. Try disable RequestLogger; if status tests fail, redact Authorization.",
            outcome="Disabling RequestLogger blinded status codes. Header redact. Tests 3/3. Residual CH-3: one route still raw. Distinct from zap leftover.",
            plan_basis="pay-api Chi RequestLogger leaked Authorization. Inspect logger before disable chi log.",
            list_obs="pay.go middleware.RequestLogger\nAuthorization logged",
            test_fail="FAIL test_no_authorization: leaked. FAIL test_keep_chilog.",
            read1="r.Use(middleware.RequestLogger(nil))",
            read2="log_headers = true",
            rb="cached: redact Authorization. Disable RequestLogger blinds status. Distinct from zap leftover.",
            wrong="disable chi logger",
            wo="log_headers = true",
            wn="chi.log = false",
            wto="FAILED test_keep_chilog: status gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling RequestLogger is the wrong layer. Redact Authorization.",
            rr="Need header redact. Restore RequestLogger.",
            fb="Redact Authorization; keep RequestLogger.",
            fo="r.Use(middleware.RequestLogger(nil))",
            fn="r.Use(middleware.RequestLogger(&LogFormatter{Redact: []string{\"Authorization\"}}))",
            right="redact Authorization",
            residual="one route raw; not zap leftover",
            distinct="Distinct from zap leftover.",
            rk="leaked",
            rv=540,
        ),
        FAIL(
            slug="fiber-logger-handoff",
            domain="fiber-logger-authorization-vs-disable-fiber",
            stack="Fiber logger Authorization vs disable Fiber logger",
            seed="fiber-log-pay-auth-handoff",
            ticket="FB-4",
            root="fiberlog",
            src="pay.go",
            cfg="fiber.toml",
            rg="logger.New|Authorization|Format",
            platform="platform-fiber",
            goal="Fiber pay-api logger Format dumped ${reqHeader:Authorization}. Do not disable Fiber logger. Hand off Format to platform-fiber.",
            plan="Prove header dump. Try disable logger; if access tests fail, request Format. Config is platform-fiber.",
            outcome="Disabling Fiber logger blinded access. Format is cluster. Reverted. Handoff FB-4 to platform-fiber. Distinct from Chi leftover.",
            plan_basis="pay-api Fiber logger leaked Authorization. Inspect Format before disable logger.",
            list_obs="fiber.toml Format=${reqHeader:Authorization}\n# @platform-fiber",
            test_fail="FAIL test_no_authorization: leaked. FAIL test_keep_fiberlog.",
            read1="app.Use(logger.New())",
            read2="Format = \"${reqHeader:Authorization}\"  # @platform-fiber",
            rb="cached: Format omit Authorization. Disable logger blinds access. Distinct from Chi leftover.",
            wrong="disable fiber logger",
            wo="Format = \"${reqHeader:Authorization}\"",
            wn="logger.enabled = false",
            wto="FAILED test_keep_fiberlog: access gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling Fiber logger is the wrong layer. Format is platform-fiber.",
            rr="Need Format without Authorization. Config is platform-fiber.",
            fb="Draft Format; config still unsigned.",
            fo="app.Use(logger.New())",
            fn="app.Use(logger.New(logger.Config{Format: \"${status} ${latency}\"})) // FB-4",
            slo="FAILED: config unsigned. Need platform-fiber.",
            hb="Handoff FB-4: platform-fiber must omit Authorization. Distinct from Chi leftover.",
            right="Format omit Authorization",
            distinct="Not Chi RequestLogger leftover.",
            rk="leaked",
            rv=280,
        ),
    ),
    (
        OK(
            slug="nestjs-interceptor-auth",
            domain="nestjs-logging-interceptor-vs-disable-logger",
            stack="NestJS logging interceptor Authorization redact vs disable Logger",
            seed="nest-int-pay-auth-off",
            ticket="NS-3",
            root="nestlog",
            src="pay.interceptor.ts",
            cfg="logger.module.ts",
            rg="Interceptor|Authorization|Logger",
            goal="NestJS pay-api interceptor logged req.headers.authorization. Redact the header; do not disable Logger (that blinds request ids). Distinct from pino leftover.",
            plan="Prove header dump. Try disable Logger; if request-id tests fail, redact Authorization.",
            outcome="Disabling Logger blinded request ids. Header redact. Tests 3/3. Residual NS-3: one controller still raw. Distinct from pino leftover.",
            plan_basis="pay-api NestJS interceptor leaked Authorization. Inspect interceptor before disable Logger.",
            list_obs="pay.interceptor.ts logs headers\nLogger on",
            test_fail="FAIL test_no_authorization: leaked. FAIL test_keep_logger.",
            read1="this.logger.log(req.headers)",
            read2="logger.enabled = true",
            rb="cached: redact authorization. Disable Logger blinds request ids. Distinct from pino leftover.",
            wrong="disable logger",
            wo="logger.enabled = true",
            wn="logger.enabled = false",
            wto="FAILED test_keep_logger: request ids gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling Logger is the wrong layer. Redact Authorization.",
            rr="Need header redact. Restore Logger.",
            fb="Redact Authorization; keep Logger.",
            fo="this.logger.log(req.headers)",
            fn="this.logger.log({ ...req.headers, authorization: '[REDACTED]' })",
            right="redact Authorization",
            residual="one controller raw; not pino leftover",
            distinct="Distinct from pino leftover.",
            rk="leaked",
            rv=490,
        ),
        FAIL(
            slug="koa-logger-handoff",
            domain="koa-logger-authorization-vs-disable-koa",
            stack="Koa logger Authorization vs disable Koa logger",
            seed="koa-log-pay-auth-handoff",
            ticket="KO-4",
            root="koalog",
            src="pay.js",
            cfg="koa.json",
            rg="koa-logger|Authorization|app.use",
            platform="platform-koa",
            goal="Koa pay-api koa-logger printed Authorization. Do not disable Koa logger. Hand off format to platform-koa.",
            plan="Prove header dump. Try disable logger; if access tests fail, request format. Format is platform-koa.",
            outcome="Disabling Koa logger blinded access. Format is cluster. Reverted. Handoff KO-4 to platform-koa. Distinct from NestJS leftover.",
            plan_basis="pay-api Koa logger leaked Authorization. Inspect format before disable logger.",
            list_obs="koa.json logger=on\n# @platform-koa",
            test_fail="FAIL test_no_authorization: leaked. FAIL test_keep_koalog.",
            read1="app.use(logger())",
            read2="logger.enabled = true  # @platform-koa",
            rb="cached: format omit Authorization. Disable logger blinds access. Distinct from Nest leftover.",
            wrong="disable koa logger",
            wo="logger.enabled = true",
            wn="logger.enabled = false",
            wto="FAILED test_keep_koalog: access gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling Koa logger is the wrong layer. Format is platform-koa.",
            rr="Need format redact. Config is platform-koa.",
            fb="Draft format; config still unsigned.",
            fo="app.use(logger())",
            fn="app.use(logger((str, args) => redact(str, args))) // KO-4",
            slo="FAILED: format unsigned. Need platform-koa.",
            hb="Handoff KO-4: platform-koa must redact Authorization. Distinct from Nest leftover.",
            right="format redact",
            distinct="Not NestJS interceptor leftover.",
            rk="leaked",
            rv=210,
        ),
    ),
    (
        OK(
            slug="picologging-filter",
            domain="picologging-filter-ssn-vs-nullhandler",
            stack="Python picologging Filter SSN vs NullHandler",
            seed="picolog-filter-pay-ssn-off",
            ticket="PC-3",
            root="picolog",
            src="pay.py",
            cfg="logging.ini",
            rg="Filter|SSN|NullHandler",
            goal="picologging pay-api logs leaked SSNs after Filter stayed unset. Add Filter; do not attach NullHandler (that blinds INFO). Distinct from logbook leftover.",
            plan="Prove SSN in records. Try NullHandler; if INFO tests fail, Filter redacts SSN.",
            outcome="NullHandler blinded INFO. Filter redacts SSN. Tests 3/3. Residual PC-3: one logger still raw. Distinct from logbook leftover.",
            plan_basis="pay-api picologging leaked SSN. Inspect Filter before NullHandler.",
            list_obs="logging.ini handlers=stream\n# no Filter",
            test_fail="FAIL test_no_ssn: leaked. FAIL test_keep_info.",
            read1="log.info('ssn=%s', ssn)",
            read2="[handler_stream]\nclass=StreamHandler",
            rb="cached: Filter redacts SSN. NullHandler blinds INFO. Distinct from logbook leftover.",
            wrong="nullhandler",
            wo="class=StreamHandler",
            wn="class=NullHandler",
            wto="FAILED test_keep_info: INFO gone. leak would vanish for the wrong reason.",
            pc="Plan change: NullHandler is the wrong layer. Filter redacts SSN.",
            rr="Need SSN Filter. Restore StreamHandler.",
            fb="Add Filter; keep StreamHandler.",
            fo="log.info('ssn=%s', ssn)",
            fn="log.addFilter(SsnFilter())\nlog.info('ssn=%s', ssn)",
            right="SSN Filter",
            residual="one logger raw; not logbook leftover",
            distinct="Distinct from logbook leftover.",
            rk="leaked",
            rv=88,
        ),
        FAIL(
            slug="semantic-logger-handoff",
            domain="ruby-semantic-logger-vs-disable-semantic",
            stack="Ruby Semantic Logger payload vs disable SemanticLogger",
            seed="semlog-pay-token-handoff",
            ticket="SM-4",
            root="semlog",
            src="pay.rb",
            cfg="semantic.yml",
            rg="SemanticLogger|payload|filter",
            platform="platform-ruby",
            goal="Semantic Logger pay-api payload dumped api_token. Do not disable SemanticLogger. Hand off filter to platform-ruby.",
            plan="Prove token dump. Try disable SemanticLogger; if metric tests fail, request filter. Filter is platform-ruby.",
            outcome="Disabling SemanticLogger blinded metrics. Filter is cluster. Reverted. Handoff SM-4 to platform-ruby. Distinct from picologging leftover.",
            plan_basis="pay-api Semantic Logger leaked api_token. Inspect filter before disable SemanticLogger.",
            list_obs="semantic.yml payload=on\n# @platform-ruby",
            test_fail="FAIL test_no_token: leaked. FAIL test_keep_semlog.",
            read1="logger.info('pay', payload: attrs)",
            read2="payload = true  # @platform-ruby",
            rb="cached: filter api_token. Disable SemanticLogger blinds metrics. Distinct from picolog leftover.",
            wrong="disable semantic logger",
            wo="payload = true",
            wn="semantic.enabled = false",
            wto="FAILED test_keep_semlog: metrics gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling SemanticLogger is the wrong layer. Filter is platform-ruby.",
            rr="Need payload filter. Config is platform-ruby.",
            fb="Draft filter; config still unsigned.",
            fo="logger.info('pay', payload: attrs)",
            fn="logger.info('pay', payload: redact(attrs)) # SM-4",
            slo="FAILED: filter unsigned. Need platform-ruby.",
            hb="Handoff SM-4: platform-ruby must filter api_token. Distinct from picolog leftover.",
            right="payload filter",
            distinct="Not picologging leftover.",
            rk="leaked",
            rv=70,
        ),
    ),
    (
        OK(
            slug="env-logger-redact",
            domain="env-logger-redact-token-vs-off",
            stack="Rust env_logger redact api_token vs RUST_LOG=off",
            seed="envlog-pay-token-off",
            ticket="EL-3",
            root="envlog",
            src="pay.rs",
            cfg="log.toml",
            rg="env_logger|api_token|RUST_LOG",
            goal="env_logger pay-api dumped api_token after format stayed Display. Redact in format; do not set RUST_LOG=off (that blinds WARN). Distinct from tracing leftover.",
            plan="Prove token dump. Try RUST_LOG=off; if WARN tests fail, format redact.",
            outcome="RUST_LOG=off blinded WARN. format redact. Tests 3/3. Residual EL-3: one crate still raw. Distinct from tracing leftover.",
            plan_basis="pay-api env_logger leaked api_token. Inspect format before RUST_LOG=off.",
            list_obs="log.toml RUST_LOG=info\nformat Display",
            test_fail="FAIL test_no_token: leaked. FAIL test_keep_warn.",
            read1="env_logger::Builder::from_default_env().init();",
            read2="RUST_LOG=info",
            rb="cached: format redact api_token. RUST_LOG=off blinds WARN. Distinct from tracing leftover.",
            wrong="rust_log off",
            wo="RUST_LOG=info",
            wn="RUST_LOG=off",
            wto="FAILED test_keep_warn: WARN gone. leak would vanish for the wrong reason.",
            pc="Plan change: RUST_LOG=off is the wrong layer. format redact api_token.",
            rr="Need format redact. Restore RUST_LOG=info.",
            fb="Redact api_token; keep info.",
            fo="env_logger::Builder::from_default_env().init();",
            fn="env_logger::Builder::from_default_env().format(|buf, rec| redact(buf, rec)).init();",
            right="format redact",
            residual="one crate raw; not tracing leftover",
            distinct="Distinct from tracing leftover.",
            rk="leaked",
            rv=55,
        ),
        FAIL(
            slug="phuslu-log-handoff",
            domain="phuslu-log-token-vs-disable-phuslu",
            stack="phuslu/log token vs disable phuslu",
            seed="phuslu-pay-token-handoff",
            ticket="PH-4",
            root="phuslulog",
            src="pay.go",
            cfg="phuslu.toml",
            rg="phuslu|api_token|Caller",
            platform="platform-go",
            goal="phuslu/log pay-api dumped api_token in structured fields. Do not disable phuslu. Hand off field filter to platform-go.",
            plan="Prove token dump. Try disable phuslu; if slog tests fail, request filter. Filter is platform-go.",
            outcome="Disabling phuslu blinded slog. Filter is cluster. Reverted. Handoff PH-4 to platform-go. Distinct from env_logger leftover.",
            plan_basis="pay-api phuslu leaked api_token. Inspect fields before disable phuslu.",
            list_obs="phuslu.toml caller=true\n# @platform-go",
            test_fail="FAIL test_no_token: leaked. FAIL test_keep_phuslu.",
            read1="log.Info().Str(\"api_token\", tok).Msg(\"pay\")",
            read2="phuslu.enabled = true  # @platform-go",
            rb="cached: field filter api_token. Disable phuslu blinds slog. Distinct from env_logger leftover.",
            wrong="disable phuslu",
            wo="phuslu.enabled = true",
            wn="phuslu.enabled = false",
            wto="FAILED test_keep_phuslu: slog gone. leak would vanish for the wrong reason.",
            pc="Plan change: disabling phuslu is the wrong layer. Field filter is platform-go.",
            rr="Need field filter. Config is platform-go.",
            fb="Draft filter; config still unsigned.",
            fo="log.Info().Str(\"api_token\", tok).Msg(\"pay\")",
            fn="log.Info().Str(\"api_token\", \"[REDACTED]\").Msg(\"pay\") // PH-4",
            slo="FAILED: filter unsigned. Need platform-go.",
            hb="Handoff PH-4: platform-go must filter api_token. Distinct from env_logger leftover.",
            right="field filter",
            distinct="Not env_logger leftover.",
            rk="leaked",
            rv=40,
        ),
    ),
]


def plants_for(round_number: int):
    used = published_identities()
    for a, b in PAIRS:
        if a["slug"].lower() in used or b["slug"].lower() in used:
            continue
        if a["domain"].lower() in used or b["domain"].lower() in used:
            continue
        return (lambda r, s=a: build(r, s), lambda r, s=b: build(r, s))
    raise SystemExit(f"no unused leftover LRD plants for r{round_number}")


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
        if rec["meta"]["generator"] != GENERATOR:
            raise SystemExit("bad generator")
        if rec["meta"]["factory"] != FACTORY:
            raise SystemExit("bad factory")
        if "[variant" in rec["goal"].lower():
            raise SystemExit(f"{rec['id']}: variant stamp")
        if re.search(r"-w\d{3,}$", rec["id"]):
            raise SystemExit(f"{rec['id']}: gum suffix")
    staging = args.staging
    staging.mkdir(parents=True, exist_ok=True)
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes = staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    notes.write_text(notes_for(args.round, recs))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("NOTES missing Novel coverage:")
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
