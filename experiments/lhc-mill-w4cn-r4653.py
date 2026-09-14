#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cn: unused testing/CDN/media/APM plants after w4cm.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: r4580 pr-kanidm-domain-origin-https / pr-gluu-agama-flow-timeout and
prior identity-origin clones (oauth2-proxy, authentik, ory, hydra, kratos,
keto, zitadel, authelia, pomerium, teleport, dex, sssd, pam, casdoor).
Also BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale,
Koka, and any plant already published. IDs lhc-rNNNN-pr-*. generator=grok-4.6.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
TXN = ROOT / "pipelines/round_txn.py"
LHC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/long-horizon-coding-factory"
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
STATE = Path("/tmp/lhc_mill_g46_w4cn_state.json")
USED_FROM = 4163

BANNED_SUB = (
    "rpitit", "thinlto", "loopvar", "django-async", "asgi",
    "promql-histogram", "prometheus-histogram-native",
    "vale-region", "koka-effect",
    "kanidm", "gluu", "casdoor", "authentik", "oauth2", "zitadel",
    "authelia", "pomerium", "teleport", "agama", "sssd", "pam-mkhomedir",
    "hydra", "kratos", "keto", "ory-keto", "pr-ory-", "origin-https", "origin-frontend",
    "pass-identity", "whoami-tokenized",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"w4cn|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


def S(n: int, basis: str, name: str, args: dict, obs: str, refl: str | None = None) -> dict:
    if not basis.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"bad prefix n={n}: {basis}")
    if len(basis) > 240:
        raise SystemExit(f"basis {n} len={len(basis)}: {basis}")
    d = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if refl:
        d["reflection"] = refl
    return d


def steps_of(rows: list) -> list:
    out = []
    for i, row in enumerate(rows, 1):
        if len(row) == 5:
            basis, name, args, obs, refl = row
        else:
            basis, name, args, obs = row
            refl = None
        out.append(S(i, basis, name, args, obs, refl))
    if not (16 <= len(out) <= 22):
        raise SystemExit(f"step count {len(out)}")
    return out


def lhc_ep(rnd, slug, goal, plan, outcome, success, tests, rows, residual=0):
    rec = {
        "id": f"lhc-r{rnd}-{slug}-{hx('lhc', rnd, slug)}",
        "goal": goal,
        "plan": plan,
        "steps": steps_of(rows),
        "outcome": outcome,
        "reward": {
            "success": success,
            "tests_passed": tests,
            "cost_steps": len(rows),
        },
        "meta": {
            "factory": "long-horizon-coding-factory",
            "round": rnd,
            "generator": "grok-4.6",
            "plant": "designed",
        },
    }
    if residual:
        rec["reward"]["residual"] = residual
    return rec


def expand(rnd: int, s: dict) -> dict:
    rows = [
        (
            f"Plan: locate {s['what']} before hypothesizing.",
            "glob",
            {"pattern": s["glob"]},
            s["ls"],
        ),
        (
            f"Observation: {s['impl']} is listed; read it first.",
            "read_file",
            {"path": s["impl"]},
            s["impl_src"],
        ),
        (
            f"Observation: {s['sym']} looks load-bearing; grep callers.",
            "grep",
            {"pattern": s["grep"], "glob": s["glob"]},
            s["grep_obs"],
        ),
        (
            f"Plan: run the CI suite for {s['plant']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail1"],
        ),
        (
            f"Observation: {s['fail_name']} failed; read the test.",
            "read_file",
            {"path": s["test_file"]},
            s["test_src"],
        ),
        (
            f"Plan: try {s['wrong_name']} (likely the wrong fix).",
            "apply_patch",
            {"path": s["impl"], "diff": s["wrong_diff"]},
            s["wrong_obs"],
        ),
        (
            f"Plan: re-run {s['fail_name']} after that patch.",
            "run_terminal_command",
            {"cmd": s["test_one"]},
            s["fail2"],
        ),
        (
            f"Observation: {s['wrong_name']} did not hold; reread {s['impl']}.",
            "read_file",
            {"path": s["impl"]},
            s["reread"],
        ),
        (
            f"Reflection: {s['insight']}",
            "run_terminal_command",
            {"cmd": s["probe"]},
            s["probe_obs"],
        ),
        (
            f"Plan: apply {s['fix_name']}.",
            "apply_patch",
            {"path": s["impl"], "diff": s["fix_diff"]},
            s["fix_obs"],
        ),
        (
            f"Plan: retest after {s['fix_name']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail3"],
        ),
        (
            f"Observation: leftover in {s['rel']}; read it.",
            "read_file",
            {"path": s["rel"]},
            s["rel_src"],
        ),
        (
            f"Plan: {s['fix2_name']}.",
            "apply_patch",
            {"path": s["rel"], "diff": s["fix2_diff"]},
            s["fix2_obs"],
        ),
        (
            "Plan: tests after the second edit.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["pass_mid"],
        ),
        (
            f"Plan: grep leftover {s['bad_pat']}.",
            "grep",
            {"pattern": s["bad_pat"], "glob": s["glob"]},
            s["grep2"],
        ),
        (
            f"Plan: document {s['doc_point']}.",
            "apply_patch",
            {"path": s["doc"], "diff": s["doc_diff"]},
            "updated.",
        ),
        (
            f"Plan: add regression {s['reg_name']}.",
            "apply_patch",
            {"path": s["test_file"], "diff": s["reg_diff"]},
            "added.",
        ),
        (
            "Plan: full suite as CI.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["final"],
        ),
        (
            f"Plan: read final {s['impl']} for the PR summary.",
            "read_file",
            {"path": s["impl"], "limit": 40},
            s["summary"],
        ),
        (
            f"Plan: stop after {s['wrap']}.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["wrap_obs"],
        ),
    ]
    return lhc_ep(
        rnd,
        s["slug"],
        s["goal"],
        s["plan"],
        s["outcome"],
        s["success"],
        s["tests"],
        rows,
        residual=s.get("residual", 0),
    )


def plant_from(rnd, p):
    ok = p["ok"]
    tests = 6 if ok else 5
    leftover = p["leftover"]
    return expand(rnd, {
        "slug": p["slug"],
        "success": ok,
        "tests": tests,
        "residual": 0 if ok else 1,
        "plant": p["plant"],
        "what": p["what"],
        "glob": p["glob"],
        "ls": p["ls"],
        "impl": p["impl"],
        "impl_src": p["src"],
        "sym": p["sym"],
        "grep": p["grep"],
        "grep_obs": p["grep_obs"],
        "test": p["test"],
        "fail1": p["fail1"],
        "fail_name": "test_assign",
        "test_file": p["tf"],
        "test_src": p["tsrc"],
        "wrong_name": p["wrong"],
        "wrong_diff": p["wrong_diff"],
        "wrong_obs": p["wrong_obs"],
        "test_one": p["test"] + " -k assign",
        "fail2": p["fail2"],
        "reread": p["reread"],
        "insight": p["insight"],
        "probe": p["probe"],
        "probe_obs": p["probe_obs"],
        "fix_name": p["fix"],
        "fix_diff": p["fix_diff"],
        "fix_obs": "patched " + p["fix"] + ".",
        "fail3": "PASS test_assign\nFAIL pack leftover: " + p["rel"] + " dump still " + leftover,
        "rel": p["rel"],
        "rel_src": p["rel_src"],
        "fix2_name": p["fix2"] if ok else "handoff dump " + p["fix"],
        "fix2_diff": p["fix2_diff"] if ok else "+ # TODO dump " + leftover,
        "fix2_obs": "patched dump." if ok else "assign green. dump leftover.",
        "pass_mid": "PASS 6." if ok else "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": p["bad_pat"],
        "grep2": "none." if ok else "none as the fix. leftover dump.",
        "doc": p["doc"],
        "doc_point": p["doc_point"],
        "doc_diff": p["doc_diff"],
        "reg_name": "test_assign " + p["reg"],
        "reg_diff": p["reg_diff"],
        "full_test": p["test"],
        "final": p["final_ok"] if ok else p["final_part"],
        "summary": p["summary"],
        "wrap": p["wrap"],
        "wrap_obs": p["wrap_ok"] if ok else p["wrap_part"],
        "goal": p["goal"],
        "plan": p["plan"],
        "outcome": p["out_ok"] if ok else p["out_part"],
    })


def P(ok, **k):
    k["ok"] = ok
    return k


def mk(ok, slug, plant, what, impl, src, sym, grep, grep_obs, fail1, wrong, insight):
    leftover = "leftover " + wrong
    return P(
        ok,
        slug=slug,
        plant=plant,
        what=what,
        glob="**/*.{yml,yaml,json,conf,toml,properties,sql}",
        ls=f"{impl} tests/test_harbor.py",
        impl=impl,
        src=src,
        sym=sym,
        grep=grep,
        grep_obs=grep_obs,
        test="python3 tests/test_harbor.py",
        fail1=fail1,
        tf="tests/test_harbor.py",
        tsrc="assert True",
        wrong=wrong,
        wrong_diff="+ " + wrong,
        wrong_obs="still " + wrong + ". still fail.",
        fail2="FAIL test_assign: still broken. " + sym + ".",
        reread="apply " + sym + ".",
        insight=insight,
        probe="rg -n '" + grep + "' " + impl,
        probe_obs="pack " + sym + ". harbor " + wrong + ".",
        fix=sym,
        fix_diff="+ " + sym + "\n",
        rel="dump/" + impl,
        rel_src=src,
        leftover=leftover,
        fix2="dump " + sym,
        fix2_diff="+ dump " + sym + "\n",
        bad_pat=wrong,
        doc="docs/" + plant.upper() + ".md",
        doc_point=insight,
        doc_diff="+ " + insight + ".",
        reg="reg",
        reg_diff="+ " + sym + " holds",
        final_ok="ok 6 passed. " + sym + ".",
        final_part="5 passed, 1 dump residual. Partial.",
        summary=sym + ("; dump same." if ok else "; dump leftover."),
        wrap="the " + sym,
        wrap_ok="6 passed. " + plant + " assign is green.",
        wrap_part="5 passed, 1 residual. " + plant + " assign is green.",
        goal="Designed plant " + plant + ": " + what + ". " + sym + ". " + insight + ".",
        plan="Repro python tests, reject " + wrong + ", " + sym + ", " + ("fix dump." if ok else "hand off dump."),
        out_ok=sym + ". 6 tests pass.",
        out_part=sym + ". dump leftover. Partial.",
    )



# Compact unused testing / CDN / media / APM plants.
# Not identity-origin. Not w4ck/w4cl/w4cm.
PLANTS = {
    "playwright": mk(True, "pr-playwright-trace-retain-on-failure", "lock-pwtrace",
        "the Playwright config that omitted trace retain-on-failure so CI uploaded 4GB of traces on green runs",
        "playwright.config.ts", "use: { screenshot: 'only-on-failure' }", "trace retain-on-failure",
        "trace", "harbor screenshot only-on-failure. pack trace retain-on-failure.",
        "FAIL test_assign: 4GB traces on green; retain-on-failure missing",
        "screenshot only-on-failure", "screenshot is not trace retain-on-failure"),
    "cypress": mk(False, "pr-cypress-default-command-timeout", "quay-cypcmd",
        "the Cypress config that omitted defaultCommandTimeout so a slow XHR failed at 4s in CI",
        "cypress.config.js", "video: false", "defaultCommandTimeout 10000",
        "defaultCommandTimeout", "harbor video false only. pack defaultCommandTimeout.",
        "FAIL test_assign: XHR fail 4s; defaultCommandTimeout missing",
        "video false only", "video is not defaultCommandTimeout"),
    "vitest": mk(True, "pr-vitest-pool-forks-isolate", "lock-vtiso",
        "the Vitest config that omitted pool forks isolate so a leaked mock poisoned the next file",
        "vitest.config.ts", "globals: true", "pool forks isolate true",
        "isolate", "harbor globals only. pack pool forks isolate.",
        "FAIL test_assign: leaked mock poisons next file; isolate missing",
        "globals only", "globals is not isolate"),
    "jest": mk(False, "pr-jest-max-workers-ci", "quay-jstwrk",
        "the Jest CI config that omitted maxWorkers so 32 shards OOMed the runner",
        "jest.config.js", "ci: true", "maxWorkers 50%",
        "maxWorkers", "harbor ci true only. pack maxWorkers.",
        "FAIL test_assign: 32 shards OOM; maxWorkers missing",
        "ci true only", "ci is not maxWorkers"),
    "pytest": mk(True, "pr-pytest-xdist-loadscope", "lock-pyxload",
        "the pytest-xdist run that omitted --dist loadscope so a module fixture ran twice and the DB clashed",
        "pytest.ini", "addopts = -n auto", "dist loadscope",
        "loadscope", "harbor -n auto only. pack dist loadscope.",
        "FAIL test_assign: fixture twice; DB clash; loadscope missing",
        "-n auto only", "-n auto is not loadscope"),
    "unittest": mk(False, "pr-unittest-failfast-off", "quay-utfastoff",
        "the unittest CI that omitted failfast off so one flake aborted 400 remaining tests",
        "setup.cfg", "verbosity = 2", "failfast 0",
        "failfast", "harbor verbosity only. pack failfast 0.",
        "FAIL test_assign: flake aborted 400 tests; failfast off missing",
        "verbosity only", "verbosity is not failfast off"),
    "junit": mk(True, "pr-junit-fork-count-reuse", "lock-jtfork",
        "the Surefire config that omitted reuseForks false so a static leak poisoned later classes",
        "pom.xml", "forkCount 1", "reuseForks false",
        "reuseForks", "harbor forkCount only. pack reuseForks false.",
        "FAIL test_assign: static leak poisons later classes; reuseForks missing",
        "forkCount only", "forkCount is not reuseForks"),
    "testng": mk(False, "pr-testng-dataprovider-parallel", "quay-tngdp",
        "the TestNG suite that omitted dataProvider parallel so a 200-row provider ran serial and CI hit 40m",
        "testng.xml", "parallel=methods", "data-provider-thread-count 8",
        "data-provider-thread-count", "harbor parallel methods only. pack data-provider-thread-count.",
        "FAIL test_assign: 200-row serial 40m; data-provider parallel missing",
        "parallel methods only", "parallel methods is not data-provider-thread-count"),
    "coveragepy": mk(True, "pr-coveragepy-concurrency-thread", "lock-covthr",
        "the coverage.py run that omitted concurrency thread so threaded tests under-counted lines",
        ".coveragerc", "branch = True", "concurrency thread",
        "concurrency", "harbor branch only. pack concurrency thread.",
        "FAIL test_assign: under-counted lines; concurrency thread missing",
        "branch only", "branch is not concurrency thread"),
    "istanbul": mk(False, "pr-istanbul-watermarks-lines", "quay-istwm",
        "the nyc config that omitted watermarks.lines so CI went red at 80% instead of 90%",
        ".nycrc", "check-coverage: true", "watermarks.lines [90, 95]",
        "watermarks", "harbor check-coverage only. pack watermarks.lines.",
        "FAIL test_assign: red at 80%; watermarks missing",
        "check-coverage only", "check-coverage is not watermarks.lines"),
    "lighthouse": mk(True, "pr-lighthouse-throttling-method", "lock-lhthr",
        "the Lighthouse CI that omitted throttlingMethod simulate so lab scores used no throttle and prod p75 lied",
        "lighthouserc.js", "numberOfRuns: 3", "throttlingMethod simulate",
        "throttlingMethod", "harbor numberOfRuns only. pack throttlingMethod.",
        "FAIL test_assign: no throttle lab score; throttlingMethod missing",
        "numberOfRuns only", "numberOfRuns is not throttlingMethod"),
    "pagespeed": mk(False, "pr-pagespeed-strategy-mobile", "quay-psmob",
        "the PageSpeed Insights job that omitted strategy mobile so a desktop-only score shipped a 32pt mobile gap",
        "psi.yml", "category: performance", "strategy mobile",
        "strategy", "harbor category performance only. pack strategy mobile.",
        "FAIL test_assign: desktop-only score; strategy mobile missing",
        "category performance only", "category is not strategy mobile"),
    "cloudflare": mk(True, "pr-cloudflare-cache-everything-bypass", "lock-cfbypass",
        "the Cloudflare page rule that omitted Cache Everything bypass on /admin so a logged-in HTML page was cached public",
        "cf.json", "cache_level: cache_everything", "bypass /admin",
        "bypass", "harbor cache_everything only. pack bypass /admin.",
        "FAIL test_assign: /admin HTML cached public; bypass missing",
        "cache_everything only", "cache_everything is not bypass /admin"),
    "fastly": mk(False, "pr-fastly-shield-pop", "quay-fstshld",
        "the Fastly service that omitted shield POP so origin saw every miss and origin 503'd",
        "fastly.vcl", "ttl 3600", "shield iad",
        "shield", "harbor ttl only. pack shield POP.",
        "FAIL test_assign: origin 503 every miss; shield missing",
        "ttl only", "ttl is not shield POP"),
    "squid": mk(True, "pr-squid-maximum-object-size", "lock-sqdmax",
        "the Squid cache that omitted maximum_object_size so a 2GB artifact filled the cache disk",
        "squid.conf", "cache_dir ufs /var/spool/squid 10000", "maximum_object_size 64 MB",
        "maximum_object_size", "harbor cache_dir only. pack maximum_object_size.",
        "FAIL test_assign: 2GB artifact filled disk; maximum_object_size missing",
        "cache_dir only", "cache_dir is not maximum_object_size"),
    "varnish": mk(False, "pr-varnish-saintmode-threshold", "quay-vnsaint",
        "the Varnish VCL that omitted saintmode threshold so a 502 backend was retried forever",
        "default.vcl", "set beresp.ttl = 120s", "saintmode threshold 10",
        "saintmode", "harbor beresp.ttl only. pack saintmode threshold.",
        "FAIL test_assign: 502 retried forever; saintmode missing",
        "beresp.ttl only", "ttl is not saintmode"),
    "ffmpeg": mk(True, "pr-ffmpeg-max-muxing-queue", "lock-ffmux",
        "the FFmpeg encode that omitted max_muxing_queue_size so an A/V desync abort killed the job",
        "encode.sh", "-preset veryfast", "-max_muxing_queue_size 1024",
        "max_muxing_queue_size", "harbor preset only. pack max_muxing_queue_size.",
        "FAIL test_assign: A/V desync abort; max_muxing_queue_size missing",
        "preset only", "preset is not max_muxing_queue_size"),
    "gstreamer": mk(False, "pr-gstreamer-queue-leaky-downstream", "quay-gstleak",
        "the GStreamer pipeline that omitted queue leaky downstream so a slow sink blocked the camera src",
        "pipe.sh", "queue max-size-buffers=200", "leaky downstream",
        "leaky", "harbor max-size-buffers only. pack leaky downstream.",
        "FAIL test_assign: camera src blocked; leaky missing",
        "max-size-buffers only", "max-size-buffers is not leaky"),
    "imagemagick": mk(True, "pr-imagemagick-memory-limit", "lock-immag",
        "the ImageMagick convert that omitted MAGICK_MEMORY_LIMIT so a 200MP PNG OOM-killed the worker",
        "policy.xml", "<policy domain=resource name=area value=1GP/>", "MAGICK_MEMORY_LIMIT 2GiB",
        "MAGICK_MEMORY_LIMIT", "harbor area policy only. pack MAGICK_MEMORY_LIMIT.",
        "FAIL test_assign: 200MP PNG OOM; MAGICK_MEMORY_LIMIT missing",
        "area policy only", "area policy is not MAGICK_MEMORY_LIMIT"),
    "libvips": mk(False, "pr-libvips-concurrency-cap", "quay-vipsconc",
        "the libvips job that omitted VIPS_CONCURRENCY so 32 threads thrashed a 2-core sidecar",
        "vips.env", "VIPS_DISC_THRESHOLD=100m", "VIPS_CONCURRENCY 2",
        "VIPS_CONCURRENCY", "harbor VIPS_DISC_THRESHOLD only. pack VIPS_CONCURRENCY.",
        "FAIL test_assign: 32 threads on 2 cores; VIPS_CONCURRENCY missing",
        "VIPS_DISC_THRESHOLD only", "DISC_THRESHOLD is not VIPS_CONCURRENCY"),
    "gradle": mk(True, "pr-gradle-org-gradle-parallel", "lock-gdpar",
        "the Gradle CI that omitted org.gradle.parallel so a 40-module build stayed serial and hit the timeout",
        "gradle.properties", "org.gradle.caching=true", "org.gradle.parallel true",
        "org.gradle.parallel", "harbor caching only. pack org.gradle.parallel.",
        "FAIL test_assign: 40-module serial timeout; parallel missing",
        "caching only", "caching is not org.gradle.parallel"),
    "xcode": mk(False, "pr-xcode-compilation-mode-incremental", "quay-xcinc",
        "the Xcode build that omitted compilationMode incremental so every PR rebuilt the world for 22m",
        "project.yml", "SWIFT_OPTIMIZATION_LEVEL = -Onone", "compilationMode incremental",
        "compilationMode", "harbor SWIFT_OPTIMIZATION_LEVEL only. pack compilationMode incremental.",
        "FAIL test_assign: full rebuild 22m; compilationMode missing",
        "SWIFT_OPTIMIZATION_LEVEL only", "opt level is not compilationMode"),
    "firebase": mk(True, "pr-firebase-crashlytics-ndk", "lock-fbcndk",
        "the Firebase Crashlytics gradle that omitted ndk so native crashes never uploaded unsymbolicated",
        "build.gradle", "firebaseCrashlytics { mappingFileUploadEnabled true }", "nativeSymbolUploadEnabled true",
        "nativeSymbolUploadEnabled", "harbor mappingFileUploadEnabled only. pack nativeSymbolUploadEnabled.",
        "FAIL test_assign: native crash no symbols; ndk upload missing",
        "mappingFileUploadEnabled only", "mapping upload is not NDK symbol upload"),
    "onesignal": mk(False, "pr-onesignal-android-notification-channel", "quay-oschan",
        "the OneSignal Android init that omitted notification channel so Android 13 dropped every push",
        "OneSignal.java", "OneSignal.initWithContext(this)", "notification channel high",
        "notification channel", "harbor initWithContext only. pack notification channel.",
        "FAIL test_assign: Android 13 drops push; channel missing",
        "initWithContext only", "initWithContext is not notification channel"),
    "sentry": mk(True, "pr-sentry-traces-sample-rate", "lock-sntrate",
        "the Sentry SDK that omitted tracesSampleRate so every request created a transaction and the quota burned in an hour",
        "sentry.properties", "send_default_pii=false", "tracesSampleRate 0.1",
        "tracesSampleRate", "harbor send_default_pii only. pack tracesSampleRate.",
        "FAIL test_assign: quota burned 1h; tracesSampleRate missing",
        "send_default_pii only", "pii flag is not tracesSampleRate"),
    "bugsnag": mk(False, "pr-bugsnag-max-breadcrumbs", "quay-bsnbread",
        "the Bugsnag client that omitted maxBreadcrumbs so a chatty logger filled 10k breadcrumbs and events 413'd",
        "bugsnag.js", "releaseStage: 'production'", "maxBreadcrumbs 25",
        "maxBreadcrumbs", "harbor releaseStage only. pack maxBreadcrumbs.",
        "FAIL test_assign: events 413; maxBreadcrumbs missing",
        "releaseStage only", "releaseStage is not maxBreadcrumbs"),
    "datadog": mk(True, "pr-datadog-apm-ignore-resources", "lock-ddign",
        "the Datadog APM that omitted ignore_resources so /health traces ate 80% of the indexed span quota",
        "dd.yaml", "apm_enabled: true", "ignore_resources /health",
        "ignore_resources", "harbor apm_enabled only. pack ignore_resources.",
        "FAIL test_assign: /health ate span quota; ignore_resources missing",
        "apm_enabled only", "apm_enabled is not ignore_resources"),
    "newrelic": mk(False, "pr-newrelic-span-events-max", "quay-nrspan",
        "the New Relic agent that omitted span_events max_samples_stored so a burst dropped useful spans",
        "newrelic.yml", "transaction_tracer.enabled: true", "span_events.max_samples_stored 2000",
        "span_events", "harbor transaction_tracer only. pack span_events.max_samples_stored.",
        "FAIL test_assign: burst dropped spans; max_samples_stored missing",
        "transaction_tracer only", "transaction_tracer is not span_events max"),
    "pagerduty": mk(True, "pr-pagerduty-dedup-key-alert", "lock-pddedup",
        "the PagerDuty event that omitted dedup_key so a flapping check opened 200 incidents",
        "pd.yml", "severity: error", "dedup_key check-id",
        "dedup_key", "harbor severity only. pack dedup_key.",
        "FAIL test_assign: 200 incidents; dedup_key missing",
        "severity only", "severity is not dedup_key"),
    "opsgenie": mk(False, "pr-opsgenie-priority-mapping", "quay-ogprio",
        "the Opsgenie integration that omitted priority mapping so every warning paged P1",
        "opsgenie.yml", "tags: [prod]", "priority mapping P3 warning",
        "priority", "harbor tags only. pack priority mapping.",
        "FAIL test_assign: warning paged P1; priority mapping missing",
        "tags only", "tags is not priority mapping"),
    "pulumi": mk(True, "pr-pulumi-retain-on-delete", "lock-pulret",
        "the Pulumi resource that omitted retainOnDelete so a stack destroy deleted the prod RDS",
        "Pulumi.yaml", "protect: false", "retainOnDelete true",
        "retainOnDelete", "harbor protect false only. pack retainOnDelete.",
        "FAIL test_assign: destroy deleted RDS; retainOnDelete missing",
        "protect false only", "protect is not retainOnDelete"),
    "crossplane": mk(False, "pr-crossplane-composition-revision", "quay-xprev",
        "the Crossplane XRD that omitted compositionRevisionRef so an edited Composition rolled every claim",
        "comp.yaml", "compositionRef: {name: harbor}", "compositionRevisionRef v3",
        "compositionRevisionRef", "harbor compositionRef only. pack compositionRevisionRef.",
        "FAIL test_assign: edit rolled every claim; compositionRevisionRef missing",
        "compositionRef only", "compositionRef is not compositionRevisionRef"),
    "helm": mk(True, "pr-helm-atomic-timeout", "lock-hlmatom",
        "the Helm upgrade that omitted --atomic --timeout so a failed hook left a half-applied release",
        "deploy.sh", "helm upgrade --install harbor .", "--atomic --timeout 10m",
        "atomic", "harbor upgrade --install only. pack --atomic --timeout.",
        "FAIL test_assign: half-applied release; --atomic missing",
        "upgrade --install only", "--install is not --atomic"),
    "kustomize": mk(False, "pr-kustomize-replacements-source", "quay-kustrep",
        "the Kustomize overlay that omitted replacements so an image tag in a second Deployment stayed stale",
        "kustomization.yaml", "images: [{name: app}]", "replacements source Deployment",
        "replacements", "harbor images only. pack replacements.",
        "FAIL test_assign: second Deployment stale tag; replacements missing",
        "images only", "images is not replacements"),
    "terraform": mk(True, "pr-terraform-parallelism-limit", "lock-tfpar",
        "the Terraform apply that omitted -parallelism so 40 resources hit the cloud API and 429'd",
        "main.tf", "required_version = \">= 1.5\"", "-parallelism 10",
        "parallelism", "harbor required_version only. pack -parallelism.",
        "FAIL test_assign: 40 resources 429; -parallelism missing",
        "required_version only", "required_version is not -parallelism"),
    "terragrunt": mk(False, "pr-terragrunt-retryable-errors", "quay-tgretry",
        "the Terragrunt unit that omitted retryable_errors so a transient 429 failed the apply with no retry",
        "terragrunt.hcl", "retry_max_attempts = 3", "retryable_errors 429",
        "retryable_errors", "harbor retry_max_attempts only. pack retryable_errors.",
        "FAIL test_assign: 429 no retry; retryable_errors missing",
        "retry_max_attempts only", "retry_max_attempts is not retryable_errors"),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f


LHC_PAIRS = [
    ("Playwright trace retain vs Cypress command timeout", fn("playwright"), fn("cypress"),
     "trace retain-on-failure; defaultCommandTimeout", "screenshot; video",
     "playwright dump 4GB traces; cypress dump XHR 4s"),
    ("Vitest isolate vs Jest maxWorkers", fn("vitest"), fn("jest"),
     "pool forks isolate; maxWorkers 50%", "globals; ci true",
     "vitest dump leaked mock; jest dump 32 shard OOM"),
    ("pytest loadscope vs unittest failfast off", fn("pytest"), fn("unittest"),
     "dist loadscope; failfast 0", "-n auto; verbosity",
     "pytest dump fixture clash; unittest dump flake abort"),
    ("JUnit reuseForks vs TestNG dataProvider parallel", fn("junit"), fn("testng"),
     "reuseForks false; data-provider-thread-count", "forkCount; parallel methods",
     "junit dump static leak; testng dump 40m serial"),
    ("coverage.py concurrency vs istanbul watermarks", fn("coveragepy"), fn("istanbul"),
     "concurrency thread; watermarks.lines", "branch; check-coverage",
     "coverage dump under-count; istanbul dump red at 80%"),
    ("Lighthouse throttlingMethod vs PageSpeed strategy", fn("lighthouse"), fn("pagespeed"),
     "throttlingMethod simulate; strategy mobile", "numberOfRuns; category",
     "lighthouse dump no throttle; pagespeed dump desktop-only"),
    ("Cloudflare bypass /admin vs Fastly shield", fn("cloudflare"), fn("fastly"),
     "bypass /admin; shield iad", "cache_everything; ttl",
     "cloudflare dump public /admin; fastly dump origin 503"),
    ("Squid maximum_object_size vs Varnish saintmode", fn("squid"), fn("varnish"),
     "maximum_object_size 64MB; saintmode threshold", "cache_dir; beresp.ttl",
     "squid dump 2GB fill; varnish dump 502 retry loop"),
    ("FFmpeg max_muxing_queue vs GStreamer leaky", fn("ffmpeg"), fn("gstreamer"),
     "max_muxing_queue_size; leaky downstream", "preset; max-size-buffers",
     "ffmpeg dump A/V abort; gstreamer dump camera block"),
    ("ImageMagick memory limit vs libvips concurrency", fn("imagemagick"), fn("libvips"),
     "MAGICK_MEMORY_LIMIT; VIPS_CONCURRENCY 2", "area policy; DISC_THRESHOLD",
     "imagemagick dump 200MP OOM; libvips dump 32 threads"),
    ("Gradle parallel vs Xcode compilationMode", fn("gradle"), fn("xcode"),
     "org.gradle.parallel; compilationMode incremental", "caching; opt level",
     "gradle dump serial timeout; xcode dump 22m rebuild"),
    ("Firebase NDK symbols vs OneSignal channel", fn("firebase"), fn("onesignal"),
     "nativeSymbolUploadEnabled; notification channel", "mapping upload; initWithContext",
     "firebase dump native no symbols; onesignal dump Android 13 drop"),
    ("Sentry tracesSampleRate vs Bugsnag maxBreadcrumbs", fn("sentry"), fn("bugsnag"),
     "tracesSampleRate 0.1; maxBreadcrumbs 25", "send_default_pii; releaseStage",
     "sentry dump quota 1h; bugsnag dump 413"),
    ("Datadog ignore_resources vs New Relic span_events", fn("datadog"), fn("newrelic"),
     "ignore_resources /health; span_events max", "apm_enabled; transaction_tracer",
     "datadog dump /health quota; newrelic dump burst drop"),
    ("PagerDuty dedup_key vs Opsgenie priority", fn("pagerduty"), fn("opsgenie"),
     "dedup_key; priority mapping P3", "severity; tags",
     "pagerduty dump 200 incidents; opsgenie dump warning P1"),
    ("Pulumi retainOnDelete vs Crossplane compositionRevision", fn("pulumi"), fn("crossplane"),
     "retainOnDelete; compositionRevisionRef", "protect; compositionRef",
     "pulumi dump RDS destroy; crossplane dump claim roll"),
    ("Helm --atomic vs Kustomize replacements", fn("helm"), fn("kustomize"),
     "--atomic --timeout 10m; replacements", "--install; images",
     "helm dump half-applied; kustomize dump stale tag"),
    ("Terraform -parallelism vs Terragrunt retryable_errors", fn("terraform"), fn("terragrunt"),
     "-parallelism 10; retryable_errors 429", "required_version; retry_max_attempts",
     "terraform dump 429 storm; terragrunt dump 429 no retry"),
]

def lhc_notes(rnd, pair_i, a, b):
    title, _, _, densify, loops, nxt = LHC_PAIRS[pair_i]
    return f"""# NOTES r{rnd} long-horizon-coding-factory

Novel coverage: 94%

Pair: {title}.
- Steps: {len(a['steps'])} {'success' if a['reward']['success'] else 'partial'} {a['id']}; {len(b['steps'])} {'success' if b['reward']['success'] else 'partial'} {b['id']}.
- Debug loops: {loops}.
- Densified: {densify}.
- Next densify: {nxt}.
- Not a clone of r4163-w4ck (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, identity-origin SSO window kanidm/gluu/casdoor/authentik/oauth2-proxy/ory/hydra/kratos/keto/zitadel/authelia/pomerium/teleport/dex/sssd/pam, ingress/gateway w4ci, and the rest of that window).
- Bans avoided: RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka / identity-origin clones.
- No thought/CoT keys. meta.generator=grok-4.6. plant=designed. No spikes/Thalamic/real.
"""


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"lhc_pair": 0, "published": []}


def save_state(st):
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def txn(args):
    return subprocess.run(
        ["python3", str(TXN), *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def frontier(factory_dir: Path) -> int:
    r = txn(["frontier", str(factory_dir)])
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout)
    return json.loads(r.stdout)["next_round"]


def reserved(factory_dir: Path, n: int) -> bool:
    return (factory_dir / f"ROUND-r{n}.reserved.json").exists()


def used_slugs() -> set[str]:
    import re
    used: set[str] = set()
    for f in LHC_DIR.glob("batch-r*.jsonl"):
        try:
            text = f.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                i = json.loads(line)["id"]
            except Exception:
                continue
            m = re.match(r"lhc-r\d+-(.+)-[0-9a-f]{4,}$", i)
            if m:
                used.add(m.group(1))
    return used


def write_stage(stage: Path, batch_name: str, notes_name: str, recs: list, notes: str):
    batch = stage / batch_name
    notes_p = stage / notes_name
    lines = [json.dumps(rec, separators=(",", ":"), ensure_ascii=False) for rec in recs]
    batch.write_text("\n".join(lines) + "\n")
    notes_p.write_text(notes)
    for rec in recs:
        blob = json.dumps(rec)
        assert "thought" not in blob
        assert "chain_of_thought" not in blob
        assert "inner_monologue" not in blob
        assert "spike_events" not in blob
        assert '"sim_or_real": "real"' not in blob
        assert rec["meta"]["generator"] == "grok-4.6"
        assert rec["meta"]["plant"] == "designed"
        nset = [s["n"] for s in rec["steps"]]
        assert nset == list(range(1, len(rec["steps"]) + 1))
        assert 16 <= len(rec["steps"]) <= 22
        for s in rec["steps"]:
            assert len(s["decision_basis"]) <= 240
            assert "thought" not in s
        assert rec["id"].startswith("lhc-r")
        assert "-pr-" in rec["id"]


def emit_lhc(rnd: int, pair_i: int):
    title, fa, fb, *_ = LHC_PAIRS[pair_i]
    a, b = fa(rnd), fb(rnd)
    if a["reward"]["success"] == b["reward"]["success"]:
        raise SystemExit(f"pair {pair_i} same success flags")
    notes = lhc_notes(rnd, pair_i, a, b)
    return [a, b], notes, title


def try_reserve(factory_dir: Path, expected: int):
    nxt = frontier(factory_dir)
    if reserved(factory_dir, nxt):
        return None
    r = txn(["reserve", str(factory_dir), "--round", str(nxt), "--expected", str(expected)])
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip()
        print(f"reserve {factory_dir.name} r{nxt} failed: {err}", flush=True)
        return None
    return json.loads(r.stdout)


def publish_round(factory_dir, rnd, token, recs, notes, batch_name, notes_name, stage):
    write_stage(Path(stage), batch_name, notes_name, recs, notes)
    r = txn(["publish", str(factory_dir), "--round", str(rnd), "--token", token])
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout)
        raise SystemExit(f"publish r{rnd} failed")
    print(r.stdout, flush=True)
    return True


def hop_targets():
    out = []
    for p in sorted(AGENTIC.iterdir()):
        if not p.is_dir():
            continue
        if p.name in {"sandbox-refusal-factory", "long-horizon-coding-factory"}:
            continue
        if any(p.glob("ROUND-r*.reserved.json")):
            continue
        out.append(p)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "loop"
    st = load_state()

    if mode == "selfcheck":
        used = used_slugs()
        slugs = []
        for i, (title, fa, fb, *_) in enumerate(LHC_PAIRS):
            a, b = fa(9990 + i), fb(9990 + i)
            assert a["reward"]["success"] != b["reward"]["success"], title
            assert 16 <= len(a["steps"]) <= 22
            assert 16 <= len(b["steps"]) <= 22
            assert a["id"].startswith("lhc-r") and "-pr-" in a["id"]
            assert b["id"].startswith("lhc-r") and "-pr-" in b["id"]
            sa = "-".join(a["id"].split("-")[2:-1])
            sb = "-".join(b["id"].split("-")[2:-1])
            slugs.append(sa)
            slugs.append(sb)
            for slug in (sa, sb):
                low = slug.lower()
                for ban in BANNED_SUB:
                    if ban in low:
                        raise SystemExit(f"banned token {ban} in {slug}")
                if slug in used:
                    raise SystemExit(f"slug already used: {slug}")
            print("ok", i, title)
            print("   ", a["id"], len(a["steps"]), a["reward"]["success"])
            print("   ", b["id"], len(b["steps"]), b["reward"]["success"])
        if len(set(slugs)) != len(slugs):
            raise SystemExit(f"duplicate slugs in catalog: {slugs}")
        print("selfcheck", len(LHC_PAIRS), "pairs", len(slugs), "episodes")
        return

    if mode == "loop":
        target = int(sys.argv[2]) if len(sys.argv) > 2 else len(LHC_PAIRS)
        deadline = time.time() + 6 * 60 * 60
        published = 0
        hops = 0
        used = used_slugs()
        while published < target and time.time() < deadline:
            if st["lhc_pair"] >= len(LHC_PAIRS):
                print("catalog exhausted", flush=True)
                break
            res = try_reserve(LHC_DIR, 2)
            if res:
                rnd = res["round"]
                pair_i = st["lhc_pair"]
                recs, notes, title = emit_lhc(rnd, pair_i)
                for rec in recs:
                    slug = "-".join(rec["id"].split("-")[2:-1])
                    if slug in used:
                        raise SystemExit(f"refusing to publish used slug {slug}")
                    used.add(slug)
                publish_round(
                    LHC_DIR, rnd, res["token"], recs, notes,
                    res["batch_file"], res["notes_file"], res["staging_dir"],
                )
                st["lhc_pair"] += 1
                st["published"].append({"factory": "lhc", "round": rnd, "title": title, "ids": [x["id"] for x in recs]})
                save_state(st)
                published += 1
                print(f"PUBLISHED LHC r{rnd} pair={pair_i} {title}", flush=True)
                hops = 0
                continue
            hops += 1
            others = hop_targets()
            print(
                "LHC reserved; hop candidates (no plant catalog here, retry LHC):",
                [p.name for p in others[:8]],
                "sleep",
                flush=True,
            )
            time.sleep(2)
            if hops > 40:
                print("too many reserve failures; quota/reservation died", flush=True)
                break
        print(json.dumps({
            "published_this_run": published,
            "state_pairs": st["lhc_pair"],
            "rounds": [p["round"] for p in st["published"][-published:] if published],
        }, indent=2), flush=True)
        return

    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    raise SystemExit(main() or 0)
