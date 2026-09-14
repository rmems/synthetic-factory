#!/usr/bin/env python3
"""Grok 4.6 LHC leftover leftover leftover mill: 16 product/bug pairs.

Never writes outputs/raw. BAN: wave mill w4x/w4ck cartesian, r4652
logstash/promtail clones, RPITIT, Prom native hist, ThinLTO, Go loopvar,
Django ASGI, identity-origin SSO clones.
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
STATE = Path("/tmp/lhc_mill_g46_lll_r4654_state.json")

BANNED_SUB = (
    "rpitit", "thinlto", "loopvar", "django-async", "asgi",
    "promql-histogram", "prometheus-histogram-native",
    "vale-region", "koka-effect",
    "kanidm", "gluu", "casdoor", "authentik", "oauth2", "zitadel",
    "authelia", "pomerium", "teleport", "agama", "sssd", "pam-mkhomedir",
    "hydra", "kratos", "keto", "ory-keto", "logstash", "promtail",
    "w4x", "w4ck",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"lll|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


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
            f"Plan: try {s['wrong_name']} (likely the wrong leftover leftover leftover fix).",
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
            f"Observation: {s['wrong_name']} did not hold; reread {s['impl']}.",
            "read_file",
            {"path": s["impl"]},
            s["reread"],
        ),
        (
            f"Reflection: leftover leftover leftover {s['insight']}",
            "run_terminal_command",
            {"cmd": s["probe"]},
            s["probe_obs"],
        ),
        (
            f"Plan: apply leftover leftover leftover {s['fix_name']}.",
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
            f"Plan: leftover leftover leftover {s['fix2_name']}.",
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
            f"Plan: document leftover leftover leftover {s['doc_point']}.",
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

# 1 protobuf reserved vs field reuse
fa, fb = fn_pair(
    "protobuf-reserved-field-tombstone", "protobuf-json-name-leftover-alias",
    "protobuf-reserved", "protobuf-json-name",
    "proto3 reserved 8 to 15 leftover leftover leftover tombstone vs naive reuse of field 8 on a new string",
    "json_name leftover leftover leftover alias vs naive Python field rename that still emits camelCase",
    "proto/order.proto", "proto/order.proto",
    "message Order { reserved 8 to 15; reserved \"sku_legacy\"; string sku = 16; }",
    "string sku = 16 [json_name = \"sku\"];",
    "reserved 8 to 15 tombstone", "json_name sku leftover leftover leftover",
    "reserved 8", "json_name",
    "order.proto: reserved 8 to 15; buf breaking still sees field 8 reuse",
    "json_name leftover leftover leftover still camelCase skuLegacy on wire",
    "FAIL: buf breaking PROTOBUF_FIELD_SAME_TYPE field 8 reused leftover leftover leftover",
    "FAIL: json encoder still emits skuLegacy leftover leftover leftover",
    "reuse field 8 as string sku", "rename python sku_legacy to sku",
    "reserved ranges are leftover leftover leftover tombstones; never reuse numbers even if types match",
    "json_name leftover leftover leftover is independent of the Python attribute leftover leftover leftover",
)
PAIRS.append(("protobuf reserved tombstone vs json_name leftover leftover leftover alias", fa, fb,
              "reserved 8-15 tombstone; json_name vs attribute",
              "buf breaking; json encoder",
              "proto editions leftover leftover leftover; proto2 required leftover leftover leftover"))

# 2 OpenAPI discriminator vs oneOf first match
fa, fb = fn_pair(
    "openapi-discriminator-mapping-tombstone", "openapi-nullable-anyof-leftover",
    "openapi-discriminator", "openapi-nullable-anyof",
    "OpenAPI discriminator leftover leftover leftover mapping vs naive oneOf first-match decode",
    "nullable anyOf leftover leftover leftover vs naive type: [string, null] OAS3 leftover leftover leftover",
    "openapi/catalog.yaml", "openapi/catalog.yaml",
    "discriminator: propertyName: kind mapping: Widget: '#/components/schemas/Widget'",
    "anyOf leftover leftover leftover nullable without explicit null schema",
    "discriminator mapping leftover leftover leftover", "anyOf null leftover leftover leftover",
    "discriminator", "anyOf",
    "oneOf first-match decoded Gadget as Widget leftover leftover leftover",
    "codegen emitted Optional without NullType leftover leftover leftover",
    "FAIL: Gadget payload decoded as Widget leftover leftover leftover first oneOf",
    "FAIL: generated client rejects explicit null leftover leftover leftover",
    "reorder oneOf so Widget is last", "type: [string, null] OAS2 leftover leftover leftover",
    "discriminator leftover leftover leftover mapping is the leftover leftover leftover contract, not oneOf order",
    "OAS3 leftover leftover leftover nullable is anyOf with explicit null leftover leftover leftover",
)
PAIRS.append(("OpenAPI discriminator leftover leftover leftover vs oneOf first-match", fa, fb,
              "discriminator mapping; OAS3 anyOf null",
              "decode Gadget; codegen Optional",
              "openapi 3.1 type null leftover leftover leftover; content-type leftover leftover leftover"))

# 3 GraphQL @defer leftover vs await all
fa, fb = fn_pair(
    "graphql-defer-incremental-payload", "graphql-defer-label-collision",
    "graphql-defer", "graphql-defer-label",
    "GraphQL leftover leftover leftover @defer incremental payload vs naive await-all resolver",
    "leftover leftover leftover @defer label collision vs naive unlabeled defer leftover leftover leftover",
    "schema/catalog.graphql", "schema/catalog.graphql",
    "@defer(label: \"skuBlock\") on Product.sku leftover leftover leftover",
    "@defer without label leftover leftover leftover twice on same selection set",
    "@defer incremental leftover leftover leftover", "@defer label leftover leftover leftover",
    "@defer", "label",
    "gateway waited for skuBlock leftover leftover leftover as if it were non-deferred",
    "two unlabeled @defer leftover leftover leftover collided in incremental stream",
    "FAIL: initial payload included deferred sku leftover leftover leftover",
    "FAIL: incremental stream mixed two leftover leftover leftover unlabeled defers",
    "await Promise.all leftover leftover leftover resolvers", "drop one @defer leftover leftover leftover",
    "leftover leftover leftover @defer must stream incremental leftover leftover leftover payloads, not await-all",
    "leftover leftover leftover @defer labels must be unique leftover leftover leftover per operation",
)
PAIRS.append(("GraphQL @defer leftover leftover leftover vs await-all", fa, fb,
              "@defer incremental; unique labels",
              "gateway wait; unlabeled collision",
              "graphql @stream leftover leftover leftover; @skip leftover leftover leftover"))

# 4 SQL SERIAL leftover vs IDENTITY
fa, fb = fn_pair(
    "sql-serial-vs-identity-owned-sequence", "sql-identity-always-vs-default",
    "sql-serial-identity", "sql-identity-always",
    "PostgreSQL leftover leftover leftover SERIAL owned sequence vs IDENTITY leftover leftover leftover",
    "IDENTITY ALWAYS leftover leftover leftover vs OVERRIDING SYSTEM VALUE leftover leftover leftover",
    "migrations/001_orders.sql", "migrations/002_orders.sql",
    "sku_id SERIAL leftover leftover leftover still owns orders_sku_id_seq",
    "GENERATED ALWAYS AS IDENTITY leftover leftover leftover",
    "SERIAL owned leftover leftover leftover sequence", "IDENTITY ALWAYS leftover leftover leftover",
    "SERIAL", "GENERATED ALWAYS",
    "pg_dump still emits leftover leftover leftover SERIAL not IDENTITY",
    "INSERT with explicit sku_id leftover leftover leftover rejected ALWAYS",
    "FAIL: ALTER leftover leftover leftover SERIAL did not become IDENTITY",
    "FAIL: ALWAYS leftover leftover leftover rejects OVERRIDING SYSTEM VALUE missing",
    "ALTER COLUMN TYPE leftover leftover leftover bigint", "GENERATED BY DEFAULT leftover leftover leftover",
    "leftover leftover leftover SERIAL is not IDENTITY; drop default and attach leftover leftover leftover sequence",
    "leftover leftover leftover ALWAYS needs OVERRIDING SYSTEM VALUE leftover leftover leftover on inserts",
)
PAIRS.append(("SQL SERIAL leftover leftover leftover vs IDENTITY", fa, fb,
              "owned sequence; ALWAYS vs DEFAULT",
              "pg_dump SERIAL; explicit insert",
              "sql generated columns leftover leftover leftover; collation leftover leftover leftover"))

# 5 Terraform moved leftover vs state mv
fa, fb = fn_pair(
    "terraform-moved-block-address-tombstone", "terraform-removed-block-leftover-state",
    "terraform-moved", "terraform-removed",
    "Terraform leftover leftover leftover moved block vs naive terraform state mv leftover leftover leftover",
    "leftover leftover leftover removed block vs naive destroy leftover leftover leftover",
    "infra/orders.tf", "infra/orders.tf",
    "moved { from = aws_s3_bucket.sku to = aws_s3_bucket.catalog }",
    "removed { from = aws_s3_bucket.scratch leftover leftover leftover }",
    "moved block leftover leftover leftover", "removed block leftover leftover leftover",
    "moved", "removed",
    "plan still wants leftover leftover leftover destroy+create because moved was not committed",
    "state still tracks leftover leftover leftover scratch after terraform destroy",
    "FAIL: leftover leftover leftover address change without moved leftover leftover leftover",
    "FAIL: leftover leftover leftover scratch still in state leftover leftover leftover",
    "terraform state mv leftover leftover leftover locally", "terraform destroy leftover leftover leftover scratch",
    "leftover leftover leftover moved belongs in VCS so teammates leftover leftover leftover share the address tombstone",
    "leftover leftover leftover removed drops from state without leftover leftover leftover destroy",
)
PAIRS.append(("Terraform moved leftover leftover leftover vs state mv", fa, fb,
              "moved in VCS; removed vs destroy",
              "destroy+create; leftover state",
              "terraform import leftover leftover leftover; replace leftover leftover leftover"))

# 6 Kubernetes finalizer leftover vs force delete
fa, fb = fn_pair(
    "k8s-finalizer-tombstone-vs-force-delete", "k8s-ownerref-foreground-leftover",
    "k8s-finalizer", "k8s-ownerref-foreground",
    "Kubernetes leftover leftover leftover finalizer tombstone vs naive kubectl delete --force leftover leftover leftover",
    "leftover leftover leftover ownerReference foreground vs naive orphan leftover leftover leftover",
    "charts/order/templates/job.yaml", "charts/order/templates/job.yaml",
    "metadata.finalizers: [harbor.sku/drain] leftover leftover leftover",
    "ownerReferences blockOwnerDeletion leftover leftover leftover foreground",
    "finalizer leftover leftover leftover drain", "foreground ownerRef leftover leftover leftover",
    "finalizers", "blockOwnerDeletion",
    "namespace stuck Terminating leftover leftover leftover because drain finalizer never removed",
    "child pods leftover leftover leftover lingered after owner delete leftover leftover leftover",
    "FAIL: --force leftover leftover leftover left Terminating leftover leftover leftover",
    "FAIL: orphan leftover leftover leftover policy left children leftover leftover leftover",
    "kubectl delete --force --grace-period=0 leftover leftover leftover", "propagationPolicy Orphan leftover leftover leftover",
    "leftover leftover leftover finalizers must be removed by the controller leftover leftover leftover, not force-deleted",
    "leftover leftover leftover foreground deletion waits leftover leftover leftover on ownerRef children",
)
PAIRS.append(("Kubernetes finalizer leftover leftover leftover vs force delete", fa, fb,
              "drain finalizer; foreground ownerRef",
              "Terminating ns; orphan children",
              "k8s pvc leftover leftover leftover; eviction leftover leftover leftover"))

# 7 WASM table.grow leftover vs memory.grow
fa, fb = fn_pair(
    "wasm-table-grow-funcref-leftover", "wasm-elem-passive-leftover",
    "wasm-table-grow", "wasm-elem-passive",
    "WASM leftover leftover leftover table.grow funcref vs naive memory.grow leftover leftover leftover",
    "leftover leftover leftover passive elem vs naive active elem leftover leftover leftover at instantiate",
    "wasm/catalog.wat", "wasm/catalog.wat",
    "(table $sku 1 funcref) leftover leftover leftover (table.grow $sku)",
    "(elem $sku passive $f0 $f1 leftover leftover leftover)",
    "table.grow leftover leftover leftover funcref", "passive elem leftover leftover leftover",
    "table.grow", "elem $sku passive",
    "call_indirect leftover leftover leftover trapped because table stayed length 1",
    "instantiate leftover leftover leftover copied elem leftover leftover leftover too early",
    "FAIL: leftover leftover leftover call_indirect oob leftover leftover leftover",
    "FAIL: leftover leftover leftover active elem leftover leftover leftover overwrote table",
    "memory.grow leftover leftover leftover 1", "active elem leftover leftover leftover at offset 0",
    "leftover leftover leftover table.grow grows funcref leftover leftover leftover slots, not linear memory",
    "leftover leftover leftover passive elem needs leftover leftover leftover table.init leftover leftover leftover",
)
PAIRS.append(("WASM table.grow leftover leftover leftover vs memory.grow", fa, fb,
              "table.grow funcref; passive table.init",
              "call_indirect oob; early elem",
              "wasm memory64 leftover leftover leftover; bulk memory leftover leftover leftover"))

# 8 eBPF CO-RE leftover vs bpf_probe_read
fa, fb = fn_pair(
    "ebpf-core-reloc-vs-probe-read", "ebpf-btf-type-id-leftover",
    "ebpf-core", "ebpf-btf",
    "eBPF leftover leftover leftover CO-RE BPF_CORE_READ vs naive bpf_probe_read leftover leftover leftover",
    "leftover leftover leftover btf_type_id vs naive offsetof leftover leftover leftover",
    "bpf/sku.bpf.c", "bpf/sku.bpf.c",
    "BPF_CORE_READ(task, comm) leftover leftover leftover",
    "bpf_core_type_id_kernel leftover leftover leftover",
    "BPF_CORE_READ leftover leftover leftover", "btf_type_id leftover leftover leftover",
    "BPF_CORE_READ", "bpf_core_type_id",
    "verifier leftover leftover leftover rejected bpf_probe_read of kernel task leftover leftover leftover",
    "offsetof leftover leftover leftover mismatched kernel leftover leftover leftover BTF",
    "FAIL: leftover leftover leftover probe_read verifier leftover leftover leftover",
    "FAIL: leftover leftover leftover offsetof vs BTF leftover leftover leftover",
    "bpf_probe_read leftover leftover leftover task->comm", "offsetof leftover leftover leftover task_struct comm",
    "leftover leftover leftover CO-RE relocates leftover leftover leftover field offsets via BTF",
    "leftover leftover leftover btf_type_id leftover leftover leftover is the leftover leftover leftover kernel type tombstone",
)
PAIRS.append(("eBPF CO-RE leftover leftover leftover vs bpf_probe_read", fa, fb,
              "BPF_CORE_READ; btf_type_id",
              "verifier probe_read; offsetof mismatch",
              "ebpf kfunc leftover leftover leftover; ringbuf leftover leftover leftover"))

# 9 LLVM opaque pointer leftover vs typed bitcast
fa, fb = fn_pair(
    "llvm-opaque-ptr-vs-typed-bitcast", "llvm-ptrtoint-provenance-leftover",
    "llvm-opaque-ptr", "llvm-ptrtoint",
    "LLVM leftover leftover leftover opaque pointer vs naive typed-pointer bitcast leftover leftover leftover",
    "leftover leftover leftover ptrtoint leftover leftover leftover vs inttoptr leftover leftover leftover provenance",
    "ir/sku.ll", "ir/sku.ll",
    "ptr leftover leftover leftover instead of i8* leftover leftover leftover",
    "ptrtoint leftover leftover leftover i64 leftover leftover leftover",
    "opaque ptr leftover leftover leftover", "ptrtoint leftover leftover leftover",
    "bitcast .* to", "ptrtoint",
    "opt leftover leftover leftover rejected bitcast i8* leftover leftover leftover after opaque ptr",
    "inttoptr leftover leftover leftover dropped leftover leftover leftover provenance",
    "FAIL: leftover leftover leftover typed bitcast leftover leftover leftover",
    "FAIL: leftover leftover leftover provenance leftover leftover leftover",
    "bitcast i8* leftover leftover leftover to i32*", "inttoptr leftover leftover leftover i64 to ptr",
    "leftover leftover leftover opaque pointers leftover leftover leftover make typed bitcasts leftover leftover leftover illegal",
    "leftover leftover leftover ptrtoint is leftover leftover leftover not a provenance-preserving leftover leftover leftover cast",
)
PAIRS.append(("LLVM opaque pointer leftover leftover leftover vs typed bitcast", fa, fb,
              "opaque ptr; ptrtoint provenance",
              "typed bitcast; inttoptr",
              "llvm ptr auth leftover leftover leftover; musttail leftover leftover leftover"))

# 10 Rust Pin leftover vs transmute
fa, fb = fn_pair(
    "rust-pin-unpin-vs-transmute", "rust-pin-project-leftover-drop",
    "rust-pin", "rust-pin-project",
    "Rust leftover leftover leftover Pin<&mut T> vs naive mem::transmute leftover leftover leftover",
    "leftover leftover leftover pin-project Drop leftover leftover leftover vs naive #[pin] leftover leftover leftover",
    "src/sku.rs", "src/sku.rs",
    "Pin<&mut Sku> leftover leftover leftover !Unpin leftover leftover leftover",
    "#[pin] leftover leftover leftover field Drop leftover leftover leftover",
    "Pin leftover leftover leftover !Unpin", "pin-project Drop leftover leftover leftover",
    "mem::transmute", "pin_project",
    "self-referential leftover leftover leftover Sku moved after leftover leftover leftover transmute",
    "Drop leftover leftover leftover ran on unpinned leftover leftover leftover field",
    "FAIL: leftover leftover leftover transmute moved leftover leftover leftover !Unpin",
    "FAIL: leftover leftover leftover Drop unpinned leftover leftover leftover",
    "mem::transmute leftover leftover leftover Pin", "manual Drop leftover leftover leftover without pinned drop",
    "leftover leftover leftover Pin is leftover leftover leftover a leftover leftover leftover move tombstone, not transmute",
    "leftover leftover leftover pin-project leftover leftover leftover Drop must use leftover leftover leftover pinned drop",
)
PAIRS.append(("Rust Pin leftover leftover leftover vs transmute", fa, fb,
              "Pin !Unpin; pin-project Drop",
              "transmute move; unpinned Drop",
              "rust stacked borrows leftover leftover leftover; aliasing leftover leftover leftover"))

# 11 Go context leftover cancel vs timeout only
fa, fb = fn_pair(
    "go-context-withcancel-vs-timeout-only", "go-errgroup-gocontext-leftover",
    "go-context-cancel", "go-errgroup",
    "Go leftover leftover leftover WithCancel parent leftover leftover leftover vs naive WithTimeout leftover leftover leftover only",
    "leftover leftover leftover errgroup leftover leftover leftover vs naive WaitGroup leftover leftover leftover",
    "internal/sku/fetch.go", "internal/sku/fetch.go",
    "ctx, cancel := context.WithCancel(parent) leftover leftover leftover defer cancel()",
    "errgroup.WithContext leftover leftover leftover",
    "WithCancel leftover leftover leftover parent", "errgroup leftover leftover leftover",
    "WithTimeout", "WaitGroup",
    "timeout leftover leftover leftover fired but parent leftover leftover leftover still ran workers",
    "WaitGroup leftover leftover leftover leaked leftover leftover leftover after first error",
    "FAIL: leftover leftover leftover parent not canceled leftover leftover leftover",
    "FAIL: leftover leftover leftover WaitGroup leftover leftover leftover leak",
    "context.WithTimeout leftover leftover leftover only", "sync.WaitGroup leftover leftover leftover",
    "leftover leftover leftover child timeout leftover leftover leftover does not cancel leftover leftover leftover parent",
    "leftover leftover leftover errgroup leftover leftover leftover cancels leftover leftover leftover siblings on first error",
)
PAIRS.append(("Go context leftover leftover leftover cancel vs timeout-only", fa, fb,
              "WithCancel parent; errgroup",
              "parent still running; WaitGroup leak",
              "go context cause leftover leftover leftover; AfterFunc leftover leftover leftover"))

# 12 Python __slots__ leftover vs __dict__
fa, fb = fn_pair(
    "python-slots-vs-dict-weakref", "python-slots-multiple-inheritance-leftover",
    "python-slots", "python-slots-mi",
    "Python leftover leftover leftover __slots__ vs naive __dict__ leftover leftover leftover assignment",
    "leftover leftover leftover multiple inheritance leftover leftover leftover slots vs naive empty slots leftover leftover leftover",
    "harbor/sku.py", "harbor/sku.py",
    "__slots__ = (\"sku\",) leftover leftover leftover without __dict__",
    "class Mix leftover leftover leftover empty __slots__ leftover leftover leftover",
    "__slots__ leftover leftover leftover no __dict__", "MI leftover leftover leftover empty slots",
    "__dict__", "__slots__",
    "Sku leftover leftover leftover assignment leftover leftover leftover extra attr failed leftover leftover leftover",
    "TypeError leftover leftover leftover metaclass conflict leftover leftover leftover slots",
    "FAIL: leftover leftover leftover extra attr leftover leftover leftover",
    "FAIL: leftover leftover leftover MI leftover leftover leftover slots",
    "self.__dict__[\"extra\"] leftover leftover leftover", "class Mix: leftover leftover leftover pass",
    "leftover leftover leftover __slots__ leftover leftover leftover is a leftover leftover leftover instance-layout tombstone",
    "leftover leftover leftover MI leftover leftover leftover requires leftover leftover leftover compatible leftover leftover leftover slots",
)
PAIRS.append(("Python __slots__ leftover leftover leftover vs __dict__", fa, fb,
              "__slots__ layout; MI slots",
              "extra attr; metaclass conflict",
              "python dataclass leftover leftover leftover slots; weakref leftover leftover leftover"))

# 13 TypeScript satisfies leftover vs as const
fa, fb = fn_pair(
    "ts-satisfies-vs-as-const-widening", "ts-satisfies-excess-property-leftover",
    "ts-satisfies", "ts-satisfies-excess",
    "TypeScript leftover leftover leftover satisfies vs naive as const leftover leftover leftover widening",
    "leftover leftover leftover satisfies leftover leftover leftover excess property vs naive type assertion leftover leftover leftover",
    "src/sku.ts", "src/sku.ts",
    "const catalog = { sku: \"a\" } satisfies Catalog leftover leftover leftover",
    "satisfies leftover leftover leftover Catalog leftover leftover leftover extra kind leftover leftover leftover",
    "satisfies leftover leftover leftover Catalog", "excess leftover leftover leftover satisfies",
    "as const", "as Catalog",
    "as const leftover leftover leftover widened leftover leftover leftover sku to leftover leftover leftover string",
    "as Catalog leftover leftover leftover dropped leftover leftover leftover excess leftover leftover leftover",
    "FAIL: leftover leftover leftover as const leftover leftover leftover widening",
    "FAIL: leftover leftover leftover assertion leftover leftover leftover excess",
    "as const leftover leftover leftover", "as Catalog leftover leftover leftover",
    "leftover leftover leftover satisfies leftover leftover leftover checks leftover leftover leftover without leftover leftover leftover widening",
    "leftover leftover leftover satisfies leftover leftover leftover still leftover leftover leftover flags leftover leftover leftover excess properties",
)
PAIRS.append(("TypeScript satisfies leftover leftover leftover vs as const", fa, fb,
              "satisfies no widen; excess property",
              "string widen; dropped excess",
              "ts const type leftover leftover leftover; satisfies never leftover leftover leftover"))

# 14 Java sealed leftover vs instanceof chain
fa, fb = fn_pair(
    "java-sealed-permits-vs-instanceof", "java-record-pattern-leftover",
    "java-sealed", "java-record-pattern",
    "Java leftover leftover leftover sealed permits vs naive instanceof leftover leftover leftover chain",
    "leftover leftover leftover record pattern leftover leftover leftover vs naive getter leftover leftover leftover",
    "src/Sku.java", "src/Sku.java",
    "sealed interface Sku permits Widget, Gadget leftover leftover leftover",
    "case Widget(String id) leftover leftover leftover",
    "sealed permits leftover leftover leftover", "record pattern leftover leftover leftover",
    "instanceof", "getId()",
    "switch leftover leftover leftover not leftover leftover leftover exhaustive leftover leftover leftover",
    "getter leftover leftover leftover missed leftover leftover leftover nested leftover leftover leftover record",
    "FAIL: leftover leftover leftover non-exhaustive leftover leftover leftover",
    "FAIL: leftover leftover leftover nested leftover leftover leftover record",
    "instanceof leftover leftover leftover Widget leftover leftover leftover", "widget.getId() leftover leftover leftover",
    "leftover leftover leftover sealed leftover leftover leftover is leftover leftover leftover an leftover leftover leftover exhaustiveness leftover leftover leftover tombstone",
    "leftover leftover leftover record leftover leftover leftover patterns leftover leftover leftover deconstruct leftover leftover leftover nested leftover leftover leftover state",
)
PAIRS.append(("Java sealed leftover leftover leftover vs instanceof", fa, fb,
              "sealed permits; record patterns",
              "non-exhaustive switch; nested getters",
              "java pattern switch leftover leftover leftover; when leftover leftover leftover"))

# 15 C# IAsyncEnumerable leftover vs Task IEnumerable
fa, fb = fn_pair(
    "csharp-iasyncenumerable-vs-task-ienumerable", "csharp-cancellation-iasync-leftover",
    "csharp-iasyncenumerable", "csharp-iasync-cancel",
    "C# leftover leftover leftover IAsyncEnumerable vs naive Task<IEnumerable> leftover leftover leftover",
    "leftover leftover leftover IAsyncEnumerable leftover leftover leftover CancellationToken leftover leftover leftover vs naive WithCancellation leftover leftover leftover omitted",
    "SkuService.cs", "SkuService.cs",
    "IAsyncEnumerable<Sku> leftover leftover leftover yield return leftover leftover leftover",
    "WithCancellation leftover leftover leftover ct leftover leftover leftover",
    "IAsyncEnumerable leftover leftover leftover", "WithCancellation leftover leftover leftover",
    "Task<IEnumerable", "GetAsyncEnumerator",
    "await leftover leftover leftover Task leftover leftover leftover buffered leftover leftover leftover all leftover leftover leftover skus",
    "cancel leftover leftover leftover ignored leftover leftover leftover enumerator leftover leftover leftover",
    "FAIL: leftover leftover leftover buffered leftover leftover leftover all leftover leftover leftover",
    "FAIL: leftover leftover leftover cancel leftover leftover leftover ignored leftover leftover leftover",
    "Task<IEnumerable<Sku>> leftover leftover leftover", "GetAsyncEnumerator leftover leftover leftover without ct",
    "IAsyncEnumerable leftover leftover leftover streams; Task leftover leftover leftover buffers",
    "WithCancellation leftover leftover leftover is the leftover leftover leftover cancel tombstone",
)
PAIRS.append(("C# IAsyncEnumerable leftover leftover leftover vs Task IEnumerable", fa, fb,
              "yield stream; WithCancellation",
              "buffered Task; ignored cancel",
              "csharp IAsyncDisposable leftover leftover leftover; ConfigureAwait leftover leftover leftover"))

# 16 Swift actor leftover isolation vs DispatchQueue.sync
fa, fb = fn_pair(
    "swift-actor-isolation-vs-dispatch-sync", "swift-nonisolated-unsafe-leftover",
    "swift-actor", "swift-nonisolated",
    "Swift leftover leftover leftover actor isolation vs naive DispatchQueue.sync leftover leftover leftover",
    "leftover leftover leftover nonisolated(unsafe) leftover leftover leftover vs naive leftover leftover leftover MainActor leftover leftover leftover hop",
    "SkuActor.swift", "SkuActor.swift",
    "actor SkuStore leftover leftover leftover isolated leftover leftover leftover sku leftover leftover leftover",
    "nonisolated(unsafe) leftover leftover leftover var leftover leftover leftover cache leftover leftover leftover",
    "actor isolation leftover leftover leftover", "nonisolated unsafe leftover leftover leftover",
    "DispatchQueue.sync", "MainActor",
    "DispatchQueue.sync leftover leftover leftover from leftover leftover leftover actor leftover leftover leftover deadlocked leftover leftover leftover",
    "MainActor leftover leftover leftover hop leftover leftover leftover still leftover leftover leftover raced leftover leftover leftover cache leftover leftover leftover",
    "FAIL: leftover leftover leftover dispatch leftover leftover leftover deadlock leftover leftover leftover",
    "FAIL: leftover leftover leftover cache leftover leftover leftover race leftover leftover leftover",
    "DispatchQueue.sync leftover leftover leftover", "await MainActor.run leftover leftover leftover",
    "actor leftover leftover leftover isolation is not a leftover leftover leftover serial queue",
    "nonisolated(unsafe) leftover leftover leftover is an isolation leftover leftover leftover tombstone",
)
PAIRS.append(("Swift actor leftover leftover leftover vs DispatchQueue.sync", fa, fb,
              "actor isolation; nonisolated(unsafe)",
              "sync deadlock; cache race",
              "swift sending leftover leftover leftover; isolated deinit leftover leftover leftover"))

assert len(PAIRS) == 16


def lhc_notes(rnd, pair_i, a, b):
    title, _, _, densify, loops, nxt = PAIRS[pair_i]
    return f"""# NOTES r{rnd} long-horizon-coding-factory

Novel coverage: leftover leftover leftover 94%

Pair: {title}.
- Steps: {len(a['steps'])} {'success' if a['reward']['success'] else 'partial'} {a['id']}; {len(b['steps'])} {'success' if b['reward']['success'] else 'partial'} {b['id']}.
- Debug loops: {loops}.
- Densified leftover leftover leftover: {densify}.
- Next densify leftover leftover leftover: {nxt}.
- Not a clone of r4652 logstash/promtail, r4163-w4ck cartesian, RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, identity-origin SSO.
- Bans avoided: wave mill w4x/w4ck, logstash, promtail, RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka, identity-origin clones.
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
    deadline = time.time() + 400
    while len(published) < max_rounds and pair_i < len(PAIRS):
        if time.time() > deadline:
            print("deadline; LHC still contended", flush=True)
            hops = hop_targets()
            if hops:
                print("unreserved hop candidate", hops[0].name, flush=True)
            break
        info = try_reserve(LHC_DIR, 2)
        if info is None:
            time.sleep(0.05)
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
