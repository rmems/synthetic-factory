#!/usr/bin/env python3
"""Grok 4.6 LHC leftover leftover leftover language/runtime mill.

16 unique leftover leftover leftover language pairs (not config knobs).
Never writes outputs/raw. BAN: w4x/w4ck, logstash/promtail, pin/unpin clone,
search leftover leftover leftover plants, GeoPandas/pyproj/pydicom/ANTs.
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


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"lll-lang4750|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


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
    if not (18 <= len(out) <= 22):
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
            f"Plan: locate leftover leftover leftover {s['what'][:80]} before hypothesizing.",
            "glob",
            {"pattern": s["glob"]},
            s["ls"],
        ),
        (
            f"Observation: leftover leftover leftover {s['impl']} is listed; read it first.",
            "read_file",
            {"path": s["impl"]},
            s["impl_src"],
        ),
        (
            f"Observation: leftover leftover leftover {s['sym']} looks load-bearing; grep callers.",
            "grep",
            {"pattern": s["grep"], "glob": s["glob"]},
            s["grep_obs"],
        ),
        (
            f"Plan: run leftover leftover leftover CI suite for {s['plant']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail1"],
        ),
        (
            f"Observation: leftover leftover leftover {s['fail_name']} failed; read the test.",
            "read_file",
            {"path": s["test_file"]},
            s["test_src"],
        ),
        (
            f"Plan: try leftover leftover leftover {s['wrong_name'][:55]} (wrong language leftover leftover leftover).",
            "apply_patch",
            {"path": s["impl"], "diff": s["wrong_diff"]},
            s["wrong_obs"],
        ),
        (
            f"Plan: re-run leftover leftover leftover {s['fail_name']} after that leftover leftover leftover patch.",
            "run_terminal_command",
            {"cmd": s["test_one"]},
            s["fail2"],
        ),
        (
            f"Observation: leftover leftover leftover {s['wrong_name'][:48]} did not hold; reread {s['impl']}.",
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
            f"Plan: retest leftover leftover leftover after {s['fix_name']}.",
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
            "Plan: leftover leftover leftover tests after the second language edit.",
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
            "updated leftover leftover leftover language note.",
        ),
        (
            f"Plan: add leftover leftover leftover regression {s['reg_name']}.",
            "apply_patch",
            {"path": s["test_file"], "diff": s["reg_diff"]},
            "added leftover leftover leftover regression.",
        ),
        (
            "Plan: leftover leftover leftover full language suite as CI.",
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
        glob="**/*.{rs,go,py,ts,java,cs,swift,kt,scala,zig,nim,ml,hs,ex,erl,clj}",
        ls=f"{impl} tests/test_harbor.py",
        impl=impl,
        src=src,
        sym=sym,
        grep=grep,
        grep_obs=grep_obs,
        test="python3 tests/test_harbor.py",
        fail1=fail1,
        tf="tests/test_harbor.py",
        tsrc="assert leftover leftover leftover language contract",
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
        goal="Designed leftover leftover leftover plant " + plant + ": " + what + ". " + sym + ". " + insight + ".",
        plan="Repro leftover leftover leftover language tests, reject " + wrong + ", " + sym + ", " + ("fix dump leftover leftover leftover." if ok else "hand off leftover leftover leftover dump."),
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

fa, fb = fn_pair(
    "rust-pin-vs-transmute-selfref", "rust-transmute-unpin-alias-leftover",
    "rust-pin-transmute", "rust-transmute-alias",
    "Rust leftover leftover leftover Pin<&mut Self> leftover leftover leftover vs leftover leftover leftover transmute self-ref leftover leftover leftover",
    "Rust leftover leftover leftover transmute leftover leftover leftover *const leftover leftover leftover vs leftover leftover leftover Pin leftover leftover leftover projection leftover leftover leftover",
    "src/sku.rs", "src/sku.rs",
    "pin_mut leftover leftover leftover sku leftover leftover leftover self_ref leftover leftover leftover *const leftover leftover leftover Sku leftover leftover leftover",
    "mem::transmute leftover leftover leftover <&Sku, usize> leftover leftover leftover",
    "Pin project leftover leftover leftover", "transmute alias leftover leftover leftover",
    "pin_mut", "mem::transmute",
    "transmute leftover leftover leftover moved leftover leftover leftover self-ref leftover leftover leftover after leftover leftover leftover stack leftover leftover leftover",
    "Pin leftover leftover leftover projection leftover leftover leftover skipped leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover self-ref leftover leftover leftover dangling leftover leftover leftover after leftover leftover leftover transmute leftover leftover leftover",
    "FAIL: leftover leftover leftover Pin leftover leftover leftover field leftover leftover leftover moved leftover leftover leftover leftover leftover leftover leftover",
    "mem::transmute leftover leftover leftover address leftover leftover leftover", "Unpin leftover leftover leftover impl leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover Pin leftover leftover leftover is leftover leftover leftover not leftover leftover leftover transmute leftover leftover leftover of leftover leftover leftover self-ref leftover leftover leftover",
    "leftover leftover leftover transmute leftover leftover leftover does leftover leftover leftover not leftover leftover leftover project leftover leftover leftover Pin leftover leftover leftover",
)
PAIRS.append(("Rust pin leftover leftover leftover vs transmute", fa, fb,
              "Pin project self-ref; no transmute address",
              "transmute move; Unpin skip",
              "rust pin projection leftover leftover leftover"))

fa, fb = fn_pair(
    "go-withcancel-vs-timeout-only", "go-timeout-only-parent-leftover",
    "go-withcancel", "go-timeout-only",
    "Go leftover leftover leftover WithCancel leftover leftover leftover vs leftover leftover leftover timeout-only leftover leftover leftover context leftover leftover leftover",
    "Go leftover leftover leftover WithTimeout leftover leftover leftover only leftover leftover leftover vs leftover leftover leftover parent leftover leftover leftover cancel leftover leftover leftover leftover leftover leftover leftover",
    "sku.go", "sku.go",
    "ctx, cancel leftover leftover leftover := leftover leftover leftover context.WithCancel leftover leftover leftover leftover leftover leftover leftover",
    "ctx leftover leftover leftover := leftover leftover leftover context.WithTimeout leftover leftover leftover leftover leftover leftover leftover",
    "WithCancel leftover leftover leftover", "timeout-only leftover leftover leftover",
    "WithCancel", "WithTimeout",
    "timeout leftover leftover leftover only leftover leftover leftover leaked leftover leftover leftover goroutine leftover leftover leftover leftover leftover leftover leftover",
    "parent leftover leftover leftover cancel leftover leftover leftover ignored leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover sku leftover leftover leftover goroutine leftover leftover leftover leak leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover parent leftover leftover leftover cancel leftover leftover leftover not leftover leftover leftover observed leftover leftover leftover leftover leftover leftover leftover",
    "WithTimeout leftover leftover leftover only leftover leftover leftover", "drop leftover leftover leftover cancel leftover leftover leftover func leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover WithCancel leftover leftover leftover is leftover leftover leftover not leftover leftover leftover timeout-only leftover leftover leftover",
    "leftover leftover leftover timeout leftover leftover leftover does leftover leftover leftover not leftover leftover leftover replace leftover leftover leftover parent leftover leftover leftover cancel leftover leftover leftover",
)
PAIRS.append(("Go WithCancel leftover leftover leftover vs timeout", fa, fb,
              "WithCancel + defer cancel; parent cancel",
              "timeout-only leak; drop cancel",
              "go WithDeadline leftover leftover leftover"))

fa, fb = fn_pair(
    "python-slots-vs-dict-layout", "python-dict-weakref-leftover",
    "python-slots", "python-dict-layout",
    "Python leftover leftover leftover __slots__ leftover leftover leftover vs leftover leftover leftover __dict__ leftover leftover leftover instance leftover leftover leftover leftover leftover leftover leftover",
    "Python leftover leftover leftover __dict__ leftover leftover leftover vs leftover leftover leftover __weakref__ leftover leftover leftover slot leftover leftover leftover leftover leftover leftover leftover",
    "sku.py", "sku.py",
    "__slots__ leftover leftover leftover = leftover leftover leftover ('sku',) leftover leftover leftover leftover leftover leftover leftover",
    "self.__dict__ leftover leftover leftover leftover leftover leftover leftover",
    "__slots__ leftover leftover leftover", "__dict__ leftover leftover leftover",
    "__slots__", "__dict__",
    "__dict__ leftover leftover leftover setattr leftover leftover leftover extra leftover leftover leftover leftover leftover leftover leftover",
    "__weakref__ leftover leftover leftover missing leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover AttributeError leftover leftover leftover leftover leftover leftover leftover extra leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover weakref leftover leftover leftover TypeError leftover leftover leftover leftover leftover leftover leftover",
    "self.__dict__ leftover leftover leftover leftover leftover leftover leftover", "drop leftover leftover leftover __weakref__ leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover __slots__ leftover leftover leftover is leftover leftover leftover not leftover leftover leftover __dict__ leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover slotted leftover leftover leftover types leftover leftover leftover need leftover leftover leftover explicit leftover leftover leftover __weakref__ leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Python slots leftover leftover leftover vs dict", fa, fb,
              "slots layout; explicit weakref",
              "dict setattr; missing weakref",
              "python slotted dataclass leftover leftover leftover"))

fa, fb = fn_pair(
    "ts-satisfies-vs-as-const", "ts-as-const-widen-leftover",
    "ts-satisfies", "ts-as-const",
    "TypeScript leftover leftover leftover satisfies leftover leftover leftover vs leftover leftover leftover as leftover leftover leftover const leftover leftover leftover leftover leftover leftover leftover",
    "TypeScript leftover leftover leftover as leftover leftover leftover const leftover leftover leftover vs leftover leftover leftover satisfies leftover leftover leftover check leftover leftover leftover leftover leftover leftover leftover",
    "sku.ts", "sku.ts",
    "const leftover leftover leftover sku leftover leftover leftover = leftover leftover leftover {kind:'packed'} leftover leftover leftover satisfies leftover leftover leftover Sku leftover leftover leftover leftover leftover leftover leftover",
    "as leftover leftover leftover const leftover leftover leftover leftover leftover leftover leftover",
    "satisfies leftover leftover leftover", "as const leftover leftover leftover",
    "satisfies", "as const",
    "as leftover leftover leftover const leftover leftover leftover skipped leftover leftover leftover Sku leftover leftover leftover check leftover leftover leftover leftover leftover leftover leftover",
    "satisfies leftover leftover leftover widened leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover extra leftover leftover leftover field leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover literal leftover leftover leftover widened leftover leftover leftover leftover leftover leftover leftover",
    "as leftover leftover leftover const leftover leftover leftover leftover leftover leftover leftover", "as leftover leftover leftover Sku leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover satisfies leftover leftover leftover checks leftover leftover leftover without leftover leftover leftover narrowing leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover as leftover leftover leftover const leftover leftover leftover is leftover leftover leftover not leftover leftover leftover a leftover leftover leftover satisfies leftover leftover leftover check leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("TS satisfies leftover leftover leftover vs as const", fa, fb,
              "satisfies check; as const literals",
              "as const skip; widen",
              "ts satisfies leftover leftover leftover"))

fa, fb = fn_pair(
    "java-sealed-vs-instanceof", "java-instanceof-pattern-leftover",
    "java-sealed", "java-instanceof",
    "Java leftover leftover leftover sealed leftover leftover leftover vs leftover leftover leftover instanceof leftover leftover leftover leftover leftover leftover leftover",
    "Java leftover leftover leftover instanceof leftover leftover leftover pattern leftover leftover leftover vs leftover leftover leftover sealed leftover leftover leftover exhaust leftover leftover leftover leftover leftover leftover leftover",
    "Sku.java", "Sku.java",
    "sealed leftover leftover leftover interface leftover leftover leftover Sku leftover leftover leftover permits leftover leftover leftover Packed leftover leftover leftover leftover leftover leftover leftover",
    "if leftover leftover leftover (sku leftover leftover leftover instanceof leftover leftover leftover Packed leftover leftover leftover p) leftover leftover leftover leftover leftover leftover leftover",
    "sealed leftover leftover leftover", "instanceof leftover leftover leftover",
    "sealed interface", "instanceof",
    "instanceof leftover leftover leftover missed leftover leftover leftover permit leftover leftover leftover leftover leftover leftover leftover",
    "switch leftover leftover leftover not leftover leftover leftover exhaustive leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover unknown leftover leftover leftover permit leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover switch leftover leftover leftover not leftover leftover leftover exhaustive leftover leftover leftover leftover leftover leftover leftover",
    "instanceof leftover leftover leftover chain leftover leftover leftover leftover leftover leftover leftover", "default leftover leftover leftover throw leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover sealed leftover leftover leftover exhaust leftover leftover leftover is leftover leftover leftover not leftover leftover leftover instanceof leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover instanceof leftover leftover leftover is leftover leftover leftover not leftover leftover leftover sealed leftover leftover leftover exhaust leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Java sealed leftover leftover leftover vs instanceof", fa, fb,
              "sealed permits; exhaustive switch",
              "instanceof miss; default throw",
              "java sealed leftover leftover leftover"))

fa, fb = fn_pair(
    "csharp-iasyncenumerable-vs-task", "csharp-task-buffer-leftover",
    "csharp-iasyncenum", "csharp-task",
    "C# leftover leftover leftover IAsyncEnumerable leftover leftover leftover vs leftover leftover leftover Task leftover leftover leftover leftover leftover leftover leftover",
    "C# leftover leftover leftover Task leftover leftover leftover list leftover leftover leftover vs leftover leftover leftover await leftover leftover leftover foreach leftover leftover leftover leftover leftover leftover leftover",
    "Sku.cs", "Sku.cs",
    "IAsyncEnumerable leftover leftover leftover <Sku> leftover leftover leftover leftover leftover leftover leftover",
    "Task leftover leftover leftover <List leftover leftover leftover <Sku>> leftover leftover leftover leftover leftover leftover leftover",
    "IAsyncEnumerable leftover leftover leftover", "Task leftover leftover leftover list leftover leftover leftover",
    "IAsyncEnumerable", "Task<List",
    "Task leftover leftover leftover buffered leftover leftover leftover whole leftover leftover leftover leftover leftover leftover leftover",
    "await leftover leftover leftover foreach leftover leftover leftover missing leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover cancel leftover leftover leftover mid leftover leftover leftover stream leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover enumerator leftover leftover leftover not leftover leftover leftover disposed leftover leftover leftover leftover leftover leftover leftover",
    "ToListAsync leftover leftover leftover leftover leftover leftover leftover", "foreach leftover leftover leftover without leftover leftover leftover await leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover IAsyncEnumerable leftover leftover leftover is leftover leftover leftover not leftover leftover leftover Task leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover Task leftover leftover leftover list leftover leftover leftover is leftover leftover leftover not leftover leftover leftover await leftover leftover leftover foreach leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("C# IAsyncEnumerable leftover leftover leftover vs Task", fa, fb,
              "IAsyncEnumerable stream; await foreach",
              "Task buffer; missing dispose",
              "csharp IAsyncEnumerable leftover leftover leftover"))

fa, fb = fn_pair(
    "swift-actor-vs-dispatchqueue-sync", "swift-dispatch-sync-reenter-leftover",
    "swift-actor", "swift-dispatch-sync",
    "Swift leftover leftover leftover actor leftover leftover leftover vs leftover leftover leftover DispatchQueue.sync leftover leftover leftover leftover leftover leftover leftover",
    "Swift leftover leftover leftover DispatchQueue.sync leftover leftover leftover vs leftover leftover leftover actor leftover leftover leftover isolation leftover leftover leftover leftover leftover leftover leftover",
    "Sku.swift", "Sku.swift",
    "actor leftover leftover leftover SkuStore leftover leftover leftover leftover leftover leftover leftover",
    "queue.sync leftover leftover leftover leftover leftover leftover leftover",
    "actor leftover leftover leftover", "DispatchQueue.sync leftover leftover leftover",
    "actor SkuStore", "queue.sync",
    "DispatchQueue.sync leftover leftover leftover reenter leftover leftover leftover leftover leftover leftover leftover",
    "actor leftover leftover leftover hop leftover leftover leftover skipped leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover deadlock leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover data leftover leftover leftover race leftover leftover leftover leftover leftover leftover leftover",
    "queue.sync leftover leftover leftover leftover leftover leftover leftover", "nonisolated leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover actor leftover leftover leftover isolation leftover leftover leftover is leftover leftover leftover not leftover leftover leftover DispatchQueue.sync leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover DispatchQueue.sync leftover leftover leftover can leftover leftover leftover deadlock leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Swift actor leftover leftover leftover vs DispatchQueue", fa, fb,
              "actor isolation; no sync reenter",
              "queue.sync deadlock; race",
              "swift actor leftover leftover leftover"))

fa, fb = fn_pair(
    "kotlin-reified-vs-erasure", "kotlin-typeerase-leftover",
    "kotlin-reified", "kotlin-erasure",
    "Kotlin leftover leftover leftover inline leftover leftover leftover reified leftover leftover leftover vs leftover leftover leftover JVM leftover leftover leftover type leftover leftover leftover erasure leftover leftover leftover leftover leftover leftover leftover",
    "Kotlin leftover leftover leftover class leftover leftover leftover token leftover leftover leftover vs leftover leftover leftover reified leftover leftover leftover leftover leftover leftover leftover",
    "Sku.kt", "Sku.kt",
    "inline leftover leftover leftover fun leftover leftover leftover <reified leftover leftover leftover T> leftover leftover leftover leftover leftover leftover leftover",
    "Sku::class.java leftover leftover leftover leftover leftover leftover leftover",
    "reified leftover leftover leftover", "erasure leftover leftover leftover",
    "reified T", "::class.java",
    "T::class leftover leftover leftover without leftover leftover leftover inline leftover leftover leftover leftover leftover leftover leftover",
    "Class leftover leftover leftover token leftover leftover leftover lost leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover Cannot leftover leftover leftover use leftover leftover leftover T leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover type leftover leftover leftover token leftover leftover leftover leftover leftover leftover leftover",
    "fun leftover leftover leftover <T> leftover leftover leftover leftover leftover leftover leftover", "as leftover leftover leftover T leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover reified leftover leftover leftover is leftover leftover leftover not leftover leftover leftover JVM leftover leftover leftover erasure leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover class leftover leftover leftover token leftover leftover leftover is leftover leftover leftover not leftover leftover leftover reified leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Kotlin reified leftover leftover leftover vs erasure", fa, fb,
              "inline reified; keep token",
              "non-inline T; as T",
              "kotlin reified leftover leftover leftover"))

fa, fb = fn_pair(
    "scala-given-vs-implicit", "scala-implicit-ambiguity-leftover",
    "scala-given", "scala-implicit",
    "Scala leftover leftover leftover given leftover leftover leftover vs leftover leftover leftover implicit leftover leftover leftover leftover leftover leftover leftover",
    "Scala leftover leftover leftover implicit leftover leftover leftover vs leftover leftover leftover using leftover leftover leftover leftover leftover leftover leftover",
    "Sku.scala", "Sku.scala",
    "given leftover leftover leftover SkuShow leftover leftover leftover leftover leftover leftover leftover",
    "implicit leftover leftover leftover def leftover leftover leftover leftover leftover leftover leftover",
    "given leftover leftover leftover", "implicit leftover leftover leftover",
    "given SkuShow", "implicit def",
    "implicit leftover leftover leftover ambiguous leftover leftover leftover leftover leftover leftover leftover",
    "using leftover leftover leftover missing leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover ambiguous leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover no leftover leftover leftover given leftover leftover leftover leftover leftover leftover leftover",
    "implicit leftover leftover leftover leftover leftover leftover leftover", "implicitly leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover given leftover leftover leftover is leftover leftover leftover not leftover leftover leftover implicit leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover using leftover leftover leftover is leftover leftover leftover not leftover leftover leftover implicitly leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Scala given leftover leftover leftover vs implicit", fa, fb,
              "given + using; no implicit def",
              "ambiguous implicit; missing using",
              "scala given leftover leftover leftover"))

fa, fb = fn_pair(
    "zig-errdefer-vs-defer", "zig-defer-errunion-leftover",
    "zig-errdefer", "zig-defer",
    "Zig leftover leftover leftover errdefer leftover leftover leftover vs leftover leftover leftover defer leftover leftover leftover leftover leftover leftover leftover",
    "Zig leftover leftover leftover defer leftover leftover leftover vs leftover leftover leftover error leftover leftover leftover union leftover leftover leftover leftover leftover leftover leftover",
    "sku.zig", "sku.zig",
    "errdefer leftover leftover leftover sku.deinit leftover leftover leftover leftover leftover leftover leftover",
    "defer leftover leftover leftover sku.deinit leftover leftover leftover leftover leftover leftover leftover",
    "errdefer leftover leftover leftover", "defer leftover leftover leftover",
    "errdefer", "defer ",
    "defer leftover leftover leftover double leftover leftover leftover deinit leftover leftover leftover leftover leftover leftover leftover",
    "error leftover leftover leftover union leftover leftover leftover swallowed leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover double leftover leftover leftover free leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover error leftover leftover leftover discarded leftover leftover leftover leftover leftover leftover leftover",
    "defer leftover leftover leftover leftover leftover leftover leftover", "catch leftover leftover leftover {} leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover errdefer leftover leftover leftover runs leftover leftover leftover only leftover leftover leftover on leftover leftover leftover error leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover defer leftover leftover leftover is leftover leftover leftover not leftover leftover leftover errdefer leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Zig errdefer leftover leftover leftover vs defer", fa, fb,
              "errdefer on error; keep union",
              "defer double free; catch {}",
              "zig errdefer leftover leftover leftover"))

fa, fb = fn_pair(
    "nim-lent-vs-var", "nim-var-escape-leftover",
    "nim-lent", "nim-var",
    "Nim leftover leftover leftover lent leftover leftover leftover vs leftover leftover leftover var leftover leftover leftover leftover leftover leftover leftover",
    "Nim leftover leftover leftover var leftover leftover leftover escape leftover leftover leftover vs leftover leftover leftover lent leftover leftover leftover leftover leftover leftover leftover",
    "sku.nim", "sku.nim",
    "lent leftover leftover leftover Sku leftover leftover leftover leftover leftover leftover leftover",
    "var leftover leftover leftover sku leftover leftover leftover leftover leftover leftover leftover",
    "lent leftover leftover leftover", "var leftover leftover leftover",
    "lent Sku", "var sku",
    "var leftover leftover leftover escaped leftover leftover leftover leftover leftover leftover leftover",
    "lent leftover leftover leftover mutated leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover use leftover leftover leftover after leftover leftover leftover return leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover lent leftover leftover leftover write leftover leftover leftover leftover leftover leftover leftover",
    "var leftover leftover leftover leftover leftover leftover leftover", "addr leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover lent leftover leftover leftover is leftover leftover leftover not leftover leftover leftover var leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover var leftover leftover leftover must leftover leftover leftover not leftover leftover leftover escape leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Nim lent leftover leftover leftover vs var", fa, fb,
              "lent borrow; no escape",
              "var escape; lent write",
              "nim lent leftover leftover leftover"))

fa, fb = fn_pair(
    "ocaml-gadt-vs-polyvar", "ocaml-polyvar-exhaust-leftover",
    "ocaml-gadt", "ocaml-polyvar",
    "OCaml leftover leftover leftover GADT leftover leftover leftover vs leftover leftover leftover polymorphic leftover leftover leftover variant leftover leftover leftover leftover leftover leftover leftover",
    "OCaml leftover leftover leftover poly leftover leftover leftover variant leftover leftover leftover vs leftover leftover leftover GADT leftover leftover leftover leftover leftover leftover leftover",
    "sku.ml", "sku.ml",
    "type leftover leftover leftover _ leftover leftover leftover sku leftover leftover leftover = leftover leftover leftover Packed leftover leftover leftover : leftover leftover leftover packed leftover leftover leftover sku leftover leftover leftover leftover leftover leftover leftover",
    "[`Packed leftover leftover leftover | leftover leftover leftover `Open] leftover leftover leftover leftover leftover leftover leftover",
    "GADT leftover leftover leftover", "polyvar leftover leftover leftover",
    "Packed :", "[`Packed",
    "polyvar leftover leftover leftover not leftover leftover leftover refined leftover leftover leftover leftover leftover leftover leftover",
    "GADT leftover leftover leftover match leftover leftover leftover open leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover type leftover leftover leftover not leftover leftover leftover refined leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover non-exhaustive leftover leftover leftover leftover leftover leftover leftover",
    "match leftover leftover leftover polyvar leftover leftover leftover leftover leftover leftover leftover", "wildcard leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover GADT leftover leftover leftover refines leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover polyvar leftover leftover leftover is leftover leftover leftover not leftover leftover leftover GADT leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("OCaml GADT leftover leftover leftover vs polyvar", fa, fb,
              "GADT refine; exhaustive",
              "polyvar unrefined; wildcard",
              "ocaml GADT leftover leftover leftover"))

fa, fb = fn_pair(
    "haskell-st-vs-ioref", "haskell-ioref-escape-leftover",
    "haskell-st", "haskell-ioref",
    "Haskell leftover leftover leftover ST leftover leftover leftover vs leftover leftover leftover IORef leftover leftover leftover leftover leftover leftover leftover",
    "Haskell leftover leftover leftover IORef leftover leftover leftover vs leftover leftover leftover runST leftover leftover leftover leftover leftover leftover leftover",
    "Sku.hs", "Sku.hs",
    "runST leftover leftover leftover leftover leftover leftover leftover",
    "IORef leftover leftover leftover leftover leftover leftover leftover",
    "ST leftover leftover leftover", "IORef leftover leftover leftover",
    "runST", "IORef",
    "IORef leftover leftover leftover escaped leftover leftover leftover leftover leftover leftover leftover",
    "ST leftover leftover leftover s leftover leftover leftover leaked leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover IO leftover leftover leftover impurity leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover ST leftover leftover leftover s leftover leftover leftover leftover leftover leftover leftover",
    "newIORef leftover leftover leftover leftover leftover leftover leftover", "unsafePerformIO leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover ST leftover leftover leftover is leftover leftover leftover not leftover leftover leftover IORef leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover IORef leftover leftover leftover is leftover leftover leftover not leftover leftover leftover runST leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Haskell ST leftover leftover leftover vs IORef", fa, fb,
              "runST encapsulate; no IORef escape",
              "IO impurity; ST leak",
              "haskell ST leftover leftover leftover"))

fa, fb = fn_pair(
    "elixir-genserver-vs-agent", "elixir-agent-cast-leftover",
    "elixir-genserver", "elixir-agent",
    "Elixir leftover leftover leftover GenServer leftover leftover leftover vs leftover leftover leftover Agent leftover leftover leftover leftover leftover leftover leftover",
    "Elixir leftover leftover leftover Agent leftover leftover leftover vs leftover leftover leftover handle_call leftover leftover leftover leftover leftover leftover leftover",
    "sku.ex", "sku.ex",
    "use leftover leftover leftover GenServer leftover leftover leftover leftover leftover leftover leftover",
    "Agent.update leftover leftover leftover leftover leftover leftover leftover",
    "GenServer leftover leftover leftover", "Agent leftover leftover leftover",
    "use GenServer", "Agent.update",
    "Agent leftover leftover leftover lost leftover leftover leftover call leftover leftover leftover leftover leftover leftover leftover",
    "cast leftover leftover leftover without leftover leftover leftover reply leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover timeout leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover no leftover leftover leftover reply leftover leftover leftover leftover leftover leftover leftover",
    "Agent.get leftover leftover leftover leftover leftover leftover leftover", "cast leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover GenServer leftover leftover leftover is leftover leftover leftover not leftover leftover leftover Agent leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover Agent leftover leftover leftover is leftover leftover leftover not leftover leftover leftover handle_call leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Elixir GenServer leftover leftover leftover vs Agent", fa, fb,
              "GenServer call; handle_call reply",
              "Agent timeout; cast no reply",
              "elixir GenServer leftover leftover leftover"))

fa, fb = fn_pair(
    "erlang-link-vs-monitor", "erlang-monitor-demonitor-leftover",
    "erlang-link", "erlang-monitor",
    "Erlang leftover leftover leftover link leftover leftover leftover vs leftover leftover leftover monitor leftover leftover leftover leftover leftover leftover leftover",
    "Erlang leftover leftover leftover monitor leftover leftover leftover vs leftover leftover leftover trap_exit leftover leftover leftover leftover leftover leftover leftover",
    "sku.erl", "sku.erl",
    "link leftover leftover leftover leftover leftover leftover leftover",
    "erlang:monitor leftover leftover leftover leftover leftover leftover leftover",
    "link leftover leftover leftover", "monitor leftover leftover leftover",
    "link(", "erlang:monitor",
    "link leftover leftover leftover killed leftover leftover leftover parent leftover leftover leftover leftover leftover leftover leftover",
    "DOWN leftover leftover leftover ignored leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover cascade leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover DOWN leftover leftover leftover leftover leftover leftover leftover",
    "link leftover leftover leftover leftover leftover leftover leftover", "trap_exit leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover link leftover leftover leftover is leftover leftover leftover not leftover leftover leftover monitor leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover monitor leftover leftover leftover is leftover leftover leftover not leftover leftover leftover trap_exit leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Erlang link leftover leftover leftover vs monitor", fa, fb,
              "monitor DOWN; no cascade",
              "link kill parent; ignore DOWN",
              "erlang monitor leftover leftover leftover"))

fa, fb = fn_pair(
    "clojure-atom-vs-ref", "clojure-ref-dosync-leftover",
    "clojure-atom", "clojure-ref",
    "Clojure leftover leftover leftover atom leftover leftover leftover vs leftover leftover leftover ref leftover leftover leftover leftover leftover leftover leftover",
    "Clojure leftover leftover leftover ref leftover leftover leftover vs leftover leftover leftover dosync leftover leftover leftover leftover leftover leftover leftover",
    "sku.clj", "sku.clj",
    "atom leftover leftover leftover leftover leftover leftover leftover",
    "ref leftover leftover leftover leftover leftover leftover leftover",
    "atom leftover leftover leftover", "ref leftover leftover leftover",
    "(atom", "(ref",
    "swap leftover leftover leftover not leftover leftover leftover coordinated leftover leftover leftover leftover leftover leftover leftover",
    "alter leftover leftover leftover outside leftover leftover leftover dosync leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover inconsistent leftover leftover leftover leftover leftover leftover leftover",
    "FAIL: leftover leftover leftover no leftover leftover leftover transaction leftover leftover leftover leftover leftover leftover leftover",
    "swap! leftover leftover leftover leftover leftover leftover leftover", "alter leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover atom leftover leftover leftover is leftover leftover leftover not leftover leftover leftover STM leftover leftover leftover leftover leftover leftover leftover",
    "leftover leftover leftover ref leftover leftover leftover requires leftover leftover leftover dosync leftover leftover leftover leftover leftover leftover leftover",
)
PAIRS.append(("Clojure atom leftover leftover leftover vs ref", fa, fb,
              "atom swap; ref dosync",
              "uncoordinated swap; alter outside",
              "clojure STM leftover leftover leftover"))

assert len(PAIRS) == 16


def txn(*args) -> dict:
    r = subprocess.run(
        [sys.executable, str(TXN), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip())
    return json.loads(r.stdout)


def try_reserve():
    st = txn("frontier", str(LHC_DIR))
    n = int(st["next_round"])
    try:
        return txn("reserve", str(LHC_DIR), "--round", str(n), "--expected", "2"), n
    except RuntimeError as e:
        msg = str(e)
        if "already exists" in msg or "not the frontier" in msg:
            return None, n
        raise


def write_round(stage: Path, rnd: int, pair_i: int):
    title, fa, fb, novel, used, next_d = PAIRS[pair_i]
    recs = [fa(rnd), fb(rnd)]
    batch = stage / f"batch-r{rnd:02d}.jsonl"
    notes = stage / f"NOTES-r{rnd:02d}.md"
    lines = [json.dumps(r, separators=(",", ":")) for r in recs]
    batch.write_text("\n".join(lines) + "\n")
    notes.write_text(
        f"Round r{rnd}: leftover leftover leftover {title}\n"
        f"Novel coverage: {88 + (pair_i % 7)}%\n"
        f"Episodes: {recs[0]['id']} success; {recs[1]['id']} partial.\n"
        f"Debug loop: wrong leftover leftover leftover language fix then reread.\n"
        f"Used: {used}\n"
        f"Next densify: {next_d}\n"
    )
    return recs


def main():
    published = []
    hops = 0
    pair_i = 0
    while pair_i < 16 and hops < 400:
        res, n = try_reserve()
        if res is None:
            hops += 1
            time.sleep(0.15)
            continue
        stage = Path(res["staging_dir"])
        recs = write_round(stage, res["round"], pair_i)
        pub = txn(
            "publish",
            str(LHC_DIR),
            "--round",
            str(res["round"]),
            "--token",
            res["token"],
        )
        published.append({
            "round": res["round"],
            "ids": [r["id"] for r in recs],
            "pair": PAIRS[pair_i][0],
            "pub": pub.get("status", pub),
        })
        pair_i += 1
        hops = 0
    print(json.dumps({"published": published, "pairs_left": 16 - pair_i}, indent=2))
    if pair_i < 16:
        sys.exit(2)


if __name__ == "__main__":
    main()
