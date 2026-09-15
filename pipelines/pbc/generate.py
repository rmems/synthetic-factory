#!/usr/bin/env python3
"""PBC episode builder and AST-only mill-source extract. Never execs mills."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from . import _contract
from ._contract import FACTORY, GENERATOR, VENDOR_PREFIX

BANNED_SLUGS = {
    "map-key-fixed32",
    "field-presence-implicit-override",
    "map-key-i32-to-i64",
    "map-key-bool-to-str",
    "map4-str-to-u64",
    "field-presence-explicit",
    "ed2023-legacy-required",
    "optional4-peak-hasfield",
    "optional-bytes-drop",
    "optional-enum-quench-drop",
    "optional-msg-tuyere-drop",
}
BANNED_NEEDLES = (
    "map-key-fixed32",
    "field-presence-implicit",
    "map-key-i32-to-i64",
    "map-key-bool-to-str",
    "map4-str-to-u64",
    "field-presence-explicit",
    "legacy-required",
    "optional4-peak",
    "optional-bytes-drop",
    "optional-enum-quench",
    "optional-msg-tuyere",
)


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, name: str, args: dict, obs: str) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise ValueError(f"bad decision_basis prefix: {basis!r}")
    return {"n": n, "decision_basis": basis, "tool_call": {"name": name, "args": args}, "observation": obs}


def bash(n: int, basis: str, cmd: str, obs: str) -> dict:
    return step(n, basis, "bash", {"command": cmd}, obs)


def read(n: int, basis: str, path: str, obs: str) -> dict:
    return step(n, basis, "read", {"path": path}, obs)


def grep(n: int, basis: str, path: str, pattern: str, obs: str) -> dict:
    return step(n, basis, "grep", {"path": path, "pattern": pattern}, obs)


def edit(n: int, basis: str, path: str, old: str, new: str, obs: str) -> dict:
    return step(n, basis, "edit", {"path": path, "old": old, "new": new}, obs)


def write_tool(n: int, basis: str, path: str, contents: str, obs: str) -> dict:
    return step(n, basis, "write", {"path": path, "contents": contents}, obs)


def proto_text(p: dict, decl: str) -> str:
    imports = "".join(f'import "{imp}";\n' for imp in p.get("imports") or ())
    file_opts = p.get("file_opts") or ""
    extra = p.get("extra_msgs") or ""
    if file_opts and not file_opts.endswith("\n"):
        file_opts += "\n"
    if extra and not extra.endswith("\n"):
        extra += "\n"
    return (
        f"{p['syntax']}\npackage {p['short']}.v1;\n{imports}{file_opts}{extra}"
        f"message Heat {{ string id = 1; {decl} }}\n"
        f"service S {{ rpc Put(Heat) returns (Heat); }}\n"
    )


def guard_plant(spec: dict) -> None:
    slug = spec["slug"]
    if slug in BANNED_SLUGS:
        raise ValueError(f"banned slug {slug!r}")
    identity = " ".join(str(spec.get(k, "")) for k in ("slug", "short", "decl_old", "decl_new", "buf_rule")).lower()
    for needle in BANNED_NEEDLES:
        if needle in identity:
            raise ValueError(f"banned needle {needle!r} in {identity!r}")


def plant(**kw: object) -> dict:
    for key in (
        "slug", "short", "decl_old", "decl_new", "syntax", "buf_rule",
        "wire_old", "wire_new", "freeze", "ticket", "lang", "vs", "avoid",
        "json_name", "debug", "compat", "grep_pat", "goal_bit",
    ):
        if key not in kw:
            raise ValueError(f"plant missing {key}")
    kw.setdefault("imports", ())
    kw.setdefault("file_opts", "")
    kw.setdefault("extra_msgs", "")
    kw.setdefault("dead_old", "")
    kw.setdefault("dead_new", "")
    kw.setdefault("dead_obs", "")
    kw.setdefault("dead_desc", "")
    return kw


def proto_path(p: dict) -> str:
    return f"proto/{p['short']}.proto"


def handler_path(p: dict) -> str:
    return f"src/{p['short']}/h.go"


def success_episode(round_n: int, p: dict) -> dict:
    guard_plant(p)
    eid = f"pbc-r{round_n}-{p['slug']}-{round_n}a"
    proto = proto_path(p)
    handler = handler_path(p)
    old_src = proto_text(p, p["decl_old"])
    new_src = proto_text(p, p["decl_new"])
    steps = [
        bash(1, f"Plan: locate {proto}, {p['goal_bit']}, handler, and goldens before editing.", f"ls -la proto src/{p['short']} clients tests buf.yaml Makefile | sed -n '1,48p'", f"{proto}  {handler}  tests/wire/test_{p['short']}.go  tests/contract/test_json.py  buf.yaml"),
        grep(2, f"Observation: {p['short']} tree present (step 1). Grep {p['grep_pat']}.", ".", p["grep_pat"], f"{proto}: {p['decl_new']}  // was {p['decl_old']}\n{p['freeze']}"),
        read(3, f"Observation: {p['wire_old']} vs {p['wire_new']} (step 2). Read {proto}.", proto, new_src),
        bash(4, f"Observation: {p['buf_rule']} candidate, not {p['avoid']} (step 3). Diff versus origin/main.", f"git diff origin/main -- {proto} | sed -n '1,60p'", f"-  {p['decl_old']}\n+  {p['decl_new']}"),
        bash(5, f"Observation: WIRE {p['wire_old']} vs {p['wire_new']} (step 4). Run buf breaking versus main.", "buf breaking proto --against '.git#branch=origin/main,subdir=proto' 2>&1 | tail -n 20", f"{proto}: {p['decl_old']} → {p['decl_new']}.\nFailure: 1 breaking change ({p['buf_rule']}). {p['wire_old']} vs {p['wire_new']}. Distinct from {p['vs']}."),
        bash(6, f"Observation: buf flags {p['buf_rule']} (step 5). Run protojson contract tests CI gates on.", "pytest tests/contract/test_json.py -q --tb=short 2>&1 | tail -n 16", f"test_{p['short']}_json PASSED\ntest_extra_{p['debug']}_ignored PASSED\n2 passed"),
        read(7, f"Observation: JSON suite green on {p['short']} (step 6). Read the unknown-field test.", "tests/contract/test_json.py", f"def test_extra_{p['debug']}_ignored():\n    Parse(..., ignore_unknown_fields=True)\n"),
        bash(8, f"Observation: IgnoreUnknown is the false-green (step 7). Run the {p['short']} runtime/wire probe.", f"go test ./tests/wire -run {p['short'].title()} -count=1 -v 2>&1 | tail -n 16", f"{p['freeze']}\n--- FAIL Test{p['short'].title()}"),
        bash(9, f"Observation: {p['wire_old']} vs {p['wire_new']} (step 8). Dump the golden payload.", f'''python3 -c "from pathlib import Path; print(Path('tests/wire/golden_{p['short']}.bin').read_bytes().hex() if Path('tests/wire/golden_{p['short']}.bin').exists() else open('tests/fixtures/{p['short']}.txt').read())"''', f"{p['freeze']}"),
        edit(10, f"Observation: mismatch (step 9). Dead-end — json_name {p['json_name']} as a wire/type substitute.", proto, p["decl_new"], p["decl_new"].rstrip(";") + f' [json_name = "{p["json_name"]}"];', f"json_name does not restore {p['wire_old']}. Freeze still {p['wire_new']}."),
        bash(11, f"Observation: {p['short']} dead-end patch applied (step 10). Re-run buf + runtime + protojson.", "buf breaking proto --against '.git#branch=origin/main,subdir=proto'; go test ./tests/wire -count=1 -v 2>&1 | tail -n 8", f"buf: {p['buf_rule']} still {p['decl_new']}\n{p['wire_old']} freeze frames"),
        write_tool(12, f"Reflection: revert the {p['short']} dead-end (steps 10-11). Restore {p['decl_old']} Dual-read leftover {p['wire_new']}.", proto, old_src, f"{p['decl_old']} restored"),
        bash(13, f"Observation: {p['short']} schema restored (step 12). buf versus main.", "buf breaking proto --against '.git#branch=origin/main,subdir=proto' 2>&1 | tail -n 12", "ERR: none\n0 breaking changes."),
        bash(14, f"Observation: buf 0 ERR on {p['short']} (step 13). Regen and inspect descriptors.", f"make proto && rg -n '{p['short']}' {proto} {handler.replace('h.go', 'gen/' + p['short'] + '.pb.go')} | head", p["decl_old"]),
        read(15, f"Observation: {p['decl_old']} restored (step 14). Read the handler that still assumes the break.", handler, f"// handler still assumes {p['goal_bit']}\n"),
        write_tool(16, f"Observation: handler still on the break (step 15). Compat shim for freeze frames without treating the break as success.", f"src/{p['short']}/compat.go", f"package {p['short']}\n// {p['compat']}\n", f"compat shim for {p['short']}"),
        edit(17, f"Observation: {p['short']} shim written (step 16). Wire it into the handler.", handler, p["decl_new"], p["decl_old"], "compat wired"),
        bash(18, f"Observation: handler wired for {p['short']} (step 17). Re-run wire, shim, protojson.", f"go test ./tests/wire ./src/{p['short']} -count=1 2>&1 | tail -n 10; pytest tests/contract -q", "wire PASS\npytest 2 passed"),
        bash(19, f"Observation: {p['short']} recovered (step 18). Final buf + go + pytest.", "go test ./... -count=1 2>&1 | tail -n 8; pytest tests/contract -q; buf breaking proto --against '.git#branch=origin/main,subdir=proto'", "go: ok (8 passed)\npytest: 4 passed\nbuf breaking: 0"),
        bash(20, f"Observation: 8 go + 4 py + buf 0 (step 19). Confirm residual {p['debug']} is still a false-green.", f"rg -n '{p['grep_pat'].split('|')[0]}' {proto}", p["decl_old"]),
    ]
    if not 18 <= len(steps) <= 22:
        raise ValueError(f"{eid} bad step count {len(steps)}")
    return {
        "id": eid,
        "goal": f"{p['short']} {p['goal_bit']}. Restore {p['decl_old']} dual-read {p['wire_new']}. Distinct from {p['vs']}.",
        "plan": f"Prove {p['buf_rule']}, reject json_name substitute, restore {p['decl_old']}, buf 0.",
        "steps": steps,
        "outcome": f"Restored {p['decl_old']} json_name was a dead-end. protojson {p['debug']} was the false-green. buf 0. Residual: {p['wire_new']} leftover dual-read.",
        "reward": {"success": True, "tests_passed": 12, "buf_breaking": 0, "cost_steps": len(steps)},
        "meta": {"factory": FACTORY, "round": round_n, "generator": GENERATOR},
    }


def handoff_episode(round_n: int, p: dict) -> dict:
    guard_plant(p)
    eid = f"pbc-r{round_n}-{p['slug']}-{round_n}b"
    proto = proto_path(p)
    ticket = f"tickets/{p['ticket']}.md"
    old_src = proto_text(p, p["decl_old"])
    new_src = proto_text(p, p["decl_new"])
    dead_old = p["dead_old"] or p["decl_new"]
    dead_new = p["dead_new"] or p["decl_new"].rstrip(";") + f' [json_name = "{p["json_name"]}"];'
    dead_obs = p["dead_obs"] or f"json_name does not restore {p['wire_old']}; freeze still {p['wire_new']}"
    dead_desc = p["dead_desc"] or f"json_name {p['json_name']} as a type substitute"
    freeze_py = f"clients/{p['lang'].lower()}/test_{p['short']}.py"
    steps = [
        bash(1, f"Plan: locate {proto}, {p['goal_bit']}, {p['lang']} freeze, and {p['ticket']}.md.", f"ls -la proto src/{p['short']} clients tests tickets buf.yaml | sed -n '1,48p'", f"{proto}  src/{p['short']}/h.go  clients/ freeze {ticket} tests/contract/test_json.py buf.yaml"),
        grep(2, f"Observation: freeze client + ticket present for {p['short']} (step 1). Grep {p['grep_pat']}.", ".", p["grep_pat"], f"{proto}: {p['decl_new']}  // {p['decl_old']}\n{p['freeze']}\n{ticket}: Status: OPEN"),
        read(3, f"Observation: {p['freeze']} (step 2). Read {proto}.", proto, new_src),
        bash(4, f"Observation: {p['buf_rule']}, not {p['avoid']} (step 3). Diff versus origin/main.", f"git diff origin/main -- {proto} | sed -n '1,60p'", f"-    {p['decl_old']}\n+    {p['decl_new']}"),
        bash(5, f"Observation: WIRE {p['wire_old']} vs {p['wire_new']}; freeze still on the pre-break contract (step 4). buf breaking.", "buf breaking proto --against '.git#branch=origin/main,subdir=proto' 2>&1 | tail -n 20", f"{proto}: {p['decl_old']} → {p['decl_new']}.\nFailure: 1 breaking change ({p['buf_rule']}). Distinct from {p['vs']}."),
        bash(6, f"Observation: buf {p['buf_rule']} (step 5). protojson contract tests.", "pytest tests/contract/test_json.py -q --tb=short 2>&1 | tail -n 16", f"test_{p['short']}_json PASSED\ntest_extra_{p['debug']}_ignored PASSED\n2 passed"),
        bash(7, f"Observation: JSON green on {p['short']} (step 6). Run the {p['lang']} freeze suite.", f"pytest {freeze_py} -q --tb=short 2>&1 | tail -n 16", f"{p['freeze']}\nFAILED"),
        read(8, f"Observation: freeze still implements the pre-break {p['short']} contract (step 7). Read {p['ticket']}.md.", ticket, f"# {p['ticket']} freeze\nStatus: OPEN\n{p['goal_bit']}. Do not substitute.\n"),
        edit(9, f"Observation: ticket says restore or dual-read, do not fake a client regen (step 8). Dead-end — {dead_desc}.", proto, dead_old, dead_new, dead_obs),
        bash(10, f"Observation: {p['short']} dead-end (step 9). Re-run freeze + buf.", f"buf breaking proto --against '.git#branch=origin/main,subdir=proto'; pytest {freeze_py} -q --tb=short 2>&1 | tail -n 16", f"buf: {p['buf_rule']} still broken\n{p['lang']} freeze fail"),
        write_tool(11, f"Reflection: revert dead-end (steps 9-10). Restore {p['decl_old']}.", proto, old_src, f"{p['decl_old']} restored"),
        bash(12, f"Observation: {p['short']} schema restored (step 11). buf versus main.", "buf breaking proto --against '.git#branch=origin/main,subdir=proto' 2>&1 | tail -n 12", "ERR: none\n0 breaking changes."),
        bash(13, f"Observation: buf 0 (step 12). Regen server stubs; {p['lang']} freeze is not regenerated.", f"make proto && rg -n '{p['short']}' {proto} | head", p["decl_old"]),
        bash(14, f"Observation: {p['decl_old']} restored (step 13). Freeze suite + leftover break fixture.", f"pytest {freeze_py} -q --tb=short 2>&1 | tail -n 16; pytest tests/contract -q", f"restore PASS\nFAILED testBroken{p['short'].title()} — HEAD asserted break\npytest 2 passed"),
        edit(15, f"Observation: leftover {p['short']} fixture after restore (step 14). Mark xfail against {p['ticket']}.md.", freeze_py, f"def test_broken_{p['short']}():", f'@pytest.mark.skip(reason="{p["ticket"]}")\ndef test_broken_{p["short"]}():', "skipped break-field fixture"),
        bash(16, f"Observation: xfail in place for {p['short']} (step 15). Final buf + freeze + protojson.", f"buf breaking proto --against '.git#branch=origin/main,subdir=proto'; pytest {freeze_py} -q --tb=short 2>&1 | tail -n 16; pytest tests/contract -q", f"buf 0\n{p['lang']}: 1 passed, 1 skipped\npytest: 2 passed\n{p['ticket']} OPEN"),
        bash(17, f"Observation: freeze still on the pre-break {p['short']} shape (step 16). Confirm restore.", f"rg -n '{p['grep_pat'].split('|')[0]}' {proto}", p["decl_old"]),
        read(18, f"Observation: restored {p['goal_bit']} (step 17). Residual {p['debug']}.", "tests/contract/test_json.py", f"def test_extra_{p['debug']}_ignored():\n    Parse(..., ignore_unknown_fields=True)\n"),
        bash(19, f"Observation: false-green leftover on {p['short']} (step 18). Ticket still OPEN.", f"rg -n 'Status' {ticket}", "Status: OPEN"),
        bash(20, f"Observation: not a completed {p['lang']} migration (step 19). Mechanic check.", f"rg -n '{p['grep_pat'].split('|')[0]}' {proto}", p["goal_bit"]),
        bash(21, f"Observation: {p['ticket']}.md remains OPEN (step 20). Stop.", f"sed -n '1,12p' {ticket}", "Status: OPEN"),
    ]
    if not 18 <= len(steps) <= 22:
        raise ValueError(f"{eid} bad step count {len(steps)}")
    return {
        "id": eid,
        "goal": f"{p['short']} {p['goal_bit']}. Restore {p['decl_old']}; leave {p['ticket']} open. Distinct from {p['vs']}.",
        "plan": f"Prove {p['buf_rule']}, reject {dead_desc}, restore {p['decl_old']}, xfail freeze.",
        "steps": steps,
        "outcome": f"Restored {p['decl_old']} {dead_desc.split(' as ')[0]} was a dead-end. {p['lang']} freeze still has a break fixture — {p['ticket']} OPEN, 1 skipped. Extra {p['debug']} still false-green. WIRE buf 0. Not a completed client migration.",
        "reward": {"success": False, "tests_passed": 7, "xfailed": 1, "buf_breaking": 0, "cost_steps": len(steps)},
        "meta": {"factory": FACTORY, "round": round_n, "generator": GENERATOR},
    }


def notes_for(
    round_n: int,
    suc: dict,
    xf: dict,
    srec: dict,
    xrec: dict,
    *,
    catalog_first: int,
    extra_ban: str = "",
    footer: str = "",
) -> str:
    cov = 79 + ((round_n - catalog_first) % 6)
    ban = (
        "- Ban check: not r700 map-key-fixed32 / field-presence-implicit-override, not r691 "
        "map-key-i32-to-i64, not r687 map-key-bool-to-str, not r632 map4-str-to-u64, not r44 "
        "field-presence-explicit, not r635 ed2023-legacy-required, not r629 optional drop"
        f"{extra_ban}.\n"
    )
    return (
        f"# NOTES-r{round_n} proto-breaking-change-factory\n\n"
        f"Novel coverage: {cov}%\n\n"
        f"- Episodes: 2 (quota). Step counts: {suc['slug']} {srec['reward']['cost_steps']}, "
        f"{xf['slug']} {xrec['reward']['cost_steps']} (18–22 density).\n"
        f"- Distinct from {suc['vs']}: this success is {suc['goal_bit']}. Xfail is "
        f"{xf['goal_bit']} — not {xf['avoid']}.\n"
        f"- Debug loops: json_name {suc['json_name']} as a wire/type substitute (10–11); "
        f"{xf['dead_desc'] or ('json_name ' + xf['json_name'] + ' as a type substitute')} (9–10).\n"
        f"- Success `{srec['id']}` and freeze-client partial `{xrec['id']}`.\n"
        f"- False-green: protojson IgnoreUnknown / extra {suc['debug']} {xf['debug']} keys; "
        f"OpenAPI additionalProperties.\n"
        f"- Residual: leftover {suc['wire_new']} still dual-read; {xf['ticket']} freeze still "
        f"pre-break.\n"
        f"{ban}{footer}"
    )


def _const(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    raise ValueError("not a constant")


def _call_slug(node: ast.Call) -> str | None:
    func = node.func
    if not isinstance(func, ast.Name) or func.id not in {"plant", "ty"}:
        return None
    try:
        for keyword in node.keywords:
            if keyword.arg == "slug":
                return str(_const(keyword.value))
        if node.args:
            return str(_const(node.args[0]))
    except ValueError:
        return None
    return None


def first_slugs_from_source(text: str) -> tuple[str, ...]:
    """Return plant()/ty() slugs in source order. Parse only; never exec."""

    tree = ast.parse(text)
    slugs: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            slug = _call_slug(node)
            if slug is not None:
                slugs.append(slug)
    if slugs:
        return tuple(slugs)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "RAW" for t in node.targets):
            continue
        raw = _const(node.value)
        if not isinstance(raw, str):
            continue
        for line in raw.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "|" in line:
                return (line.split("|", 1)[0],)
    raise ValueError("no plant()/ty()/RAW slugs in source")


def extract_tree(source_root: Path) -> dict[str, Any]:
    """AST-extract first slugs from ``pbc-mill*.py`` text. Never execs or copies."""

    root = source_root.resolve()
    rows = []
    for path in sorted(root.rglob("pbc-mill-*.py")):
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        slugs = first_slugs_from_source(text)
        rows.append({"source": path.name, "first_slug": slugs[0], "slug_count": len(slugs)})
    return {
        "extract": {"exec": False, "method": "ast.parse"},
        "rows": rows,
        "vendor_prefix": VENDOR_PREFIX,
    }


__all__ = [
    "BANNED_NEEDLES",
    "BANNED_SLUGS",
    "extract_tree",
    "first_slugs_from_source",
    "handoff_episode",
    "notes_for",
    "plant",
    "success_episode",
]

_contract.bind_import_twin(__name__)
