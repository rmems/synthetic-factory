#!/usr/bin/env python3
"""Build one browser-tool-use pair from an AST-extracted ``brw-mill-r193`` plant.

The success/fail tool sequences are the designed trajectories from the
AST-extracted mill: leftover CSS first, then new agent-breakers, 13–16 steps,
with a fail/handoff that is never HTTP 409. This module does not publish a
raw round and does not execute leftover mill scripts.
"""

from __future__ import annotations

import json
from typing import Any

from . import catalog as cat
from ._contract import (
    BANNED_CSS,
    BANNED_HOSTS,
    CATALOG_FIRST,
    FACTORY,
    GEN,
    BrwError,
    require_round,
)
from .catalog import PAIRS

__all__ = [
    "build_fail",
    "build_success",
    "clip",
    "generate_window",
    "meta",
    "notes_for",
    "pair_for_round",
    "pair_records",
    "rec",
    "site",
    "st",
    "validate_pair",
]


def clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def st(n: int, basis: str, name: str, args: dict, obs: str, reflection: str | None = None) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise BrwError(f"bad decision_basis prefix: {basis!r}")
    if len(basis) > 240:
        raise BrwError(f"decision_basis too long ({len(basis)}): {basis}")
    step = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if reflection:
        step["reflection"] = reflection
    return step


def rec(eid: str, goal: str, plan: str, steps: list, outcome: str, reward: dict, meta: dict) -> dict:
    if not 13 <= len(steps) <= 16:
        raise BrwError(f"{eid}: need 13–16 steps, got {len(steps)}")
    for i, step in enumerate(steps, 1):
        if step["n"] != i:
            raise BrwError(f"{eid}: step n gap at {i}")
        blob = json.dumps(step)
        for key in ("thought", "chain_of_thought", "scratch", "inner_monologue"):
            if f'"{key}"' in blob:
                raise BrwError(f"{eid}: banned key {key}")
    return {
        "id": eid,
        "goal": goal,
        "plan": plan,
        "steps": steps,
        "outcome": outcome,
        "reward": reward,
        "meta": meta,
    }


def site(sub: str, host: str) -> str:
    if host in BANNED_HOSTS:
        raise BrwError(f"banned host: {host}")
    return f"{sub}.{host}.example"


def meta(n: int, seed: str, host_site: str) -> dict:
    return {
        "factory": FACTORY,
        "round": n,
        "generator": GEN,
        "kind": "episode",
        "designed": True,
        "seed": seed,
        "site": host_site,
    }


def _nav_obs(p: dict, host: str, extra: str) -> str:
    sub = p["sub"]
    return (
        f"status=200 title='{host.capitalize()} — {p['title']}'\n"
        f"[a11y]\n"
        f"- generic #{sub} {p['css_short']}={p['from_v']}\n"
        f"  - article {p['item']} ref={p['ref']}\n"
        f"  - article {p['item_b']} ref={p['ref_b']}\n"
        f"- button '{p['trig']}' ref={p['trig_ref']}\n"
        f"- button '{p['verb']}' ref={p['act_ref']} disabled\n"
        f"link rel='service' href='https://api.{host}.example/openapi.json'\n"
        f"link rel='css' href='https://css.{host}.example/gate'\n"
        f"{extra}"
    )


def _eval_expr(p: dict) -> str:
    return (
        "JSON.stringify({"
        f"{p['js_prop'][:6]}:getComputedStyle(document.querySelector('#{p['sub']}'))"
        f".{p['js_prop']},"
        f"x:document.querySelector('[data-ref={p['ref']}]').getBoundingClientRect().x,"
        f"y:document.querySelector('[data-ref={p['ref']}]').getBoundingClientRect().y"
        "})"
    )


def build_success(n: int, p: dict) -> dict:
    host = p["ok_host"]
    s = site(p["sub"], host)
    css_s = site("css", host)
    api = site("api", host)
    keep = p["ok_id"]
    shape = p["shape"]
    x0, x1, y = p["x0"], p["x1"], p["y"]
    y1 = p.get("y1", y)
    vis_x = p.get("visual_x", x1)

    if shape == "shift":
        steps = [
            st(1, f"Plan: open the designed {host.capitalize()} {p['noun']}s before using a pre-{p['css_short']} x.",
               "browser_navigate", {"url": f"https://{s}/keep"},
               _nav_obs(p, host, f"link rel='hint' href='https://{css_s}/shift'"),
               p["reflect"]),
            st(2, f"Observation: snapshot {p['from_v']} row.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- article '{p['item']}' ref={p['ref']}\n- article '{p['item_b']}' ref={p['ref_b']}"),
            st(3, f"Observation: measure {p['item']} before {p['css_short']}.",
               "browser_evaluate", {"expression": _eval_expr(p)},
               json.dumps({p["js_prop"][:6]: p["from_v"], "x": x0, "y": y})),
            st(4, f"Observation: GET {p['css_short']} contract.",
               "http_request", {"method": "GET", "url": f"https://{css_s}/shift", "headers": {"Accept": "application/json"}},
               f"200 {{\"from\":{p['from_v']!r},\"to\":{p['to_v']!r},\"warn\":{p['warn']!r}}}"),
            st(5, f"Observation: click {p['trig']} {p['trig_ref']}.",
               "browser_click", {"ref": p["trig_ref"]},
               f"clicked {p['trig_ref']}; {p['css_short']}={p['to_v']}; {p['item']} x {x0}→{x1}"),
            st(6, f"Observation: click stored x={x0}.",
               "browser_click", {"position": {"x": x0, "y": y}},
               f"Error: click hit {p['item_b']} (now at {x0}); {p['item']} is at {x1}"),
            st(7, f"Observation: screenshot {p['css_short']} shift.",
               "browser_screenshot", {"filename": f"findings/{host}-{p['css_short'].replace(':','-')}.png"},
               f"png: {p['item_b']} under old x; {p['item']} at {x1}"),
            st(8, f"Observation: remeasure after {p['to_v']}.",
               "browser_evaluate", {"expression": _eval_expr(p)},
               json.dumps({p["js_prop"][:6]: p["to_v"], "x": x1, "y": y1})),
            st(9, f"Observation: click {p['item']} {p['ref']}.",
               "browser_click", {"ref": p["ref"]},
               f"clicked {p['ref']}; {p['verb']} enabled"),
            st(10, f"Observation: fill {p['verb'].lower()} note.",
               "browser_fill_form", {"fields": [{"ref": p["note_ref"], "value": f"{p['item']} {host[:4]}"}]},
               f"filled {p['note_ref']}='{p['item']} {host[:4]}'"),
            st(11, f"Observation: click {p['verb']} {p['act_ref']}.",
               "browser_click", {"ref": p["act_ref"]},
               f"clicked {p['act_ref']}; POST https://{s}/ui/keep → 201 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\"}}"),
            st(12, f"Observation: GET api {p['verb'].lower()}.",
               "http_request", {"method": "GET", "url": f"https://{api}/{p['verb'].lower()}s/{keep}", "headers": {"Accept": "application/json"}},
               f"200 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\",\"{p['css_short']}\":{p['to_v']!r}}}"),
            st(13, f"Observation: snapshot kept {keep}.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- status 'Kept {keep}' ref=s1"),
            st(14, f"Observation: {keep}. Write findings.",
               "write", {"path": f"findings/{host}-{p['item']}.json", "contents": json.dumps({"keep_id": keep, "item": p["item"], "source": f"ref_after_{p['css_short']}"}) + "\n"},
               f"wrote findings/{host}-{p['item']}.json"),
        ]
        outcome = f"{p['css']} moved {p['item']}. Stored x hit {p['item_b']}. Clicked {p['ref']}. POST: {keep}."
    elif shape == "visual":
        steps = [
            st(1, f"Plan: open the designed {host.capitalize()} {p['noun']}s before treating painted pixels as the hit box.",
               "browser_navigate", {"url": f"https://{s}/keep"},
               _nav_obs(p, host, f"link rel='paint' href='https://{css_s}/paint'"),
               p["reflect"]),
            st(2, f"Observation: snapshot {p['noun']}s and {p['css_short']}.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- article '{p['item']}' ref={p['ref']}\n- article '{p['item_b']}' ref={p['ref_b']}\n- button '{p['verb']}' ref={p['act_ref']}"),
            st(3, f"Observation: evaluate {p['css_short']} vs box.",
               "browser_evaluate", {"expression": _eval_expr(p)},
               json.dumps({p["js_prop"][:6]: p["to_v"], "x": x0, "y": y, "width": 72})),
            st(4, f"Observation: GET paint-vs-hit contract.",
               "http_request", {"method": "GET", "url": f"https://{css_s}/paint", "headers": {"Accept": "application/json"}},
               f"200 {{\"css\":{p['css']!r},\"warn\":{p['warn']!r}}}"),
            st(5, f"Observation: click {p['trig']} {p['trig_ref']}.",
               "browser_click", {"ref": p["trig_ref"]},
               f"clicked {p['trig_ref']}; {p['css_short']} live; paint ≠ box"),
            st(6, f"Observation: click visual blob at x={vis_x}.",
               "browser_click", {"position": {"x": vis_x, "y": y}},
               f"Error: click hit {p['item']} box at {x0} (paint was at {vis_x}); not {p['item_b']}"),
            st(7, f"Observation: screenshot paint vs used box.",
               "browser_screenshot", {"filename": f"findings/{host}-paint.png"},
               f"png: painted face offset; a11y still {p['item']} at {x0}"),
            st(8, f"Observation: remeasure unfiltered/unmasked box.",
               "browser_evaluate", {"expression": _eval_expr(p)},
               json.dumps({p["js_prop"][:6]: p["to_v"], "x": x0, "y": y})),
            st(9, f"Observation: click {p['item']} {p['ref']} not the blob.",
               "browser_click", {"ref": p["ref"]},
               f"clicked {p['ref']}; {p['verb']} enabled"),
            st(10, f"Observation: fill {p['verb'].lower()} note.",
               "browser_fill_form", {"fields": [{"ref": p["note_ref"], "value": f"{p['item']} {host[:4]}"}]},
               f"filled {p['note_ref']}='{p['item']} {host[:4]}'"),
            st(11, f"Observation: click {p['verb']} {p['act_ref']}.",
               "browser_click", {"ref": p["act_ref"]},
               f"clicked {p['act_ref']}; POST https://{s}/ui/keep → 201 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\"}}"),
            st(12, f"Observation: GET api receipt.",
               "http_request", {"method": "GET", "url": f"https://{api}/{p['verb'].lower()}s/{keep}", "headers": {"Accept": "application/json"}},
               f"200 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\",\"via\":\"a11y_ref\"}}"),
            st(13, f"Observation: snapshot {keep}.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- status 'Kept {keep}' ref=s1"),
            st(14, f"Observation: {keep}. Write findings.",
               "write", {"path": f"findings/{host}-{p['item']}.json", "contents": json.dumps({"keep_id": keep, "item": p["item"], "source": f"ref_not_paint_{p['css_short']}"}) + "\n"},
               f"wrote findings/{host}-{p['item']}.json"),
        ]
        if p["css_short"] == "backface-visibility":
            # Trig is "Show face" — do not flip before proving the hidden backface miss.
            steps[4] = st(
                5,
                f"Observation: click {p['item']} {p['ref']} while rotateY=180.",
                "browser_click",
                {"ref": p["ref"]},
                f"Error: locator.click: {p['item']} backface-hidden; a11y node exists, paint is the back",
            )
            steps[5] = st(
                6,
                "Observation: click stored face x (empty paint).",
                "browser_click",
                {"position": {"x": vis_x, "y": y}},
                f"Error: click hit empty transformed face; {p['item']} backface-visibility=hidden",
            )
            steps.insert(
                7,
                st(
                    8,
                    f"Observation: click {p['trig']} {p['trig_ref']} to rotateY(0).",
                    "browser_click",
                    {"ref": p["trig_ref"]},
                    "clicked e4; rotateY=0; face visible; Flip enabled",
                ),
            )
            for i, step in enumerate(steps, 1):
                step["n"] = i
            if not (13 <= len(steps) <= 16):
                raise BrwError(f"visual/backface step count {len(steps)}")
        outcome = f"{p['css']} split paint from the used box. Clicked {p['ref']}. POST: {keep}."
    elif shape == "overlay":
        steps = [
            st(1, f"Plan: open the designed {host.capitalize()} {p['noun']}s before clicking through {p['css_short']}.",
               "browser_navigate", {"url": f"https://{s}/keep"},
               _nav_obs(p, host, f"link rel='layer' href='https://{css_s}/layer'"),
               p["reflect"]),
            st(2, f"Observation: snapshot overlay covering {p['verb']}.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- article '{p['item']}' ref={p['ref']}\n- generic overlay ref=ov1\n- button '{p['verb']}' ref={p['act_ref']}\n- button '{p['trig']}' ref={p['trig_ref']}"),
            st(3, f"Observation: evaluate overlay vs {p['verb']} box.",
               "browser_evaluate", {"expression": _eval_expr(p)},
               json.dumps({p["js_prop"][:6]: p["from_v"], "x": x0, "y": y, "overlay": True})),
            st(4, f"Observation: GET {p['css_short']} contract.",
               "http_request", {"method": "GET", "url": f"https://{css_s}/layer", "headers": {"Accept": "application/json"}},
               f"200 {{\"css\":{p['css']!r},\"warn\":{p['warn']!r}}}"),
            st(5, f"Observation: click {p['verb']} px through the overlay.",
               "browser_click", {"position": {"x": x0, "y": y}},
               f"Error: click hit overlay ({p['css_short']}); {p['verb']} not received"),
            st(6, f"Observation: screenshot overlay capture.",
               "browser_screenshot", {"filename": f"findings/{host}-overlay.png"},
               f"png: {p['css_short']} covering {p['verb']}"),
            st(7, f"Observation: click {p['trig']} {p['trig_ref']}.",
               "browser_click", {"ref": p["trig_ref"]},
               f"clicked {p['trig_ref']}; overlay cleared or stage scrolled; {p['verb']} free"),
            st(8, f"Observation: remeasure after overlay gone.",
               "browser_evaluate", {"expression": _eval_expr(p)},
               json.dumps({p["js_prop"][:6]: p["to_v"], "x": x1, "y": y1})),
            st(9, f"Observation: click {p['item']} {p['ref']}.",
               "browser_click", {"ref": p["ref"]},
               f"clicked {p['ref']}; {p['verb']} enabled"),
            st(10, f"Observation: fill {p['verb'].lower()} note.",
               "browser_fill_form", {"fields": [{"ref": p["note_ref"], "value": f"{p['item']} {host[:4]}"}]},
               f"filled {p['note_ref']}='{p['item']} {host[:4]}'"),
            st(11, f"Observation: click {p['verb']} {p['act_ref']}.",
               "browser_click", {"ref": p["act_ref"]},
               f"clicked {p['act_ref']}; POST https://{s}/ui/keep → 201 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\"}}"),
            st(12, f"Observation: GET api receipt.",
               "http_request", {"method": "GET", "url": f"https://{api}/{p['verb'].lower()}s/{keep}", "headers": {"Accept": "application/json"}},
               f"200 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\",\"overlay\":\"cleared\"}}"),
            st(13, f"Observation: snapshot {keep}.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- status 'Kept {keep}' ref=s1"),
            st(14, f"Observation: {keep}. Write findings.",
               "write", {"path": f"findings/{host}-{p['item']}.json", "contents": json.dumps({"keep_id": keep, "item": p["item"], "source": f"clear_{p['css_short']}"}) + "\n"},
               f"wrote findings/{host}-{p['item']}.json"),
        ]
        outcome = f"{p['css']} captured the click. Cleared overlay, clicked {p['ref']}. POST: {keep}."
    elif shape == "viewport":
        vpl = p.get("vp_label", "closed-chrome y")
        steps = [
            st(1, f"Plan: open the designed {host.capitalize()} {p['noun']}s before trusting a {vpl}.",
               "browser_navigate", {"url": f"https://{s}/keep"},
               _nav_obs(p, host, f"link rel='vp' href='https://{css_s}/vp'"),
               p["reflect"]),
            st(2, f"Observation: snapshot layout under {vpl}.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- article '{p['item']}' ref={p['ref']}\n- button '{p['verb']}' ref={p['act_ref']} y≈{y}"),
            st(3, f"Observation: measure {p['css_short']} before the viewport/env change.",
               "browser_evaluate", {"expression": _eval_expr(p)},
               json.dumps({p["js_prop"][:6]: p["from_v"], "x": x0, "y": y})),
            st(4, f"Observation: GET viewport/env contract.",
               "http_request", {"method": "GET", "url": f"https://{css_s}/vp", "headers": {"Accept": "application/json"}},
               f"200 {{\"css\":{p['css']!r},\"warn\":{p['warn']!r}}}"),
            st(5, f"Observation: click {p['trig']} {p['trig_ref']}.",
               "browser_click", {"ref": p["trig_ref"]},
               f"clicked {p['trig_ref']}; chrome/keyboard changed; {p['item']} y {y}→{y1}"),
            st(6, f"Observation: click stored y={y}.",
               "browser_click", {"position": {"x": x0, "y": y}},
               f"Error: click hit chrome/keyboard or {p['item_b']}; {p['item']} now at y={y1}"),
            st(7, f"Observation: screenshot after viewport change.",
               "browser_screenshot", {"filename": f"findings/{host}-vp.png"},
               f"png: {p['verb']} lifted/grown; old y is leftover chrome"),
            st(8, f"Observation: remeasure dvh/inset box.",
               "browser_evaluate", {"expression": _eval_expr(p)},
               json.dumps({p["js_prop"][:6]: p["to_v"], "x": x1, "y": y1})),
            st(9, f"Observation: click {p['item']} {p['ref']}.",
               "browser_click", {"ref": p["ref"]},
               f"clicked {p['ref']}; {p['verb']} enabled"),
            st(10, f"Observation: fill {p['verb'].lower()} note.",
               "browser_fill_form", {"fields": [{"ref": p["note_ref"], "value": f"{p['item']} {host[:4]}"}]},
               f"filled {p['note_ref']}='{p['item']} {host[:4]}'"),
            st(11, f"Observation: click {p['verb']} {p['act_ref']}.",
               "browser_click", {"ref": p["act_ref"]},
               f"clicked {p['act_ref']}; POST https://{s}/ui/keep → 201 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\"}}"),
            st(12, f"Observation: GET api receipt.",
               "http_request", {"method": "GET", "url": f"https://{api}/{p['verb'].lower()}s/{keep}", "headers": {"Accept": "application/json"}},
               f"200 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\",\"unit\":{p['to_v']!r}}}"),
            st(13, f"Observation: snapshot {keep}.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- status 'Kept {keep}' ref=s1"),
            st(14, f"Observation: {keep}. Write findings.",
               "write", {"path": f"findings/{host}-{p['item']}.json", "contents": json.dumps({"keep_id": keep, "item": p["item"], "source": f"ref_after_{p['css_short']}"}) + "\n"},
               f"wrote findings/{host}-{p['item']}.json"),
        ]
        outcome = f"{p['css']} moved the used y. Stored y missed. Clicked {p['ref']}. POST: {keep}."
    elif shape == "text":
        steps = [
            st(1, f"Plan: open the designed {host.capitalize()} {p['noun']}s before trusting OCR after {p['css_short']}.",
               "browser_navigate", {"url": f"https://{s}/keep"},
               _nav_obs(p, host, f"link rel='type' href='https://{css_s}/type'"),
               p["reflect"]),
            st(2, f"Observation: snapshot unwrapped label.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- article '{p['item']}' ref={p['ref']} name='締約 Post'\n- button '{p['verb']}' ref={p['act_ref']}"),
            st(3, f"Observation: measure wrap before auto-phrase.",
               "browser_evaluate", {"expression": _eval_expr(p)},
               json.dumps({p["js_prop"][:6]: p["from_v"], "lines": 1, "x": x0, "y": y})),
            st(4, f"Observation: GET phrase-wrap contract.",
               "http_request", {"method": "GET", "url": f"https://{css_s}/type", "headers": {"Accept": "application/json"}},
               f"200 {{\"css\":{p['css']!r},\"warn\":{p['warn']!r}}}"),
            st(5, f"Observation: click {p['trig']} {p['trig_ref']}.",
               "browser_click", {"ref": p["trig_ref"]},
               f"clicked {p['trig_ref']}; {p['css_short']}={p['to_v']}; label now 2 lines covering {p['verb']}"),
            st(6, f"Observation: OCR the wrapped fragment.",
               "browser_evaluate", {"expression": "document.querySelector('[data-ref=" + p['ref'] + "]').innerText"},
               "締\\n約 Post"),
            st(7, f"Observation: screenshot phrase wrap over {p['verb']}.",
               "browser_screenshot", {"filename": f"findings/{host}-phrase.png"},
               f"png: second line covers {p['verb']}; glyph '締' is not the token"),
            st(8, f"Observation: click {p['item']} {p['ref']} not the fragment.",
               "browser_click", {"ref": p["ref"]},
               f"clicked {p['ref']}; {p['verb']} enabled"),
            st(9, f"Observation: fill {p['verb'].lower()} with full token.",
               "browser_fill_form", {"fields": [{"ref": p["note_ref"], "value": p["item"]}]},
               f"filled {p['note_ref']}='{p['item']}'"),
            st(10, f"Observation: click {p['verb']} {p['act_ref']} by ref under wrap.",
               "browser_click", {"ref": p["act_ref"]},
               f"clicked {p['act_ref']}; POST https://{s}/ui/keep → 201 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\"}}"),
            st(11, f"Observation: GET api receipt.",
               "http_request", {"method": "GET", "url": f"https://{api}/{p['verb'].lower()}s/{keep}", "headers": {"Accept": "application/json"}},
               f"200 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\",\"token\":\"full\"}}"),
            st(12, f"Observation: GET OpenAPI 415 clause.",
               "http_request", {"method": "GET", "url": f"https://{api}/openapi.json", "headers": {"Accept": "application/json"}},
               f"200\nPOST /{p['sub']} 415 phrase_ocr if token is a wrap fragment"),
            st(13, f"Observation: snapshot {keep}.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- status 'Kept {keep}' ref=s1"),
            st(14, f"Observation: {keep}. Write findings.",
               "write", {"path": f"findings/{host}-{p['item']}.json", "contents": json.dumps({"keep_id": keep, "item": p["item"], "source": "ref_not_ocr_fragment"}) + "\n"},
               f"wrote findings/{host}-{p['item']}.json"),
        ]
        outcome = f"{p['css']} wrapped the label. OCR fragment ignored. Clicked {p['act_ref']}. POST: {keep}."
    else:  # box
        steps = [
            st(1, f"Plan: open the designed {host.capitalize()} {p['noun']}s before clicking a vanished or cloned box.",
               "browser_navigate", {"url": f"https://{s}/keep"},
               _nav_obs(p, host, f"link rel='box' href='https://{css_s}/box'"),
               p["reflect"]),
            st(2, f"Observation: snapshot principal box.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- article '{p['item']}' ref={p['ref']}\n- generic parent ref=par\n- button '{p['verb']}' ref={p['act_ref']}"),
            st(3, f"Observation: measure box before {p['css_short']}.",
               "browser_evaluate", {"expression": _eval_expr(p)},
               json.dumps({p["js_prop"][:6]: p["from_v"], "x": x0, "y": y, "w": 72, "h": 40})),
            st(4, f"Observation: GET box contract.",
               "http_request", {"method": "GET", "url": f"https://{css_s}/box", "headers": {"Accept": "application/json"}},
               f"200 {{\"css\":{p['css']!r},\"warn\":{p['warn']!r}}}"),
            st(5, f"Observation: click {p['trig']} {p['trig_ref']}.",
               "browser_click", {"ref": p["trig_ref"]},
               f"clicked {p['trig_ref']}; {p['css_short']}={p['to_v']}; principal box changed"),
            st(6, f"Observation: click old parent/lobe x={x0}.",
               "browser_click", {"position": {"x": x0 if p['css_short'] != 'overflow-clip-margin' else x0 + 32, "y": y if p['css_short'] != 'box-decoration-break' else y + 34}},
               f"Error: {p['css_short']} — empty parent, cloned fragment, or leaked lobe; not {p['item']} hit"),
            st(7, f"Observation: screenshot box change.",
               "browser_screenshot", {"filename": f"findings/{host}-box.png"},
               f"png: {p['css_short']} altered the painted box; child/ref still {p['item']}"),
            st(8, f"Observation: remeasure used child box.",
               "browser_evaluate", {"expression": _eval_expr(p)},
               json.dumps({p["js_prop"][:6]: p["to_v"], "x": x1, "y": y1, "w": 0 if p["css_short"] == "display:contents" else 72})),
            st(9, f"Observation: click child {p['item']} {p['ref']}.",
               "browser_click", {"ref": p["ref"]},
               f"clicked {p['ref']}; {p['verb']} enabled"),
            st(10, f"Observation: fill {p['verb'].lower()} note.",
               "browser_fill_form", {"fields": [{"ref": p["note_ref"], "value": f"{p['item']} {host[:4]}"}]},
               f"filled {p['note_ref']}='{p['item']} {host[:4]}'"),
            st(11, f"Observation: click {p['verb']} {p['act_ref']}.",
               "browser_click", {"ref": p["act_ref"]},
               f"clicked {p['act_ref']}; POST https://{s}/ui/keep → 201 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\"}}"),
            st(12, f"Observation: GET api receipt.",
               "http_request", {"method": "GET", "url": f"https://{api}/{p['verb'].lower()}s/{keep}", "headers": {"Accept": "application/json"}},
               f"200 {{\"{p['verb'].lower()}_id\":\"{keep}\",\"item\":\"{p['item']}\",\"box\":\"child\"}}"),
            st(13, f"Observation: snapshot {keep}.",
               "browser_snapshot", {"interactive": True},
               f"[a11y]\n- status 'Kept {keep}' ref=s1"),
            st(14, f"Observation: {keep}. Write findings.",
               "write", {"path": f"findings/{host}-{p['item']}.json", "contents": json.dumps({"keep_id": keep, "item": p["item"], "source": f"child_ref_{p['css_short']}"}) + "\n"},
               f"wrote findings/{host}-{p['item']}.json"),
        ]
        outcome = f"{p['css']} changed the principal box. Clicked child {p['ref']}. POST: {keep}."

    reward = {
        "success": True,
        p["css_short"].split(":")[0].replace("-", "_")[:24]: 1,
        "ref_recovery": 1,
        "cost_steps": len(steps),
    }
    return rec(
        f"brw-r{n}-{p['ok_slug']}",
        f"On the designed {host.capitalize()} {p['noun']} desk, {p['verb'].lower()} {p['item']} after {p['css']}, and return the {p['verb'].lower()} id.",
        p["teach"],
        steps,
        outcome,
        reward,
        meta(n, p["seed_ok"], s),
    )


def build_fail(n: int, p: dict) -> dict:
    host = p["bad_host"]
    s = site(p["sub"], host)
    css_s = site("css", host)
    api = site("api", host)
    code = p["code"]
    if code == 409:
        raise BrwError("409-only fails are banned")
    item = p["item_fail"]
    steps = [
        st(1, f"Plan: open the designed {host.capitalize()} {p['noun']}s before posting a stale {p['css_short']} box.",
           "browser_navigate", {"url": f"https://{s}/keep"},
           _nav_obs(p, host, f"link rel='gate' href='https://{css_s}/gate'"),
           p["reflect"] + " Stale geometry is a failed dependency."),
        st(2, f"Observation: snapshot live {p['css_short']}.",
           "browser_snapshot", {"interactive": True},
           f"[a11y]\n- article '{item}' ref={p['ref_fail']}\n- button '{p['verb']}' ref={p['act_ref']}"),
        st(3, f"Observation: GET {p['css_short']} gate.",
           "http_request", {"method": "GET", "url": f"https://{css_s}/gate", "headers": {"Accept": "application/json"}},
           f"200 {p['gate']}"),
        st(4, f"Observation: evaluate live box.",
           "browser_evaluate", {"expression": _eval_expr(p)},
           json.dumps({p["js_prop"][:6]: p["to_v"], "x": p["x1"], "y": p.get("y1", p["y"])})),
        st(5, f"Observation: fill {item}.",
           "browser_fill_form", {"fields": [{"ref": p["note_ref"], "value": item}]},
           f"filled {p['note_ref']}='{item}'"),
        st(6, f"Observation: screenshot stale vs live.",
           "browser_screenshot", {"filename": f"findings/{host}-stale.png"},
           f"png: live {p['css_short']}={p['to_v']}; old geometry still painted as a trap"),
        st(7, f"Observation: POST stale {p['css_short']} payload.",
           "http_request",
           {"method": "POST", "url": f"https://{s}/ui/keep", "headers": {"Content-Type": "application/json", f"X-{host[:4].capitalize()}-Key": f"{host[:4]}-write"}, "body": json.loads(p["fail_body"]) if p["fail_body"].startswith("{") else {"code": item}},
           f"{code} {{\"error\":\"{p['err']}\",\"have\":{p['to_v']!r}}}"),
        st(8, f"Observation: GET OpenAPI {code}.",
           "http_request", {"method": "GET", "url": f"https://{api}/openapi.json", "headers": {"Accept": "application/json"}},
           f"200\nPOST /{p['sub']} {code} {p['err']}"),
        st(9, f"Observation: GET {item}.",
           "http_request", {"method": "GET", "url": f"https://{api}/{p['sub']}/{item}", "headers": {"Accept": "application/json"}},
           f"200 {{\"item\":\"{item}\",\"kept\":false}}"),
        st(10, f"Observation: snapshot {code}.",
           "browser_snapshot", {"interactive": True},
           f"[a11y]\n- status '{code} {p['err']}' ref=s1"),
        st(11, f"Observation: click {p['verb']} {p['act_ref']}.",
           "browser_click", {"ref": p["act_ref"]},
           f"Error: locator.click: {p['verb']} disabled ({p['err']})"),
        st(12, f"Observation: wait {code} lock.",
           "browser_wait", {"seconds": 1, "reason": f"{p['err']} lock"},
           f"still unkept; {p['err']}"),
        st(13, f"Observation: stop. Write {code} handoff.",
           "write",
           {"path": f"findings/{host}-{item}-unkept.json",
            "contents": json.dumps({"item": item, "kept": False, "reason": f"{p['css_short']} POST {code} {p['err']}", "source": p["seed_bad"]}) + "\n"},
           f"wrote findings/{host}-{item}-unkept.json"),
    ]
    # body must be object for http_request; r192 used dict. parse fail_body
    # already handled above
    outcome = f"Posted stale {p['css_short']} geometry. {code} {p['err']}. {item} unkept."
    reward = {
        "success": False,
        p["css_short"].split(":")[0].replace("-", "_")[:24]: 1,
        f"http_{code}s": 1,
        "kept": 0,
        "cost_steps": len(steps),
    }
    return rec(
        f"brw-r{n}-{p['bad_slug']}",
        f"On the designed {host.capitalize()} {p['noun']} desk, {p['verb'].lower()} {item} after {p['css']} and return the {p['verb'].lower()} id.",
        f"If {p['verb']} posts stale {p['css_short']} geometry, API {code} {p['err']}. Stop.",
        steps,
        outcome,
        reward,
        meta(n, p["seed_bad"], s),
    )


def notes_for(n: int, p: dict) -> str:
    ok = f"brw-r{n}-{p['ok_slug']}"
    bad = f"brw-r{n}-{p['bad_slug']}"
    return (
        f"# browser-tool-use-factory — NOTES r{n}\n\n"
        f"Novel coverage: {p['coverage']}%\n\n"
        f"New: {p['novel']} Pair: {p['code']}, not 409. {p['not']}\n\n"
        f"| id | site | mechanic | success |\n"
        f"|---|---|---|---|\n"
        f"| {ok} | {site(p['sub'], p['ok_host'])} | {p['css_short']} then ref | true |\n"
        f"| {bad} | {site(p['sub'], p['bad_host'])} | stale {p['err']} {p['code']} | false |\n\n"
        f"## decision_basis audit\n"
        f"All steps Plan:/Observation:/Reflection:. Designed.\n\n"
        f"## Teaching\n"
        f"{p['teach']}\n\n"
        f"## Weaknesses / next\n"
        f"{p['next']}\n"
    )


def pair_for_round(n: int) -> dict:
    idx = n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise BrwError(f"no catalog entry for r{n} (first={CATALOG_FIRST} last={CATALOG_FIRST + len(PAIRS) - 1})")
    return PAIRS[idx]


def validate_pair(n: int, ok: dict, bad: dict, p: dict) -> None:
    for host in (p["ok_host"], p["bad_host"]):
        if host in BANNED_HOSTS:
            raise BrwError(f"banned host {host}")
    seed_blob = f"{p['css']} {p['seed_ok']} {p['seed_bad']} {p['css_short']}".lower()
    for token in BANNED_CSS:
        if token in seed_blob:
            raise BrwError(f"banned css as this-round seed: {token}")
    if ok["reward"]["success"] is not True:
        raise BrwError("success episode not success")
    if bad["reward"]["success"] is not False:
        raise BrwError("fail episode not fail")
    fail_blob = json.dumps(bad, ensure_ascii=False)
    if '"http_409s"' in fail_blob or fail_blob.count("409") and p["code"] == 409:
        raise BrwError("409 fail banned")
    for rec_ in (ok, bad):
        if not (13 <= len(rec_["steps"]) <= 16):
            raise BrwError("step count")
        if rec_["meta"]["generator"] != GEN:
            raise BrwError("generator")
        if rec_["meta"]["round"] != n:
            raise BrwError("round")


def pair_records(rnd: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Success then fail/handoff for ``rnd``. Raises ``BrwError`` if unclean."""

    rnd = require_round(rnd)
    pair = pair_for_round(rnd)
    ok = build_success(rnd, pair)
    bad = build_fail(rnd, pair)
    validate_pair(rnd, ok, bad, pair)
    return ok, bad


def generate_window(
    start_round: int = CATALOG_FIRST,
    count: int | None = None,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """One success/fail pair per catalog entry, rounds ``start_round`` .."""

    start_round = require_round(start_round)
    if count is None:
        count = len(cat.PAIRS)
    if type(count) is not int or not 1 <= count <= len(cat.PAIRS):
        raise BrwError(f"invalid_count: {count!r}")
    return [pair_records(start_round + index) for index in range(count)]
