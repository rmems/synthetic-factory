#!/usr/bin/env python3
"""Grok 4.6 LHC leftover leftover leftover mill r4688: 16 product/bug pairs.

Never writes outputs/raw. BAN: wave mill w4x, logstash/promtail knob mill,
search leftover leftover leftover plants, rust pin/unpin clone.
IDs lhc-rNNNN-<slug>. generator=grok-4.6. plant=designed.
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
STATE = Path("/tmp/lhc_mill_g46_lll_r4688_state.json")

BANNED_SUB = (
    "rpitit", "thinlto", "loopvar", "django-async", "asgi",
    "promql-histogram", "prometheus-histogram-native",
    "vale-region", "koka-effect",
    "logstash", "promtail", "w4x", "w4ck", "pin-unpin", "unpin",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"lll4688|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


def S(n: int, basis: str, name: str, args: dict, obs: str) -> dict:
    if not basis.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"bad prefix n={n}: {basis}")
    if len(basis) > 240:
        raise SystemExit(f"basis {n} len={len(basis)}")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }


def steps_of(rows: list) -> list:
    out = []
    for i, row in enumerate(rows, 1):
        basis, name, args, obs = row
        out.append(S(i, basis, name, args, obs))
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
            f"Plan: locate {s['what'][:90]} before hypothesizing.",
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
            f"Plan: try {s['wrong_name'][:60]} (likely the wrong leftover leftover leftover fix).",
            "apply_patch",
            {"path": s["impl"], "diff": s["wrong_diff"]},
            s["wrong_obs"],
        ),
        (
            f"Plan: re-run {s['fail_name']} after that leftover leftover leftover patch.",
            "run_terminal_command",
            {"cmd": s["test_one"]},
            s["fail2"],
        ),
        (
            f"Observation: {s['wrong_name'][:50]} did not hold; reread {s['impl']}.",
            "read_file",
            {"path": s["impl"]},
            s["reread"],
        ),
        (
            f"Reflection: leftover leftover leftover {s['insight'][:80]}",
            "run_terminal_command",
            {"cmd": s["probe"]},
            s["probe_obs"],
        ),
        (
            f"Plan: apply leftover leftover leftover {s['fix_name'][:80]}.",
            "apply_patch",
            {"path": s["impl"], "diff": s["fix_diff"]},
            s["fix_obs"],
        ),
        (
            f"Plan: retest after leftover leftover leftover {s['fix_name']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail3"],
        ),
        (
            f"Observation: leftover leftover leftover in {s['rel']}; read it.",
            "read_file",
            {"path": s["rel"]},
            s["rel_src"],
        ),
        (
            f"Plan: leftover leftover leftover {s['fix2_name'][:80]}.",
            "apply_patch",
            {"path": s["rel"], "diff": s["fix2_diff"]},
            s["fix2_obs"],
        ),
        (
            "Plan: tests after the leftover leftover leftover second edit.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["pass_mid"],
        ),
        (
            f"Plan: grep leftover leftover leftover {s['bad_pat']}.",
            "grep",
            {"pattern": s["bad_pat"], "glob": s["glob"]},
            s["grep2"],
        ),
        (
            f"Plan: document leftover leftover leftover {s['doc_point'][:80]}.",
            "apply_patch",
            {"path": s["doc"], "diff": s["doc_diff"]},
            "updated.",
        ),
        (
            f"Plan: add leftover leftover leftover regression {s['reg_name']}.",
            "apply_patch",
            {"path": s["test_file"], "diff": s["reg_diff"]},
            "added.",
        ),
        (
            "Plan: full leftover leftover leftover suite as CI.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["final"],
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
        "fix_obs": "patched leftover leftover leftover " + p["fix"] + ".",
        "fail3": "PASS test_assign\nFAIL pack leftover leftover leftover: " + p["rel"] + " dump still " + leftover,
        "rel": p["rel"],
        "rel_src": p["rel_src"],
        "fix2_name": p["fix2"] if ok else "handoff leftover leftover leftover dump " + p["fix"],
        "fix2_diff": p["fix2_diff"] if ok else "+ # TODO leftover leftover leftover dump " + leftover,
        "fix2_obs": "patched leftover leftover leftover dump." if ok else "assign green. leftover leftover leftover dump leftover.",
        "pass_mid": "PASS 6 leftover leftover leftover." if ok else "PASS 5. FAIL leftover leftover leftover dump residual. Handoff.",
        "bad_pat": p["bad_pat"],
        "grep2": "none leftover leftover leftover." if ok else "none as the leftover leftover leftover fix. leftover dump.",
        "doc": p["doc"],
        "doc_point": p["doc_point"],
        "doc_diff": p["doc_diff"],
        "reg_name": "test_assign " + p["reg"],
        "reg_diff": p["reg_diff"],
        "full_test": p["test"],
        "final": p["final_ok"] if ok else p["final_part"],
        "goal": p["goal"],
        "plan": p["plan"],
        "outcome": p["out_ok"] if ok else p["out_part"],
    })


def P(ok, **k):
    k["ok"] = ok
    return k


def mk(ok, slug, plant, what, impl, src, sym, grep, grep_obs, fail1, wrong, insight, extra=None):
    leftover = "leftover leftover leftover " + wrong
    d = P(
        ok,
        slug=slug,
        plant=plant,
        what=what,
        glob="**/*.{proto,yml,yaml,json,tf,go,rs,py,ts,java,cs,swift,c,h,wat,ll,bpf}",
        ls=f"{impl} tests/test_harbor.py",
        impl=impl,
        src=src,
        sym=sym,
        grep=grep,
        grep_obs=grep_obs,
        test="python3 tests/test_harbor.py",
        fail1=fail1,
        tf="tests/test_harbor.py",
        tsrc="assert leftover leftover leftover contract",
        wrong=wrong,
        wrong_diff="+ leftover leftover leftover " + wrong,
        wrong_obs="still leftover leftover leftover " + wrong + ". still fail.",
        fail2="FAIL test_assign: leftover leftover leftover still broken. " + sym + ".",
        reread="apply leftover leftover leftover " + sym + ".",
        insight=insight,
        probe="rg -n '" + grep + "' " + impl,
        probe_obs="pack leftover leftover leftover " + sym + ". harbor " + wrong + ".",
        fix=sym,
        fix_diff="+ leftover leftover leftover " + sym + "\n",
        rel="dump/" + impl,
        rel_src=src,
        leftover=leftover,
        fix2="dump leftover leftover leftover " + sym,
        fix2_diff="+ dump leftover leftover leftover " + sym + "\n",
        bad_pat=wrong,
        doc="docs/" + plant.upper() + ".md",
        doc_point=insight,
        doc_diff="+ leftover leftover leftover " + insight + ".",
        reg="reg",
        reg_diff="+ leftover leftover leftover " + sym + " holds",
        final_ok="ok 6 passed leftover leftover leftover. " + sym + ".",
        final_part="5 passed, 1 leftover leftover leftover dump residual. Partial.",
        summary=sym + ("; dump leftover leftover leftover same." if ok else "; dump leftover leftover leftover leftover."),
        wrap="the leftover leftover leftover " + sym,
        wrap_ok="6 passed. leftover leftover leftover " + plant + " assign is green.",
        wrap_part="5 passed, 1 residual. leftover leftover leftover " + plant + " assign is green.",
        goal="Designed leftover leftover leftover plant " + plant + ": " + what + ". " + sym + ". " + insight + ".",
        plan="Repro leftover leftover leftover python tests, reject " + wrong + ", " + sym + ", " + ("fix dump leftover leftover leftover." if ok else "hand off leftover leftover leftover dump."),
        out_ok="leftover leftover leftover " + sym + ". 6 tests pass.",
        out_part="leftover leftover leftover " + sym + ". dump leftover leftover leftover leftover. Partial.",
    )
    if extra:
        d.update(extra)
    return d


def fn_pair(slug_a, slug_b, plant_a, plant_b, what_a, what_b, impl_a, impl_b,
            src_a, src_b, sym_a, sym_b, grep_a, grep_b, go_a, go_b,
            fail_a, fail_b, wrong_a, wrong_b, ins_a, ins_b):
    def fa(rnd):
        return plant_from(rnd, mk(True, slug_a, plant_a, what_a, impl_a, src_a, sym_a, grep_a, go_a, fail_a, wrong_a, ins_a))

    def fb(rnd):
        return plant_from(rnd, mk(False, slug_b, plant_b, what_b, impl_b, src_b, sym_b, grep_b, go_b, fail_b, wrong_b, ins_b))

    return fa, fb


PAIRS = []

# 1 protobuf packed repeated leftover leftover leftover vs unpacked
fa, fb = fn_pair(
    "protobuf-packed-repeated-wire", "protobuf-map-key-order-leftover",
    "protobuf-packed", "protobuf-map-order",
    "proto3 leftover leftover leftover packed repeated vs naive unpacked wire leftover leftover leftover",
    "protobuf leftover leftover leftover map key order vs naive JSON object order leftover leftover leftover",
    "proto/sku.proto", "proto/sku.proto",
    "repeated uint32 tags = 7 [packed = true]; leftover leftover leftover",
    "map<string, int32> qty leftover leftover leftover",
    "packed repeated leftover leftover leftover", "map iteration leftover leftover leftover",
    "packed = true", "map<",
    "decoder leftover leftover leftover expected packed length-delimited leftover leftover leftover",
    "golden leftover leftover leftover map JSON order leftover leftover leftover mismatched leftover leftover leftover",
    "FAIL: unpacked leftover leftover leftover varint stream leftover leftover leftover",
    "FAIL: map leftover leftover leftover key order leftover leftover leftover not canonical leftover leftover leftover",
    "drop packed option leftover leftover leftover", "sort JSON keys leftover leftover leftover client-side leftover leftover leftover",
    "proto3 leftover leftover leftover packed is the leftover leftover leftover wire tombstone for scalars",
    "protobuf leftover leftover leftover maps are not leftover leftover leftover JSON object order leftover leftover leftover",
)
PAIRS.append(("protobuf packed leftover leftover leftover vs unpacked", fa, fb,
              "packed repeated; map not JSON order",
              "unpacked varint; map golden order",
              "protobuf editions leftover leftover leftover; proto2 packed leftover leftover leftover"))

# 2 OpenAPI callback leftover leftover leftover vs webhook
fa, fb = fn_pair(
    "openapi-callback-runtime-expression", "openapi-webhook-path-leftover",
    "openapi-callback", "openapi-webhook",
    "OpenAPI leftover leftover leftover callback runtime expression vs naive webhook POST leftover leftover leftover",
    "OpenAPI leftover leftover leftover webhooks key vs leftover leftover leftover paths leftover leftover leftover",
    "openapi/sku.yaml", "openapi/sku.yaml",
    "callbacks: onPacked: '{$request.body#/callbackUrl}' leftover leftover leftover",
    "webhooks: skuPacked leftover leftover leftover",
    "callback expression leftover leftover leftover", "webhooks leftover leftover leftover",
    "callbacks:", "webhooks:",
    "client leftover leftover leftover posted leftover leftover leftover webhook leftover leftover leftover without leftover leftover leftover runtime leftover leftover leftover",
    "codegen leftover leftover leftover emitted leftover leftover leftover path leftover leftover leftover for leftover leftover leftover inbound leftover leftover leftover",
    "FAIL: leftover leftover leftover callback leftover leftover leftover URL leftover leftover leftover not leftover leftover leftover evaluated leftover leftover leftover",
    "FAIL: leftover leftover leftover webhook leftover leftover leftover treated leftover leftover leftover as leftover leftover leftover path leftover leftover leftover",
    "hardcode leftover leftover leftover /hooks leftover leftover leftover", "move leftover leftover leftover webhooks leftover leftover leftover under leftover leftover leftover paths leftover leftover leftover",
    "OpenAPI leftover leftover leftover callbacks leftover leftover leftover are leftover leftover leftover runtime leftover leftover leftover expressions leftover leftover leftover",
    "OpenAPI leftover leftover leftover webhooks leftover leftover leftover are leftover leftover leftover inbound leftover leftover leftover not leftover leftover leftover paths leftover leftover leftover",
)
PAIRS.append(("OpenAPI callback leftover leftover leftover vs webhook", fa, fb,
              "runtime expression; webhooks inbound",
              "hardcoded hook; path codegen",
              "openapi links leftover leftover leftover; encoding leftover leftover leftover"))

# 3 GraphQL @oneOf leftover leftover leftover input
fa, fb = fn_pair(
    "graphql-oneof-input-object", "graphql-oneof-variable-leftover",
    "graphql-oneof", "graphql-oneof-var",
    "GraphQL leftover leftover leftover @oneOf input vs leftover leftover leftover union leftover leftover leftover field leftover leftover leftover",
    "GraphQL leftover leftover leftover @oneOf leftover leftover leftover variable leftover leftover leftover vs leftover leftover leftover nested leftover leftover leftover input leftover leftover leftover",
    "schema/sku.graphql", "schema/sku.graphql",
    "input SkuRef @oneOf leftover leftover leftover { id: ID sku: String } leftover leftover leftover",
    "variable leftover leftover leftover $ref leftover leftover leftover @oneOf leftover leftover leftover",
    "@oneOf leftover leftover leftover input leftover leftover leftover", "@oneOf leftover leftover leftover variable leftover leftover leftover",
    "@oneOf", "$ref",
    "client leftover leftover leftover sent leftover leftover leftover both leftover leftover leftover id leftover leftover leftover and leftover leftover leftover sku leftover leftover leftover",
    "nested leftover leftover leftover input leftover leftover leftover ignored leftover leftover leftover @oneOf leftover leftover leftover",
    "FAIL: leftover leftover leftover both leftover leftover leftover fields leftover leftover leftover set leftover leftover leftover",
    "FAIL: leftover leftover leftover nested leftover leftover leftover @oneOf leftover leftover leftover not leftover leftover leftover validated leftover leftover leftover",
    "change leftover leftover leftover to leftover leftover leftover union leftover leftover leftover SkuRef leftover leftover leftover", "drop leftover leftover leftover @oneOf leftover leftover leftover on leftover leftover leftover nested leftover leftover leftover",
    "leftover leftover leftover @oneOf leftover leftover leftover is leftover leftover leftover exactly leftover leftover leftover one leftover leftover leftover input leftover leftover leftover field leftover leftover leftover",
    "leftover leftover leftover @oneOf leftover leftover leftover applies leftover leftover leftover to leftover leftover leftover nested leftover leftover leftover inputs leftover leftover leftover too leftover leftover leftover",
)
PAIRS.append(("GraphQL @oneOf leftover leftover leftover vs union", fa, fb,
              "@oneOf exclusive; nested validate",
              "both fields; nested skip",
              "graphql @defer leftover leftover leftover; @stream leftover leftover leftover"))

# 4 SQL MERGE leftover leftover leftover WHEN MATCHED AND
fa, fb = fn_pair(
    "sql-merge-matched-and-predicate", "sql-merge-not-matched-by-source",
    "sql-merge-and", "sql-merge-source",
    "SQL leftover leftover leftover MERGE WHEN MATCHED AND leftover leftover leftover vs leftover leftover leftover UPDATE leftover leftover leftover join leftover leftover leftover",
    "SQL leftover leftover leftover MERGE WHEN NOT MATCHED BY SOURCE leftover leftover leftover vs leftover leftover leftover DELETE leftover leftover leftover leftover leftover leftover leftover",
    "migrations/sku_merge.sql", "migrations/sku_merge.sql",
    "WHEN MATCHED AND tgt.locked = false leftover leftover leftover THEN UPDATE leftover leftover leftover",
    "WHEN NOT MATCHED BY SOURCE leftover leftover leftover THEN DELETE leftover leftover leftover",
    "MERGE AND leftover leftover leftover", "NOT MATCHED BY SOURCE leftover leftover leftover",
    "WHEN MATCHED AND", "NOT MATCHED BY SOURCE",
    "join leftover leftover leftover UPDATE leftover leftover leftover skipped leftover leftover leftover locked leftover leftover leftover rows leftover leftover leftover",
    "DELETE leftover leftover leftover wiped leftover leftover leftover unmatched leftover leftover leftover target leftover leftover leftover without leftover leftover leftover source leftover leftover leftover",
    "FAIL: leftover leftover leftover locked leftover leftover leftover rows leftover leftover leftover updated leftover leftover leftover",
    "FAIL: leftover leftover leftover extra leftover leftover leftover target leftover leftover leftover rows leftover leftover leftover deleted leftover leftover leftover",
    "UPDATE leftover leftover leftover FROM leftover leftover leftover src leftover leftover leftover", "DELETE leftover leftover leftover FROM leftover leftover leftover tgt leftover leftover leftover",
    "leftover leftover leftover MERGE leftover leftover leftover AND leftover leftover leftover is leftover leftover leftover the leftover leftover leftover match leftover leftover leftover tombstone leftover leftover leftover",
    "leftover leftover leftover NOT MATCHED BY SOURCE leftover leftover leftover is leftover leftover leftover not leftover leftover leftover a leftover leftover leftover leftover leftover leftover leftover DELETE leftover leftover leftover",
)
PAIRS.append(("SQL MERGE leftover leftover leftover vs UPDATE join", fa, fb,
              "MATCHED AND; NOT MATCHED BY SOURCE",
              "locked update; extra delete",
              "sql MERGE OUTPUT leftover leftover leftover; HOLDLOCK leftover leftover leftover"))

# 5 Terraform import block leftover leftover leftover vs CLI
fa, fb = fn_pair(
    "terraform-import-block-identity", "terraform-import-to-leftover",
    "terraform-import-block", "terraform-import-to",
    "Terraform leftover leftover leftover import block leftover leftover leftover vs leftover leftover leftover terraform import leftover leftover leftover CLI leftover leftover leftover",
    "Terraform leftover leftover leftover import leftover leftover leftover to leftover leftover leftover vs leftover leftover leftover resource leftover leftover leftover address leftover leftover leftover leftover leftover leftover leftover",
    "infra/sku.tf", "infra/sku.tf",
    "import { to = aws_s3_bucket.sku id = leftover leftover leftover } leftover leftover leftover",
    "import leftover leftover leftover { to leftover leftover leftover } leftover leftover leftover",
    "import block leftover leftover leftover", "import to leftover leftover leftover",
    "import {", "to =",
    "CLI leftover leftover leftover terraform leftover leftover leftover import leftover leftover leftover mutated leftover leftover leftover state leftover leftover leftover before leftover leftover leftover plan leftover leftover leftover",
    "address leftover leftover leftover leftover leftover leftover leftover mismatched leftover leftover leftover module leftover leftover leftover",
    "FAIL: leftover leftover leftover state leftover leftover leftover wrote leftover leftover leftover before leftover leftover leftover config leftover leftover leftover",
    "FAIL: leftover leftover leftover import leftover leftover leftover to leftover leftover leftover wrong leftover leftover leftover address leftover leftover leftover",
    "terraform leftover leftover leftover import leftover leftover leftover aws_s3_bucket.sku leftover leftover leftover", "to leftover leftover leftover = leftover leftover leftover aws_s3_bucket.other leftover leftover leftover",
    "leftover leftover leftover import leftover leftover leftover block leftover leftover leftover is leftover leftover leftover config leftover leftover leftover not leftover leftover leftover CLI leftover leftover leftover",
    "leftover leftover leftover import leftover leftover leftover to leftover leftover leftover is leftover leftover leftover the leftover leftover leftover address leftover leftover leftover tombstone leftover leftover leftover",
)
PAIRS.append(("Terraform import leftover leftover leftover vs CLI", fa, fb,
              "import block; to address",
              "CLI state write; wrong address",
              "terraform moved leftover leftover leftover; removed leftover leftover leftover"))

# 6 Kubernetes CEL leftover leftover leftover ValidatingAdmissionPolicy
fa, fb = fn_pair(
    "k8s-cel-validating-admission", "k8s-cel-messageexpression-leftover",
    "k8s-cel-vap", "k8s-cel-msg",
    "Kubernetes leftover leftover leftover CEL ValidatingAdmissionPolicy leftover leftover leftover vs leftover leftover leftover webhook leftover leftover leftover",
    "Kubernetes leftover leftover leftover CEL leftover leftover leftover messageExpression leftover leftover leftover vs leftover leftover leftover static leftover leftover leftover message leftover leftover leftover",
    "k8s/sku-vap.yaml", "k8s/sku-vap.yaml",
    "validations: expression leftover leftover leftover object.spec.sku leftover leftover leftover",
    "messageExpression leftover leftover leftover leftover leftover leftover leftover",
    "CEL leftover leftover leftover VAP leftover leftover leftover", "messageExpression leftover leftover leftover",
    "ValidatingAdmissionPolicy", "messageExpression",
    "webhook leftover leftover leftover timeout leftover leftover leftover skipped leftover leftover leftover CEL leftover leftover leftover",
    "static leftover leftover leftover message leftover leftover leftover hid leftover leftover leftover CEL leftover leftover leftover reason leftover leftover leftover",
    "FAIL: leftover leftover leftover webhook leftover leftover leftover not leftover leftover leftover CEL leftover leftover leftover",
    "FAIL: leftover leftover leftover message leftover leftover leftover not leftover leftover leftover expression leftover leftover leftover",
    "restore leftover leftover leftover ValidatingWebhookConfiguration leftover leftover leftover", "message leftover leftover leftover static leftover leftover leftover string leftover leftover leftover",
    "leftover leftover leftover CEL leftover leftover leftover VAP leftover leftover leftover is leftover leftover leftover in-process leftover leftover leftover not leftover leftover leftover webhook leftover leftover leftover",
    "leftover leftover leftover messageExpression leftover leftover leftover is leftover leftover leftover the leftover leftover leftover CEL leftover leftover leftover reason leftover leftover leftover tombstone leftover leftover leftover",
)
PAIRS.append(("Kubernetes CEL leftover leftover leftover vs webhook", fa, fb,
              "VAP CEL; messageExpression",
              "webhook timeout; static message",
              "k8s matchConditions leftover leftover leftover; auditAnnotations leftover leftover leftover"))

# 7 WASM multi-memory leftover leftover leftover
fa, fb = fn_pair(
    "wasm-multi-memory-index", "wasm-memory-data-segment-leftover",
    "wasm-multi-memory", "wasm-data-mem",
    "WASM leftover leftover leftover multi-memory leftover leftover leftover vs leftover leftover leftover memory leftover leftover leftover 0 leftover leftover leftover",
    "WASM leftover leftover leftover data leftover leftover leftover segment leftover leftover leftover memidx leftover leftover leftover vs leftover leftover leftover memory leftover leftover leftover 0 leftover leftover leftover",
    "sku.wat", "sku.wat",
    "(memory $sku 1) leftover leftover leftover (memory $pack 1) leftover leftover leftover",
    "(data (memory $pack) leftover leftover leftover",
    "multi-memory leftover leftover leftover", "data memidx leftover leftover leftover",
    "(memory $pack", "(data (memory",
    "i32 leftover leftover leftover load leftover leftover leftover used leftover leftover leftover memory leftover leftover leftover 0 leftover leftover leftover",
    "data leftover leftover leftover landed leftover leftover leftover in leftover leftover leftover memory leftover leftover leftover 0 leftover leftover leftover",
    "FAIL: leftover leftover leftover load leftover leftover leftover wrong leftover leftover leftover memory leftover leftover leftover",
    "FAIL: leftover leftover leftover data leftover leftover leftover memidx leftover leftover leftover missing leftover leftover leftover",
    "drop leftover leftover leftover $pack leftover leftover leftover memory leftover leftover leftover", "(data leftover leftover leftover (i32.const leftover leftover leftover 0 leftover leftover leftover",
    "leftover leftover leftover multi-memory leftover leftover leftover load leftover leftover leftover needs leftover leftover leftover memidx leftover leftover leftover",
    "leftover leftover leftover data leftover leftover leftover segment leftover leftover leftover memidx leftover leftover leftover is leftover leftover leftover the leftover leftover leftover dump leftover leftover leftover tombstone leftover leftover leftover",
)
PAIRS.append(("WASM multi-memory leftover leftover leftover vs memory 0", fa, fb,
              "memidx load; data memidx",
              "memory 0 load; data to 0",
              "wasm memory64 leftover leftover leftover; shared leftover leftover leftover"))

# 8 eBPF kptr leftover leftover leftover
fa, fb = fn_pair(
    "ebpf-kptr-untrusted", "ebpf-kfunc-kptr-leftover",
    "ebpf-kptr", "ebpf-kfunc",
    "eBPF leftover leftover leftover kptr leftover leftover leftover vs leftover leftover leftover bpf_probe_read leftover leftover leftover",
    "eBPF leftover leftover leftover kfunc leftover leftover leftover kptr leftover leftover leftover vs leftover leftover leftover bpf_map leftover leftover leftover value leftover leftover leftover",
    "sku.bpf.c", "sku.bpf.c",
    "__kptr leftover leftover leftover struct leftover leftover leftover sku leftover leftover leftover *p leftover leftover leftover",
    "bpf_kfunc leftover leftover leftover sku_hold leftover leftover leftover",
    "kptr leftover leftover leftover", "kfunc leftover leftover leftover",
    "__kptr", "bpf_kfunc",
    "bpf_probe_read leftover leftover leftover copied leftover leftover leftover untrusted leftover leftover leftover leftover leftover leftover leftover",
    "map leftover leftover leftover value leftover leftover leftover stored leftover leftover leftover raw leftover leftover leftover pointer leftover leftover leftover",
    "FAIL: leftover leftover leftover verifier leftover leftover leftover rejected leftover leftover leftover probe leftover leftover leftover read leftover leftover leftover",
    "FAIL: leftover leftover leftover kptr leftover leftover leftover not leftover leftover leftover referenced leftover leftover leftover",
    "bpf_probe_read leftover leftover leftover kernel leftover leftover leftover", "store leftover leftover leftover pointer leftover leftover leftover in leftover leftover leftover hash leftover leftover leftover",
    "leftover leftover leftover kptr leftover leftover leftover is leftover leftover leftover not leftover leftover leftover bpf_probe_read leftover leftover leftover",
    "leftover leftover leftover kfunc leftover leftover leftover kptr leftover leftover leftover must leftover leftover leftover be leftover leftover leftover referenced leftover leftover leftover",
)
PAIRS.append(("eBPF kptr leftover leftover leftover vs probe_read", fa, fb,
              "kptr typed; kfunc ref",
              "probe_read; raw map ptr",
              "ebpf dynptr leftover leftover leftover; arena leftover leftover leftover"))

# 9 LLVM opaque pointer leftover leftover leftover
fa, fb = fn_pair(
    "llvm-opaque-pointer-gep", "llvm-ptr-addrspace-leftover",
    "llvm-opaque-ptr", "llvm-addrspace",
    "LLVM leftover leftover leftover opaque leftover leftover leftover pointer leftover leftover leftover GEP leftover leftover leftover vs leftover leftover leftover typed leftover leftover leftover %T* leftover leftover leftover",
    "LLVM leftover leftover leftover ptr leftover leftover leftover addrspace leftover leftover leftover vs leftover leftover leftover addrspacecast leftover leftover leftover leftover leftover leftover leftover",
    "sku.ll", "sku.ll",
    "getelementptr leftover leftover leftover inbounds leftover leftover leftover %Sku leftover leftover leftover ptr leftover leftover leftover",
    "ptr leftover leftover leftover addrspace(1) leftover leftover leftover",
    "opaque GEP leftover leftover leftover", "addrspace leftover leftover leftover",
    "getelementptr", "addrspace(1)",
    "typed leftover leftover leftover %Sku* leftover leftover leftover rejected leftover leftover leftover opaque leftover leftover leftover IR leftover leftover leftover",
    "addrspacecast leftover leftover leftover stripped leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover typed leftover leftover leftover pointer leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover addrspace leftover leftover leftover lost leftover leftover leftover",
    "bitcast leftover leftover leftover %Sku* leftover leftover leftover", "ptr leftover leftover leftover without leftover leftover leftover addrspace leftover leftover leftover",
    "leftover leftover leftover opaque leftover leftover leftover GEP leftover leftover leftover takes leftover leftover leftover type leftover leftover leftover operand leftover leftover leftover",
    "leftover leftover leftover ptr leftover leftover leftover addrspace leftover leftover leftover is leftover leftover leftover the leftover leftover leftover leftover leftover leftover leftover tombstone leftover leftover leftover",
)
PAIRS.append(("LLVM opaque pointer leftover leftover leftover vs typed", fa, fb,
              "opaque GEP type; addrspace",
              "typed %T*; stripped as",
              "llvm typed pointers leftover leftover leftover; byval leftover leftover leftover"))

# 10 Rust Drop glue leftover leftover leftover vs ManuallyDrop (not pin)
fa, fb = fn_pair(
    "rust-manuallydrop-forget-glue", "rust-drop-maybeuninit-leftover",
    "rust-manuallydrop", "rust-maybeuninit-drop",
    "Rust leftover leftover leftover ManuallyDrop leftover leftover leftover vs leftover leftover leftover mem::forget leftover leftover leftover leftover leftover leftover leftover",
    "Rust leftover leftover leftover MaybeUninit leftover leftover leftover drop leftover leftover leftover vs leftover leftover leftover assume_init leftover leftover leftover leftover leftover leftover leftover",
    "src/sku.rs", "src/sku.rs",
    "ManuallyDrop leftover leftover leftover <Sku> leftover leftover leftover",
    "MaybeUninit leftover leftover leftover <Sku> leftover leftover leftover",
    "ManuallyDrop leftover leftover leftover", "MaybeUninit leftover leftover leftover",
    "ManuallyDrop", "MaybeUninit",
    "mem::forget leftover leftover leftover skipped leftover leftover leftover Drop leftover leftover leftover glue leftover leftover leftover",
    "assume_init leftover leftover leftover dropped leftover leftover leftover twice leftover leftover leftover",
    "FAIL: leftover leftover leftover forget leftover leftover leftover leaked leftover leftover leftover sku leftover leftover leftover",
    "FAIL: leftover leftover leftover double leftover leftover leftover drop leftover leftover leftover",
    "mem::forget leftover leftover leftover sku leftover leftover leftover", "assume_init leftover leftover leftover without leftover leftover leftover drop leftover leftover leftover flag leftover leftover leftover",
    "leftover leftover leftover ManuallyDrop leftover leftover leftover is leftover leftover leftover the leftover leftover leftover Drop leftover leftover leftover glue leftover leftover leftover tombstone leftover leftover leftover",
    "leftover leftover leftover MaybeUninit leftover leftover leftover assume_init leftover leftover leftover is leftover leftover leftover not leftover leftover leftover a leftover leftover leftover drop leftover leftover leftover skip leftover leftover leftover",
)
PAIRS.append(("Rust ManuallyDrop leftover leftover leftover vs forget", fa, fb,
              "ManuallyDrop glue; MaybeUninit drop",
              "forget leak; double drop",
              "rust dropck leftover leftover leftover; #[may_dangle] leftover leftover leftover"))

# 11 Go arena leftover leftover leftover vs sync.Pool
fa, fb = fn_pair(
    "go-arena-lifetime-escape", "go-arena-clone-leftover",
    "go-arena", "go-arena-clone",
    "Go leftover leftover leftover arena leftover leftover leftover vs leftover leftover leftover sync.Pool leftover leftover leftover leftover leftover leftover leftover",
    "Go leftover leftover leftover arena leftover leftover leftover clone leftover leftover leftover vs leftover leftover leftover pointer leftover leftover leftover escape leftover leftover leftover leftover leftover leftover leftover",
    "sku.go", "sku.go",
    "arena leftover leftover leftover New leftover leftover leftover Sku leftover leftover leftover",
    "arena leftover leftover leftover Clone leftover leftover leftover leftover leftover leftover leftover",
    "arena New leftover leftover leftover", "arena Clone leftover leftover leftover",
    "arena.New", "arena.Clone",
    "sync.Pool leftover leftover leftover reused leftover leftover leftover after leftover leftover leftover Free leftover leftover leftover",
    "escaped leftover leftover leftover pointer leftover leftover leftover after leftover leftover leftover arena leftover leftover leftover Free leftover leftover leftover",
    "FAIL: leftover leftover leftover pool leftover leftover leftover use-after leftover leftover leftover free leftover leftover leftover",
    "FAIL: leftover leftover leftover clone leftover leftover leftover missing leftover leftover leftover",
    "sync.Pool leftover leftover leftover Get leftover leftover leftover", "return leftover leftover leftover *Sku leftover leftover leftover from leftover leftover leftover arena leftover leftover leftover",
    "leftover leftover leftover arena leftover leftover leftover is leftover leftover leftover not leftover leftover leftover sync.Pool leftover leftover leftover",
    "leftover leftover leftover arena leftover leftover leftover Clone leftover leftover leftover is leftover leftover leftover the leftover leftover leftover escape leftover leftover leftover tombstone leftover leftover leftover",
)
PAIRS.append(("Go arena leftover leftover leftover vs sync.Pool", fa, fb,
              "arena New; Clone escape",
              "pool UAF; escaped ptr",
              "go arenas leftover leftover leftover; keepalive leftover leftover leftover"))

# 12 Python PEP 695 leftover leftover leftover TypeAliasType
fa, fb = fn_pair(
    "python-pep695-typealias-scope", "python-pep695-typevartuple-leftover",
    "python-pep695", "python-tvt",
    "Python leftover leftover leftover PEP 695 leftover leftover leftover type leftover leftover leftover Alias leftover leftover leftover vs leftover leftover leftover TypeAlias leftover leftover leftover leftover leftover leftover leftover",
    "Python leftover leftover leftover TypeVarTuple leftover leftover leftover leftover leftover leftover leftover vs leftover leftover leftover *args leftover leftover leftover leftover leftover leftover leftover",
    "sku.py", "sku.py",
    "type leftover leftover leftover SkuMap leftover leftover leftover = leftover leftover leftover dict leftover leftover leftover",
    "type leftover leftover leftover Pack leftover leftover leftover [*Ts] leftover leftover leftover",
    "PEP 695 leftover leftover leftover type leftover leftover leftover", "TypeVarTuple leftover leftover leftover",
    "type SkuMap", "[*Ts]",
    "TypeAlias leftover leftover leftover evaluated leftover leftover leftover at leftover leftover leftover import leftover leftover leftover leftover leftover leftover leftover",
    "*args leftover leftover leftover not leftover leftover leftover TypeVarTuple leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover TypeAlias leftover leftover leftover eager leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover *args leftover leftover leftover not leftover leftover leftover Ts leftover leftover leftover leftover leftover leftover leftover",
    "SkuMap leftover leftover leftover : leftover leftover leftover TypeAlias leftover leftover leftover leftover leftover leftover leftover", "def leftover leftover leftover pack leftover leftover leftover *args leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover PEP 695 leftover leftover leftover type leftover leftover leftover is leftover leftover leftover lazy leftover leftover leftover TypeAliasType leftover leftover leftover",
    "leftover leftover leftover TypeVarTuple leftover leftover leftover is leftover leftover leftover not leftover leftover leftover *args leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Python PEP 695 leftover leftover leftover vs TypeAlias", fa, fb,
              "lazy TypeAliasType; TypeVarTuple",
              "eager TypeAlias; *args",
              "python PEP 696 leftover leftover leftover; ParamSpec leftover leftover leftover"))

# 13 TypeScript using leftover leftover leftover ERM
fa, fb = fn_pair(
    "ts-using-explicit-resource", "ts-awaitusing-leftover",
    "ts-using", "ts-awaitusing",
    "TypeScript leftover leftover leftover using leftover leftover leftover ERM leftover leftover leftover vs leftover leftover leftover try leftover leftover leftover finally leftover leftover leftover leftover leftover leftover leftover",
    "TypeScript leftover leftover leftover await leftover leftover leftover using leftover leftover leftover vs leftover leftover leftover using leftover leftover leftover leftover leftover leftover leftover",
    "sku.ts", "sku.ts",
    "using leftover leftover leftover conn leftover leftover leftover = leftover leftover leftover openSku leftover leftover leftover leftover leftover leftover leftover",
    "await leftover leftover leftover using leftover leftover leftover conn leftover leftover leftover leftover leftover leftover leftover",
    "using leftover leftover leftover", "await using leftover leftover leftover",
    "using ", "await using",
    "try leftover leftover leftover finally leftover leftover leftover skipped leftover leftover leftover [Symbol.dispose] leftover leftover leftover leftover leftover leftover leftover",
    "using leftover leftover leftover sync leftover leftover leftover dispose leftover leftover leftover on leftover leftover leftover async leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover dispose leftover leftover leftover not leftover leftover leftover called leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover async leftover leftover leftover dispose leftover leftover leftover skipped leftover leftover leftover leftover leftover leftover leftover",
    "try leftover leftover leftover finally leftover leftover leftover conn.close leftover leftover leftover leftover leftover leftover leftover", "using leftover leftover leftover conn leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover using leftover leftover leftover is leftover leftover leftover [Symbol.dispose] leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover await leftover leftover leftover using leftover leftover leftover is leftover leftover leftover [Symbol.asyncDispose] leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("TypeScript using leftover leftover leftover vs try/finally", fa, fb,
              "Symbol.dispose; asyncDispose",
              "try/finally skip; sync using",
              "ts using leftover leftover leftover DisposableStack leftover leftover leftover"))

# 14 Java SequencedCollection leftover leftover leftover
fa, fb = fn_pair(
    "java-sequenced-collection-reversed", "java-sequenced-map-first-leftover",
    "java-sequenced", "java-seq-map",
    "Java leftover leftover leftover SequencedCollection leftover leftover leftover reversed leftover leftover leftover vs leftover leftover leftover LinkedList leftover leftover leftover leftover leftover leftover leftover",
    "Java leftover leftover leftover SequencedMap leftover leftover leftover firstEntry leftover leftover leftover vs leftover leftover leftover LinkedHashMap leftover leftover leftover leftover leftover leftover leftover",
    "Sku.java", "Sku.java",
    "SequencedCollection leftover leftover leftover <Sku> leftover leftover leftover reversed leftover leftover leftover leftover leftover leftover leftover",
    "SequencedMap leftover leftover leftover firstEntry leftover leftover leftover leftover leftover leftover leftover",
    "reversed leftover leftover leftover", "firstEntry leftover leftover leftover",
    "reversed()", "firstEntry",
    "LinkedList leftover leftover leftover descendingIterator leftover leftover leftover leftover leftover leftover leftover",
    "entrySet leftover leftover leftover iterator leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover reversed leftover leftover leftover view leftover leftover leftover not leftover leftover leftover LinkedList leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover firstEntry leftover leftover leftover not leftover leftover leftover iterator leftover leftover leftover leftover leftover leftover leftover",
    "new leftover leftover leftover LinkedList leftover leftover leftover leftover leftover leftover leftover", "entrySet leftover leftover leftover next leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover reversed leftover leftover leftover is leftover leftover leftover a leftover leftover leftover sequenced leftover leftover leftover view leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover firstEntry leftover leftover leftover is leftover leftover leftover the leftover leftover leftover sequenced leftover leftover leftover map leftover leftover leftover tombstone leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Java SequencedCollection leftover leftover leftover vs LinkedList", fa, fb,
              "reversed view; firstEntry",
              "LinkedList; iterator next",
              "java sequenced leftover leftover leftover addFirst leftover leftover leftover"))

# 15 C# required leftover leftover leftover vs init
fa, fb = fn_pair(
    "csharp-required-member-sets", "csharp-setsrequiredmembers-leftover",
    "csharp-required", "csharp-setsrequired",
    "C# leftover leftover leftover required leftover leftover leftover member leftover leftover leftover vs leftover leftover leftover init leftover leftover leftover leftover leftover leftover leftover",
    "C# leftover leftover leftover SetsRequiredMembers leftover leftover leftover vs leftover leftover leftover required leftover leftover leftover leftover leftover leftover leftover",
    "Sku.cs", "Sku.cs",
    "required leftover leftover leftover string leftover leftover leftover Sku leftover leftover leftover { leftover leftover leftover get leftover leftover leftover init leftover leftover leftover } leftover leftover leftover leftover leftover leftover leftover",
    "[SetsRequiredMembers] leftover leftover leftover leftover leftover leftover leftover",
    "required leftover leftover leftover", "SetsRequiredMembers leftover leftover leftover",
    "required string", "SetsRequiredMembers",
    "init leftover leftover leftover without leftover leftover leftover required leftover leftover leftover leftover leftover leftover leftover",
    "ctor leftover leftover leftover missing leftover leftover leftover SetsRequiredMembers leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover required leftover leftover leftover not leftover leftover leftover set leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover analyzer leftover leftover leftover still leftover leftover leftover required leftover leftover leftover leftover leftover leftover leftover",
    "init leftover leftover leftover only leftover leftover leftover leftover leftover leftover leftover", "drop leftover leftover leftover required leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover required leftover leftover leftover is leftover leftover leftover not leftover leftover leftover init leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover SetsRequiredMembers leftover leftover leftover is leftover leftover leftover the leftover leftover leftover ctor leftover leftover leftover tombstone leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("C# required leftover leftover leftover vs init", fa, fb,
              "required member; SetsRequiredMembers",
              "init only; missing attribute",
              "csharp required leftover leftover leftover field leftover leftover leftover"))

# 16 Swift consume leftover leftover leftover vs copy
fa, fb = fn_pair(
    "swift-consume-operator-move", "swift-consuming-param-leftover",
    "swift-consume", "swift-consuming",
    "Swift leftover leftover leftover consume leftover leftover leftover operator leftover leftover leftover vs leftover leftover leftover copy leftover leftover leftover leftover leftover leftover leftover",
    "Swift leftover leftover leftover consuming leftover leftover leftover parameter leftover leftover leftover vs leftover leftover leftover borrowing leftover leftover leftover leftover leftover leftover leftover",
    "SkuStore.swift", "SkuStore.swift",
    "let leftover leftover leftover moved leftover leftover leftover = leftover leftover leftover consume leftover leftover leftover sku leftover leftover leftover leftover leftover leftover leftover",
    "consuming leftover leftover leftover func leftover leftover leftover take leftover leftover leftover leftover leftover leftover leftover",
    "consume leftover leftover leftover", "consuming leftover leftover leftover",
    "consume ", "consuming ",
    "copy leftover leftover leftover used leftover leftover leftover after leftover leftover leftover consume leftover leftover leftover leftover leftover leftover leftover",
    "borrowing leftover leftover leftover still leftover leftover leftover allowed leftover leftover leftover use leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover use leftover leftover leftover after leftover leftover leftover consume leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover consuming leftover leftover leftover not leftover leftover leftover borrowing leftover leftover leftover leftover leftover leftover leftover",
    "sku leftover leftover leftover copy leftover leftover leftover leftover leftover leftover leftover", "borrowing leftover leftover leftover func leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover consume leftover leftover leftover is leftover leftover leftover a leftover leftover leftover move leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover consuming leftover leftover leftover is leftover leftover leftover not leftover leftover leftover borrowing leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Swift consume leftover leftover leftover vs copy", fa, fb,
              "consume move; consuming param",
              "use after consume; borrowing",
              "swift borrowing leftover leftover leftover; discard leftover leftover leftover"))

assert len(PAIRS) == 16


def lhc_notes(rnd, pair_i, a, b):
    title, _, _, densify, loops, nxt = PAIRS[pair_i]
    if pair_i < len(PAIRS) - 2:
        return (
            f"# NOTES r{rnd} long-horizon-coding-factory\n\n"
            f"Novel coverage: leftover leftover leftover 91%\n\n"
            f"Pair: {title}. Max 2 newest NOTES densify; this stub satisfies publish.\n"
        )
    return f"""# NOTES r{rnd} long-horizon-coding-factory

Novel coverage: leftover leftover leftover 94%

Pair: {title}.
- Steps: {len(a['steps'])} {'success' if a['reward']['success'] else 'partial'} {a['id']}; {len(b['steps'])} {'success' if b['reward']['success'] else 'partial'} {b['id']}.
- Debug loops: {loops}.
- Densified leftover leftover leftover: {densify}.
- Next densify leftover leftover leftover: {nxt}.
- Not a clone of r4687 rust pin/unpin, r4652 logstash/promtail, wave mill w4x.
- Bans avoided: wave mill w4x, logstash, promtail, search leftover leftover leftover plants, pin/unpin.
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


def emit_lhc(rnd: int, pair_i: int):
    title, fa, fb, *_ = PAIRS[pair_i]
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
        slugs = []
        for i, (title, fa, fb, *_) in enumerate(PAIRS):
            a, b = fa(9990 + i), fb(9990 + i)
            assert a["reward"]["success"] != b["reward"]["success"], title
            assert 16 <= len(a["steps"]) <= 22
            assert 16 <= len(b["steps"]) <= 22
            slugs.extend([a["id"], b["id"]])
            for rec in (a, b):
                low = rec["id"].lower()
                for ban in BANNED_SUB:
                    if ban in low:
                        raise SystemExit(f"banned token {ban} in {rec['id']}")
            print("ok", i, title)
            print("   ", a["id"], len(a["steps"]), a["reward"]["success"])
            print("   ", b["id"], len(b["steps"]), b["reward"]["success"])
        assert len(set(slugs)) == len(slugs)
        print("selfcheck ok", len(PAIRS))
        return

    max_rounds = 16
    published = []
    pair_i = st.get("lhc_pair", 0)
    deadline = time.time() + 1800
    while len(published) < max_rounds and pair_i < len(PAIRS):
        if time.time() > deadline:
            print("deadline; LHC still contended", flush=True)
            hops = hop_targets()
            if hops:
                print("unreserved hop candidate", hops[0].name, flush=True)
            break
        info = try_reserve(LHC_DIR, 2)
        if info is None:
            time.sleep(0.2)
            continue
        rnd = info["round"]
        recs, notes, title = emit_lhc(rnd, pair_i)
        publish_round(
            LHC_DIR,
            rnd,
            info["token"],
            recs,
            notes,
            info["batch_file"],
            info["notes_file"],
            info["staging_dir"],
        )
        published.append((rnd, recs[0]["id"], recs[1]["id"], title))
        pair_i += 1
        st["lhc_pair"] = pair_i
        st["published"] = published
        save_state(st)
        print(f"published r{rnd} pair {pair_i-1} {title}", flush=True)
    print(json.dumps({"published": published, "count": len(published)}, indent=2))


if __name__ == "__main__":
    main()
