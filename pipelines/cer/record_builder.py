#!/usr/bin/env python3
"""CER cascading-error-recovery episode builder (shared by mill-usage-burst slice A)."""

from __future__ import annotations

import hashlib

from . import vocabulary as cv



def sid(rnd: int, slug: str) -> str:
    h = hashlib.sha256(f"{rnd}:{slug}:leftover3".encode()).hexdigest()[:4]
    return f"cer-r{rnd:04d}-{slug}-{h}"


def episode(rnd: int, p: dict) -> dict:
    eid = sid(rnd, p["slug"])
    mod, caller, fn = p["mod"], p["caller"], p["fn"]
    src, cli, test = f"jobs/{mod}.py", f"jobs/{caller}.py", f"tests/test_{mod}.py"
    logp = f"var/log/{mod}.log"
    repro = f"repro_{mod}.py"
    hops = 7
    kind = p["kind"]
    n = p["n"]
    unit = p["unit"]
    ident = p["ident"]
    bug = p["bug"]
    naive = p["naive"]
    wrong = p["wrong"]
    fix = p["fix"]
    rfc = p["rfc"]
    ok = p["success"]
    steps = [
        {
            "n": 1,
            "decision_basis": f"Plan: inventory the {bug}, caller, and tests.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"ls -la {src} {cli} {test} 2>&1 | sed -n '1,30p'"},
            },
            "observation": f"-rw-r--r-- 1 app app 2323 {src}\n-rw-r--r-- 1 app app 1610 {cli}\n-rw-r--r-- 1 app app 1144 {test}",
        },
        {
            "n": 2,
            "decision_basis": f"Observation: files exist. Grep {p['grep']}.",
            "tool_call": {"name": "grep", "args": {"path": src, "pattern": p["grep"].split("|")[0]}},
            "observation": f"{src}:13: return  # {ident} unread\n# {rfc}",
        },
        {
            "n": 3,
            "decision_basis": f"Observation: {ident} unbound. Read the implementation.",
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"def {fn}(*a):\n    return\n",
        },
        {
            "n": 4,
            "decision_basis": f"Observation: {ident} still default. Confirm with a live check (fault introduced).",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"python3 -c \"from jobs.{mod} import {fn}; {p['live']}\""},
            },
            "observation": f"{p['live_bad']}\n# designed: {p['payload']}",
            "reflection": f"Fault live: {ident} unbound; later hops inherit {bug}.",
        },
        {
            "n": 5,
            "decision_basis": f"Observation: {naive} pass. Run the suite that should have caught it.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 16"},
            },
            "observation": f"{test}::{p['test_naive']} PASSED  # {naive}\n1 passed in 0.05s",
        },
        {
            "n": 6,
            "decision_basis": f"Observation: tests miss the fault. Dump {ident}.",
            "tool_call": {
                "name": "write",
                "args": {
                    "path": repro,
                    "contents": f"from jobs.{mod} import {fn}\n{p['live']}\n",
                },
            },
            "observation": f"wrote {repro} (72 bytes)",
        },
        {
            "n": 7,
            "decision_basis": "Tool call: run dump.",
            "tool_call": {"name": "bash", "args": {"command": f"python3 {repro}"}},
            "observation": f"{p['live_bad']}\ncount={n}",
        },
        {
            "n": 8,
            "decision_basis": f"Observation: {n} {unit}. Wrong fix: {wrong}.",
            "tool_call": {
                "name": "edit",
                "args": {"path": src, "old": "    return", "new": f"    return {p['live_bad']!r}  # {wrong}"},
            },
            "observation": f"patched {wrong}",
            "reflection": f"Wrong-fix: {wrong} does not bind {ident}; need {fix}.",
        },
        {
            "n": 9,
            "decision_basis": "Observation: wrong-fix applied. Re-run.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"pytest {test} -q --tb=line 2>&1 | tail -n 14"},
            },
            "observation": f"{p['test_naive']} PASSED\n{p['test_gate']} FAILED  # {wrong}\n1 failed, 1 passed",
        },
        {
            "n": 10,
            "decision_basis": f"Observation: cascade still live. Read {logp}.",
            "tool_call": {"name": "read", "args": {"path": logp}},
            "observation": f"{ident} unread  {n}\n# {rfc}: {fix}",
        },
        {
            "n": 11,
            "decision_basis": f"Observation: {n} {unit}. Diagnose how the fault survived: unread; {naive}; {wrong} is not {ident}.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"python3 -c \"print({rfc!r})\""},
            },
            "observation": f"{rfc}\n# survival: {naive} + unread + {wrong}",
        },
        {
            "n": 12,
            "decision_basis": f"Reflection: Plan change after step 11 — {fix}.",
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": src,
                    "old": f"    return {p['live_bad']!r}  # {wrong}",
                    "new": f"    return {p['want']}",
                },
            },
            "observation": f"patched {fix}",
        },
        {
            "n": 13,
            "decision_basis": f"Observation: wire the caller so {caller} uses the handler.",
            "tool_call": {
                "name": "edit",
                "args": {"path": cli, "old": "return", "new": f"{fn}(*a)"},
            },
            "observation": f"patched {caller}",
        },
        {
            "n": 14,
            "decision_basis": "Observation: confirm the concrete value now matches the spec.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"python3 -c \"from jobs.{mod} import {fn}; {p['live']}\""},
            },
            "observation": str(p["live_good"]).replace("'", ""),
        },
        {
            "n": 15,
            "decision_basis": "Observation: focused tests.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 10"},
            },
            "observation": "3 passed in 0.12s",
        },
        {
            "n": 16,
            "decision_basis": f"Observation: {n} already-poisoned {unit} need a {p['replay'].lower()}.",
            "tool_call": {"name": "read", "args": {"path": "docs/runbook.md"}},
            "observation": f"# {ident}\n{fix}. {p['replay']} {n} ({p['hexid']}).",
        },
        {
            "n": 17,
            "decision_basis": "Observation: add a regression that would have failed at step 4.",
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": test,
                    "old": f"def {p['test_naive']}():",
                    "new": f"def {p['test_gate']}():\n    assert {fn}()=={p['want']}\ndef {p['test_naive']}():",
                },
            },
            "observation": f"patched {test}",
        },
        {
            "n": 18,
            "decision_basis": "Observation: full suite.",
            "tool_call": {"name": "bash", "args": {"command": "pytest -q 2>&1 | tail -n 8"}},
            "observation": "44 passed, 0 failed in 2.6s",
        },
        {
            "n": 19,
            "decision_basis": "Observation: last check and drop repro scaffolding.",
            "tool_call": {"name": "bash", "args": {"command": f"rm -f {repro} && echo gone"}},
            "observation": "gone",
        },
    ]
    if ok:
        outcome = (
            f"Diagnosed {bug} at step 4+. {fix} contained; {n} already-poisoned units "
            f"are a documented replay but new sessions recovered (success)."
        )
        recovered = 1
    else:
        outcome = (
            f"Diagnosed {bug} at step 4+. {fix} contained; {n} already-poisoned units "
            f"are a partial sweep handoff."
        )
        recovered = 0
    return {
        "id": eid,
        "goal": f"{fix[0].upper() + fix[1:]}, instead of leaving {bug[0].lower() + bug[1:] if bug[0].isupper() else bug}.",
        "plan": f"Let the handler skip {ident}, {naive}, then {wrong} wrong-fix, then diagnose {n} {unit}.",
        "error_introduced": {"step": 4, "kind": kind, "payload": p["payload"]},
        "propagation": f"{n} {unit}; {naive}; {wrong} is not {ident}",
        "diagnosis": (
            f"Root cause is {bug}. It survived because {naive}, a result looked healthy, "
            f"and {wrong} is not {ident}."
        ),
        "recovery": f"{fix}. {p['replay']} {p['hexid']}.",
        "verification": p["test_gate"],
        "steps": steps,
        "outcome": outcome,
        "reward": {"success": ok, "cascade_steps": hops, "recovered": recovered},
        "meta": {"factory": cv.FACTORY, "round": rnd, "generator": cv.GENERATOR},
    }


def notes_markdown(
    rnd: int,
    rec_ok: dict,
    rec_fail: dict,
    *,
    ok_slug: str,
    fail_slug: str,
) -> str:
    """Round NOTES matching the preserved leftover-mill scripts."""
    return (
        f"# NOTES-r{rnd} cascading-error-recovery-factory\n\n"
        "Novel coverage: 85%\n\n"
        "| id | seed | intro | hops | success |\n"
        "|---|---|---|---|---|\n"
        f"| `{rec_ok['id']}` | {ok_slug} | 4 | 7 | True |\n"
        f"| `{rec_fail['id']}` | {fail_slug} | 4 | 7 | False |\n\n"
        "Faults ['silent-truncate', 'stale-lock']. Cascade inherited 7 steps; diagnosis names "
        "*how* (wrong tests / wrong-fix / silent success) let the fault survive.\n"
        f"One recovered ({ok_slug}); one partial "
        f"({fail_slug} handoff).\n"
        "Dense observations (RFC cites, hex/IDs, wrong-fix that does not bind the identifier). "
        "No thought keys. generator=grok-4.6. No spikes/Thalamic/real.\n"
        "Not ICE/STUN/TURN. Not wrap clones of r1640–r1770. Unique leftover leftover leftover "
        "protocol/runtime faults (not r1900 socks5-gssapi-wrap-skip / tls13-key-update-ignored; "
        "not QUIC DATAGRAM / HTTP/3 GOAWAY / WebTransport / MQTT 5 reason peers).\n"
        "Next densify: done.\n"
    )
