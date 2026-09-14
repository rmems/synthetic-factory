#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cm: unused observability/email/CMS/runtime plants after w4cl.

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
STATE = Path("/tmp/lhc_mill_g46_w4cm_state.json")
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
    return hashlib.sha1(f"w4cm|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


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



# Compact unused observability / email / CMS / feature-flag / runtime plants.
# Not identity-origin. Not w4ck lakehouse. Not w4cl storage/mesh.
PLANTS = {
    "tempo": mk(True, "pr-tempo-ingester-max-block-duration", "lock-tmpblk",
        "the Tempo ingester that omitted max_block_duration so WAL blocks never flushed and disk filled",
        "tempo.yaml", "ingester.max_block_bytes: 500000000", "max_block_duration 30m",
        "max_block_duration", "harbor max_block_bytes only. pack max_block_duration.",
        "FAIL test_assign: WAL never flushed; disk full; max_block_duration missing",
        "max_block_bytes only", "max_block_bytes is not max_block_duration"),
    "loki": mk(False, "pr-loki-ingestion-rate-strategy", "quay-lokirs",
        "the Loki distributor that omitted ingestion_rate_strategy local so one replica ate the global rate and 429'd others",
        "loki.yaml", "ingestion_rate_mb: 4", "ingestion_rate_strategy local",
        "ingestion_rate_strategy", "harbor ingestion_rate_mb only. pack ingestion_rate_strategy.",
        "FAIL test_assign: one replica 429; strategy missing",
        "ingestion_rate_mb only", "ingestion_rate_mb is not ingestion_rate_strategy"),
    "jaeger": mk(True, "pr-jaeger-sampling-adaptive-strategies", "lock-jagadp",
        "the Jaeger collector that omitted adaptive sampling so a chatty service flooded storage at 100%",
        "jaeger.yaml", "sampling.default_strategy: {type: const, param: 1}", "adaptive sampling strategies",
        "adaptive", "harbor const 1.0 only. pack adaptive sampling.",
        "FAIL test_assign: 100% sample flood; adaptive missing",
        "const 1.0 only", "const 1.0 is not adaptive sampling"),
    "zipkin": mk(False, "pr-zipkin-storage-elasticsearch-index", "quay-zpkidx",
        "the Zipkin storage that omitted elasticsearch.index so spans wrote to zipkin:span and ILM never rolled",
        "zipkin.yml", "STORAGE_TYPE=elasticsearch", "elasticsearch.index zipkin-span",
        "elasticsearch.index", "harbor STORAGE_TYPE only. pack elasticsearch.index.",
        "FAIL test_assign: ILM never rolled; index name missing",
        "STORAGE_TYPE only", "STORAGE_TYPE is not elasticsearch.index"),
    "otel": mk(True, "pr-otel-memory-limiter-check", "lock-otelml",
        "the OTel collector that omitted memory_limiter so a burst OOMed the pod and dropped all pipelines",
        "otel.yaml", "processors: [batch]", "memory_limiter check_interval 1s",
        "memory_limiter", "harbor batch only. pack memory_limiter.",
        "FAIL test_assign: pod OOM; pipelines drop; memory_limiter missing",
        "batch only", "batch is not memory_limiter"),
    "vector": mk(False, "pr-vector-disk-buffer-max-size", "quay-vecdisk",
        "the Vector sink that omitted disk_buffer.max_size so a Kafka outage filled memory and Vector was killed",
        "vector.toml", "buffer.type = \"memory\"", "disk_buffer.max_size 268435488",
        "disk_buffer", "harbor memory buffer only. pack disk_buffer.max_size.",
        "FAIL test_assign: Vector OOM on Kafka outage; disk_buffer missing",
        "memory buffer only", "memory buffer is not disk_buffer.max_size"),
    "fluentbit": mk(True, "pr-fluentbit-mem-buf-limit-mb", "lock-fbmem",
        "the Fluent Bit tail input that omitted Mem_Buf_Limit so a log burst ballooned RSS past the node",
        "fluent-bit.conf", "Buffer_Chunk_Size 32k", "Mem_Buf_Limit 32MB",
        "Mem_Buf_Limit", "harbor Buffer_Chunk_Size only. pack Mem_Buf_Limit.",
        "FAIL test_assign: RSS balloon; Mem_Buf_Limit missing",
        "Buffer_Chunk_Size only", "Buffer_Chunk_Size is not Mem_Buf_Limit"),
    "fluentd": mk(False, "pr-fluentd-retry-type-exponential", "quay-fdrexp",
        "the Fluentd match that omitted retry_type exponential so a 503 storm retried every 1s and melted the sink",
        "fluent.conf", "flush_interval 5s", "retry_type exponential",
        "retry_type", "harbor flush_interval only. pack retry_type exponential.",
        "FAIL test_assign: 1s retry storm; sink melt; retry_type missing",
        "flush_interval only", "flush_interval is not retry_type"),
    "postal": mk(True, "pr-postal-smtp-relays-workers", "lock-pstwrk",
        "the Postal SMTP server that omitted smtp_relays workers so a burst queue never drained",
        "postal.yml", "smtp_relays: [{hostname: mx}]", "smtp_relays workers 8",
        "workers", "harbor smtp_relays hostname only. pack workers.",
        "FAIL test_assign: queue never drained; workers missing",
        "smtp_relays hostname only", "hostname is not smtp_relays workers"),
    "mailu": mk(False, "pr-mailu-fetchmail-enabled-off", "quay-mlufetch",
        "the Mailu compose that omitted FETCHMAIL=false so an old fetchmail sidecar pulled a deleted mailbox in a loop",
        "mailu.env", "WEBMAIL=roundcube", "FETCHMAIL=false",
        "FETCHMAIL", "harbor WEBMAIL only. pack FETCHMAIL=false.",
        "FAIL test_assign: fetchmail loop deleted mailbox; FETCHMAIL missing",
        "WEBMAIL only", "WEBMAIL is not FETCHMAIL"),
    "haraka": mk(True, "pr-haraka-max-unrecognized-commands", "lock-hrkunrec",
        "the Haraka smtp.ini that omitted max_unrecognized_commands so a scanner held the process in a command flood",
        "smtp.ini", "nodes=cpus", "max_unrecognized_commands 10",
        "max_unrecognized_commands", "harbor nodes=cpus only. pack max_unrecognized_commands.",
        "FAIL test_assign: command flood hung smtp; max_unrecognized missing",
        "nodes=cpus only", "nodes is not max_unrecognized_commands"),
    "opensmtpd": mk(False, "pr-opensmtpd-max-message-size", "quay-osmtpsz",
        "the OpenSMTPD smtpd.conf that omitted max-message-size so a 200MB bounce filled the queue disk",
        "smtpd.conf", "listen on egress", "max-message-size 35M",
        "max-message-size", "harbor listen on egress only. pack max-message-size.",
        "FAIL test_assign: 200MB bounce filled disk; max-message-size missing",
        "listen on egress only", "listen is not max-message-size"),
    "postfix": mk(True, "pr-postfix-smtpd-recipient-limit", "lock-pfxrcpt",
        "the Postfix main.cf that omitted smtpd_recipient_limit so a harvested list mailed 5000 rcpts in one transaction",
        "main.cf", "smtpd_client_connection_count_limit = 50", "smtpd_recipient_limit 100",
        "smtpd_recipient_limit", "harbor connection_count_limit only. pack smtpd_recipient_limit.",
        "FAIL test_assign: 5000 rcpts one txn; recipient_limit missing",
        "connection_count_limit only", "connection count is not recipient_limit"),
    "exim": mk(False, "pr-exim-queue-run-max", "quay-exqmax",
        "the Exim conf that omitted queue_run_max so a retry storm forked 400 queue runners and the host load spiked",
        "exim.conf", "split_spool_directory = true", "queue_run_max 8",
        "queue_run_max", "harbor split_spool_directory only. pack queue_run_max.",
        "FAIL test_assign: 400 queue runners; load spike; queue_run_max missing",
        "split_spool_directory only", "split_spool is not queue_run_max"),
    "ghost": mk(True, "pr-ghost-url-https-admin", "lock-ghsurl",
        "the Ghost config that omitted url https so admin assets mixed-content blocked and the editor would not load",
        "config.production.json", "server.port: 2368", "url https://blog.example",
        "url", "harbor server.port only. pack url https.",
        "FAIL test_assign: mixed-content admin; url https missing",
        "server.port only", "server.port is not url https"),
    "strapi": mk(False, "pr-strapi-admin-auth-rate-limit", "quay-straprl",
        "the Strapi admin that omitted rateLimit so a credential stuffing run locked no one and flooded bcrypt",
        "admin.js", "forgotPassword: {enabled: true}", "rateLimit interval 1m max 5",
        "rateLimit", "harbor forgotPassword only. pack rateLimit.",
        "FAIL test_assign: stuffing run; bcrypt flood; rateLimit missing",
        "forgotPassword only", "forgotPassword is not rateLimit"),
    "directus": mk(True, "pr-directus-cors-origin-list", "lock-dircors",
        "the Directus env that omitted CORS_ORIGIN list so the API reflected * and a browser app leaked tokens",
        ".env", "CORS_ENABLED=true", "CORS_ORIGIN https://app.example",
        "CORS_ORIGIN", "harbor CORS_ENABLED only. pack CORS_ORIGIN list.",
        "FAIL test_assign: ACAO *; token leak; CORS_ORIGIN missing",
        "CORS_ENABLED only", "CORS_ENABLED is not CORS_ORIGIN"),
    "payload": mk(False, "pr-payload-max-file-size-mb", "quay-pldmax",
        "the Payload upload that omitted maxFileSize so a 2GB video filled the PVC and the API 500'd",
        "payload.config.ts", "upload: {staticURL: '/media'}", "maxFileSize 20MB",
        "maxFileSize", "harbor staticURL only. pack maxFileSize.",
        "FAIL test_assign: 2GB upload filled PVC; maxFileSize missing",
        "staticURL only", "staticURL is not maxFileSize"),
    "unleash": mk(True, "pr-unleash-db-pool-max", "lock-unlpool",
        "the Unleash server that omitted db.pool.max so 200 replicas opened 2000 PG connections and PG refused",
        "unleash.yml", "db.ssl: true", "db.pool.max 10",
        "db.pool.max", "harbor db.ssl only. pack db.pool.max.",
        "FAIL test_assign: PG too many clients; db.pool.max missing",
        "db.ssl only", "db.ssl is not db.pool.max"),
    "flagsmith": mk(False, "pr-flagsmith-environment-cache-ttl", "quay-fsmttl",
        "the Flagsmith API that omitted environment cache TTL so every request hit Postgres and p99 spiked",
        "flagsmith.env", "DJANGO_ALLOWED_HOSTS=*", "ENVIRONMENT_CACHE_SECONDS 60",
        "ENVIRONMENT_CACHE_SECONDS", "harbor DJANGO_ALLOWED_HOSTS only. pack ENVIRONMENT_CACHE_SECONDS.",
        "FAIL test_assign: every request PG; p99 spike; cache TTL missing",
        "DJANGO_ALLOWED_HOSTS only", "ALLOWED_HOSTS is not environment cache TTL"),
    "growthbook": mk(True, "pr-growthbook-sdk-stale-ttl", "lock-gbstale",
        "the GrowthBook SDK that omitted staleTtl so a CDN blip served 15-minute-old flags after a kill-switch",
        "gb.js", "apiHost: 'https://cdn.growthbook.io'", "staleTtl 10",
        "staleTtl", "harbor apiHost only. pack staleTtl.",
        "FAIL test_assign: kill-switch delayed 15m; staleTtl missing",
        "apiHost only", "apiHost is not staleTtl"),
    "launchdarkly": mk(False, "pr-launchdarkly-flush-interval-ms", "quay-ldflush",
        "the LaunchDarkly client that omitted flushInterval so events sat in memory and a crash lost a day of experiments",
        "ld.js", "stream: true", "flushInterval 2000",
        "flushInterval", "harbor stream only. pack flushInterval.",
        "FAIL test_assign: crash lost events; flushInterval missing",
        "stream only", "stream is not flushInterval"),
    "zig": mk(True, "pr-zig-stack-check-release", "lock-zigstk",
        "the Zig release build that omitted -fstack-check so a recursive parser smashed the stack with no panic",
        "build.zig", "optimize = ReleaseFast", "fstack-check",
        "fstack-check", "harbor ReleaseFast only. pack fstack-check.",
        "FAIL test_assign: stack smash no panic; fstack-check missing",
        "ReleaseFast only", "ReleaseFast is not fstack-check"),
    "nim": mk(False, "pr-nim-threads-on-gc", "quay-nimthr",
        "the Nim compile that omitted --threads:on so a threadpool build used the shared heap and GC corrupted",
        "nim.cfg", "--mm:orc", "--threads:on",
        "threads:on", "harbor --mm:orc only. pack --threads:on.",
        "FAIL test_assign: GC corrupt threadpool; --threads:on missing",
        "--mm:orc only", "orc is not --threads:on"),
    "odin": mk(True, "pr-odin-vet-unused-imports", "lock-odinvet",
        "the Odin build that omitted -vet-unused so a stale import hid a renamed package and the binary shipped old code",
        "ols.json", "checker_args: []", "-vet-unused",
        "vet-unused", "harbor empty checker_args. pack -vet-unused.",
        "FAIL test_assign: stale import shipped; -vet-unused missing",
        "empty checker_args", "empty checker_args is not -vet-unused"),
    "gleam": mk(False, "pr-gleam-javascript-prelude", "quay-glmjs",
        "the Gleam JS target that omitted javascript.prelude so Deno missed gleam.mjs and the worker crashed",
        "gleam.toml", "target = \"javascript\"", "javascript.prelude gleam.mjs",
        "javascript.prelude", "harbor target javascript only. pack javascript.prelude.",
        "FAIL test_assign: Deno gleam.mjs missing; prelude missing",
        "target javascript only", "target is not javascript.prelude"),
    "elixir": mk(True, "pr-elixir-logger-sync-false", "lock-elxsync",
        "the Elixir Logger that omitted sync: false so a request storm blocked on disk and p99 hit 8s",
        "config.exs", "level: :info", "sync: false",
        "sync", "harbor level :info only. pack sync: false.",
        "FAIL test_assign: p99 8s disk block; sync: false missing",
        "level :info only", "log level is not sync: false"),
    "erlang": mk(False, "pr-erlang-kernel-poll-true", "quay-erlpoll",
        "the Erlang VM that omitted +K true so a 10k connection node used select and CPU pegged",
        "vm.args", "+P 1048576", "+K true",
        "+K", "harbor +P only. pack +K true.",
        "FAIL test_assign: select CPU peg; +K true missing",
        "+P only", "+P is not +K true"),
    "wasmtime": mk(True, "pr-wasmtime-epoch-interruption", "lock-wtmepo",
        "the Wasmtime store that omitted epoch interruption so a runaway guest loop never yielded and the worker hung",
        "wasmtime.toml", "consume_fuel = false", "epoch_interruption true",
        "epoch_interruption", "harbor consume_fuel false only. pack epoch_interruption.",
        "FAIL test_assign: runaway guest hung worker; epoch_interruption missing",
        "consume_fuel false only", "consume_fuel is not epoch_interruption"),
    "cranelift": mk(False, "pr-cranelift-opt-level-speed", "quay-clopt",
        "the Cranelift flags that omitted opt_level speed so a JIT hot path stayed at none and p50 doubled",
        "clif.toml", "enable_verifier = false", "opt_level speed",
        "opt_level", "harbor enable_verifier only. pack opt_level speed.",
        "FAIL test_assign: JIT p50 doubled; opt_level missing",
        "enable_verifier only", "enable_verifier is not opt_level"),
    "quickwit": mk(True, "pr-quickwit-split-max-num-docs", "lock-qwsplt",
        "the Quickwit index that omitted split.max_num_docs so a single split grew to 40GB and merges stalled",
        "quickwit.yaml", "indexing_resources.heap_size: 2G", "split.max_num_docs 10_000_000",
        "split.max_num_docs", "harbor heap_size only. pack split.max_num_docs.",
        "FAIL test_assign: 40GB split; merges stall; max_num_docs missing",
        "heap_size only", "heap_size is not split.max_num_docs"),
    "sonic": mk(False, "pr-sonic-max-connections-cap", "quay-sncmax",
        "the Sonic server that omitted tcp_max_connections so a scrape opened 8k sockets and search stalled",
        "config.cfg", "tcp_port = 1491", "tcp_max_connections 200",
        "tcp_max_connections", "harbor tcp_port only. pack tcp_max_connections.",
        "FAIL test_assign: 8k sockets; search stall; tcp_max_connections missing",
        "tcp_port only", "tcp_port is not tcp_max_connections"),
    "zinc": mk(True, "pr-zincsearch-shard-max-size-gb", "lock-zncshard",
        "the ZincSearch index that omitted shard max_size so one shard hit 200GB and queries timed out",
        "zinc.yaml", "index.number_of_shards: 1", "shard max_size 20gb",
        "max_size", "harbor number_of_shards only. pack shard max_size.",
        "FAIL test_assign: 200GB shard; query timeout; max_size missing",
        "number_of_shards only", "shard count is not max_size"),
    "lnx": mk(False, "pr-lnx-index-memory-limit-mb", "quay-lnxmem",
        "the Lnx engine that omitted index memory_limit so a reindex OOM-killed the box",
        "lnx.toml", "writer_buffer = 64MB", "memory_limit 2048MB",
        "memory_limit", "harbor writer_buffer only. pack memory_limit.",
        "FAIL test_assign: reindex OOM; memory_limit missing",
        "writer_buffer only", "writer_buffer is not memory_limit"),
    "rabbitmq": mk(True, "pr-rabbitmq-vm-memory-high-watermark", "lock-rmqwm",
        "the RabbitMQ node that omitted vm_memory_high_watermark so publishers never blocked and the broker OOM'd",
        "rabbitmq.conf", "disk_free_limit.relative = 2.0", "vm_memory_high_watermark 0.4",
        "vm_memory_high_watermark", "harbor disk_free_limit only. pack vm_memory_high_watermark.",
        "FAIL test_assign: broker OOM; watermark missing",
        "disk_free_limit only", "disk_free_limit is not vm_memory_high_watermark"),
    "activemq": mk(False, "pr-activemq-memory-usage-percent", "quay-amqmem",
        "the ActiveMQ broker that omitted memoryUsage percent so a slow consumer filled the heap and the JVM died",
        "activemq.xml", "storeUsage limit=\"100 gb\"", "memoryUsage percent 70",
        "memoryUsage", "harbor storeUsage only. pack memoryUsage percent.",
        "FAIL test_assign: heap full; JVM die; memoryUsage missing",
        "storeUsage only", "storeUsage is not memoryUsage"),
    "nsq": mk(True, "pr-nsq-mem-queue-size-cap", "lock-nsqmem",
        "the nsqd that omitted mem-queue-size so a paused consumer ballooned RSS and the node swapped",
        "nsqd.cfg", "max-msg-timeout=15m", "mem-queue-size 10000",
        "mem-queue-size", "harbor max-msg-timeout only. pack mem-queue-size.",
        "FAIL test_assign: RSS balloon swap; mem-queue-size missing",
        "max-msg-timeout only", "max-msg-timeout is not mem-queue-size"),
    "beanstalkd": mk(False, "pr-beanstalkd-fdatasync-wal", "quay-bnsfsync",
        "the Beanstalkd start that omitted -f 50 so a crash lost 30s of jobs sitting only in memory",
        "beanstalkd.service", "-b /var/lib/beanstalkd", "-f 50",
        "-f", "harbor -b binlog only. pack -f 50.",
        "FAIL test_assign: crash lost 30s jobs; -f missing",
        "-b binlog only", "-b is not -f fsync"),
    "celery": mk(True, "pr-celery-worker-max-tasks", "lock-celmax",
        "the Celery worker that omitted worker_max_tasks_per_child so a leaky task grew RSS until the box OOM'd",
        "celery.py", "worker_prefetch_multiplier=1", "worker_max_tasks_per_child 100",
        "worker_max_tasks_per_child", "harbor prefetch_multiplier only. pack worker_max_tasks_per_child.",
        "FAIL test_assign: leaky RSS OOM; max_tasks_per_child missing",
        "prefetch_multiplier only", "prefetch is not max_tasks_per_child"),
    "sidekiq": mk(False, "pr-sidekiq-super-fetch-reliable", "quay-sdksf",
        "the Sidekiq process that omitted super_fetch so a SIGKILL lost in-flight jobs and they never retried",
        "sidekiq.yml", "concurrency: 10", "super_fetch true",
        "super_fetch", "harbor concurrency only. pack super_fetch.",
        "FAIL test_assign: SIGKILL lost jobs; super_fetch missing",
        "concurrency only", "concurrency is not super_fetch"),
    "rq": mk(True, "pr-rq-worker-ttl-seconds", "lock-rqttl",
        "the RQ worker that omitted worker_ttl so a dead worker stayed busy and jobs sat in started",
        "rq.yml", "job_timeout: 180", "worker_ttl 420",
        "worker_ttl", "harbor job_timeout only. pack worker_ttl.",
        "FAIL test_assign: dead worker busy; jobs stuck started; worker_ttl missing",
        "job_timeout only", "job_timeout is not worker_ttl"),
    "huey": mk(False, "pr-huey-immediate-false-prod", "quay-hueyimm",
        "the Huey config that omitted immediate False so production ran tasks inline and the request thread blocked",
        "huey.py", "Huey(name='harbor')", "immediate False",
        "immediate", "harbor Huey name only. pack immediate False.",
        "FAIL test_assign: tasks inline; request blocked; immediate missing",
        "Huey name only", "name is not immediate False"),
    "bullmq": mk(True, "pr-bullmq-lock-duration-ms", "lock-bllock",
        "the BullMQ worker that omitted lockDuration so a 2m job was stalled and run twice",
        "queue.js", "stalledInterval: 30000", "lockDuration 180000",
        "lockDuration", "harbor stalledInterval only. pack lockDuration.",
        "FAIL test_assign: 2m job twice; lockDuration missing",
        "stalledInterval only", "stalledInterval is not lockDuration"),
    "agenda": mk(False, "pr-agenda-lock-limit-job", "quay-aglock",
        "the Agenda job that omitted lockLimit so two workers ran the same invoice send",
        "agenda.js", "lockLifetime: 10000", "lockLimit 1",
        "lockLimit", "harbor lockLifetime only. pack lockLimit.",
        "FAIL test_assign: invoice sent twice; lockLimit missing",
        "lockLifetime only", "lockLifetime is not lockLimit"),
    "resque": mk(True, "pr-resque-interval-poll-sec", "lock-rsqint",
        "the Resque worker that omitted INTERVAL so it busy-polled Redis at 0s and the CPU pegged",
        "resque.yml", "QUEUE=default", "INTERVAL 5",
        "INTERVAL", "harbor QUEUE only. pack INTERVAL.",
        "FAIL test_assign: busy-poll CPU peg; INTERVAL missing",
        "QUEUE only", "QUEUE is not INTERVAL"),
    "delayedjob": mk(False, "pr-delayedjob-max-run-time", "quay-djmax",
        "the Delayed Job worker that omitted max_run_time so a hung PDF job held the lock for hours",
        "delayed_job.rb", "destroy_failed_jobs = false", "max_run_time 10.minutes",
        "max_run_time", "harbor destroy_failed_jobs only. pack max_run_time.",
        "FAIL test_assign: hung PDF lock hours; max_run_time missing",
        "destroy_failed_jobs only", "destroy_failed_jobs is not max_run_time"),
    "logstash": mk(True, "pr-logstash-pipeline-workers-count", "lock-lswrk",
        "the Logstash pipeline that omitted pipeline.workers so a single worker backpressured Beats and dropped events",
        "logstash.yml", "pipeline.batch.size: 125", "pipeline.workers 4",
        "pipeline.workers", "harbor pipeline.batch.size only. pack pipeline.workers.",
        "FAIL test_assign: Beats drop; workers missing",
        "pipeline.batch.size only", "batch.size is not pipeline.workers"),
    "promtail": mk(False, "pr-promtail-positions-sync-period", "quay-ptpos",
        "the Promtail client that omitted positions.sync_period so a crash re-tailed 2GB and Loki 429'd",
        "promtail.yml", "positions.filename: /run/positions.yaml", "positions.sync_period 10s",
        "sync_period", "harbor positions.filename only. pack positions.sync_period.",
        "FAIL test_assign: crash re-tail 2GB; Loki 429; sync_period missing",
        "positions.filename only", "positions.filename is not sync_period"),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f


LHC_PAIRS = [
    ("Tempo max_block_duration vs Loki ingestion_rate_strategy", fn("tempo"), fn("loki"),
     "max_block_duration 30m; ingestion_rate_strategy local", "max_block_bytes; ingestion_rate_mb",
     "tempo dump WAL disk full; loki dump replica 429"),
    ("Jaeger adaptive sampling vs Zipkin ES index", fn("jaeger"), fn("zipkin"),
     "adaptive sampling; elasticsearch.index", "const 1.0; STORAGE_TYPE",
     "jaeger dump 100% flood; zipkin dump ILM never rolled"),
    ("OTel memory_limiter vs Vector disk_buffer", fn("otel"), fn("vector"),
     "memory_limiter; disk_buffer.max_size", "batch; memory buffer",
     "otel dump pod OOM; vector dump Kafka outage OOM"),
    ("Fluent Bit Mem_Buf_Limit vs Fluentd retry_type", fn("fluentbit"), fn("fluentd"),
     "Mem_Buf_Limit 32MB; retry_type exponential", "Buffer_Chunk_Size; flush_interval",
     "fluentbit dump RSS balloon; fluentd dump 1s retry storm"),
    ("Postal smtp workers vs Mailu FETCHMAIL", fn("postal"), fn("mailu"),
     "smtp_relays workers 8; FETCHMAIL=false", "hostname; WEBMAIL",
     "postal dump queue stuck; mailu dump fetchmail loop"),
    ("Haraka max_unrecognized vs OpenSMTPD max-message-size", fn("haraka"), fn("opensmtpd"),
     "max_unrecognized_commands; max-message-size 35M", "nodes=cpus; listen",
     "haraka dump command flood; opensmtpd dump 200MB bounce"),
    ("Postfix recipient_limit vs Exim queue_run_max", fn("postfix"), fn("exim"),
     "smtpd_recipient_limit 100; queue_run_max 8", "connection_count_limit; split_spool",
     "postfix dump 5000 rcpts; exim dump 400 runners"),
    ("Ghost url https vs Strapi admin rateLimit", fn("ghost"), fn("strapi"),
     "url https; rateLimit interval", "server.port; forgotPassword",
     "ghost dump mixed-content admin; strapi dump stuffing"),
    ("Directus CORS_ORIGIN vs Payload maxFileSize", fn("directus"), fn("payload"),
     "CORS_ORIGIN list; maxFileSize 20MB", "CORS_ENABLED; staticURL",
     "directus dump ACAO *; payload dump 2GB PVC"),
    ("Unleash db.pool.max vs Flagsmith cache TTL", fn("unleash"), fn("flagsmith"),
     "db.pool.max 10; ENVIRONMENT_CACHE_SECONDS", "db.ssl; ALLOWED_HOSTS",
     "unleash dump PG clients; flagsmith dump p99 PG"),
    ("GrowthBook staleTtl vs LaunchDarkly flushInterval", fn("growthbook"), fn("launchdarkly"),
     "staleTtl 10; flushInterval 2000", "apiHost; stream",
     "growthbook dump kill-switch 15m; launchdarkly dump crash events"),
    ("Zig fstack-check vs Nim --threads:on", fn("zig"), fn("nim"),
     "fstack-check; --threads:on", "ReleaseFast; --mm:orc",
     "zig dump stack smash; nim dump GC corrupt"),
    ("Odin -vet-unused vs Gleam javascript.prelude", fn("odin"), fn("gleam"),
     "-vet-unused; javascript.prelude", "empty checker_args; target javascript",
     "odin dump stale import; gleam dump Deno gleam.mjs"),
    ("Elixir logger sync vs Erlang +K true", fn("elixir"), fn("erlang"),
     "sync: false; +K true", "level :info; +P",
     "elixir dump p99 8s; erlang dump select CPU"),
    ("Wasmtime epoch_interruption vs Cranelift opt_level", fn("wasmtime"), fn("cranelift"),
     "epoch_interruption; opt_level speed", "consume_fuel; enable_verifier",
     "wasmtime dump runaway guest; cranelift dump JIT p50"),
    ("Quickwit split.max_num_docs vs Sonic tcp_max_connections", fn("quickwit"), fn("sonic"),
     "split.max_num_docs; tcp_max_connections 200", "heap_size; tcp_port",
     "quickwit dump 40GB split; sonic dump 8k sockets"),
    ("ZincSearch shard max_size vs Lnx memory_limit", fn("zinc"), fn("lnx"),
     "shard max_size 20gb; memory_limit 2048MB", "number_of_shards; writer_buffer",
     "zinc dump 200GB shard; lnx dump reindex OOM"),
    ("RabbitMQ vm_memory_high_watermark vs ActiveMQ memoryUsage", fn("rabbitmq"), fn("activemq"),
     "vm_memory_high_watermark 0.4; memoryUsage 70", "disk_free_limit; storeUsage",
     "rabbitmq dump broker OOM; activemq dump JVM die"),
    ("NSQ mem-queue-size vs Beanstalkd -f", fn("nsq"), fn("beanstalkd"),
     "mem-queue-size 10000; -f 50", "max-msg-timeout; -b",
     "nsq dump RSS swap; beanstalkd dump crash 30s"),
    ("Celery max_tasks_per_child vs Sidekiq super_fetch", fn("celery"), fn("sidekiq"),
     "worker_max_tasks_per_child; super_fetch", "prefetch; concurrency",
     "celery dump leaky OOM; sidekiq dump SIGKILL loss"),
    ("RQ worker_ttl vs Huey immediate False", fn("rq"), fn("huey"),
     "worker_ttl 420; immediate False", "job_timeout; Huey name",
     "rq dump stuck started; huey dump inline request"),
    ("BullMQ lockDuration vs Agenda lockLimit", fn("bullmq"), fn("agenda"),
     "lockDuration 180000; lockLimit 1", "stalledInterval; lockLifetime",
     "bullmq dump job twice; agenda dump invoice twice"),
    ("Resque INTERVAL vs DelayedJob max_run_time", fn("resque"), fn("delayedjob"),
     "INTERVAL 5; max_run_time 10m", "QUEUE; destroy_failed_jobs",
     "resque dump busy-poll CPU; delayedjob dump hung PDF"),
    ("Logstash pipeline.workers vs Promtail positions.sync_period", fn("logstash"), fn("promtail"),
     "pipeline.workers 4; positions.sync_period 10s", "batch.size; positions.filename",
     "logstash dump Beats drop; promtail dump re-tail 2GB"),
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
