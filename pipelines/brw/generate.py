#!/usr/bin/env python3
"""Build one browser-tool-use pair from an AST-extracted ``brw-mill-r193`` plant.

The success/fail tool sequences are the designed trajectories from the
AST-extracted mill: leftover CSS first, then new agent-breakers, 13–16 steps,
with a fail/handoff that is never HTTP 409. This module does not publish a
raw round and does not execute leftover mill scripts.
"""

from __future__ import annotations

import json
from collections import namedtuple
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
_JSON = "application/json"
_RECEIPT_BASIS = "Observation: GET api receipt."


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


_Scene = namedtuple("_Scene", "p host s css_s api keep shape x0 x1 y y1 vis_x")


def _scene(p: dict) -> _Scene:
    host = p["ok_host"]
    s, css_s, api = site(p["sub"], host), site("css", host), site("api", host)
    keep, shape, x0, x1, y = p["ok_id"], p["shape"], p["x0"], p["x1"], p["y"]
    return _Scene(p, host, s, css_s, api, keep, shape, x0, x1, y, p.get("y1", y), p.get("visual_x", x1))


def _open_step(c: _Scene, before: str, rel: str, path: str) -> dict:
    p, host = c.p, c.host
    return st(1, f"Plan: open the designed {host.capitalize()} {p['noun']}s before {before}.",
              "browser_navigate", {"url": f"https://{c.s}/keep"},
              _nav_obs(p, host, f"link rel='{rel}' href='https://{c.css_s}/{path}'"),
              p["reflect"])


def _contract_step(c: _Scene, n: int, basis: str, path: str) -> dict:
    p = c.p
    return st(n, basis,
              "http_request", {"method": "GET", "url": f"https://{c.css_s}/{path}", "headers": {"Accept": _JSON}},
              f"200 {{\"css\":{p['css']!r},\"warn\":{p['warn']!r}}}")


def _evaluate_step(c: _Scene, n: int, basis: str, measured: dict) -> dict:
    return st(n, basis, "browser_evaluate", {"expression": _eval_expr(c.p)}, json.dumps(measured))


def _click_trig_step(c: _Scene, n: int, effect: str) -> dict:
    p = c.p
    return st(n, f"Observation: click {p['trig']} {p['trig_ref']}.",
              "browser_click", {"ref": p["trig_ref"]}, f"clicked {p['trig_ref']}; {effect}")


def _click_item_step(c: _Scene, n: int, basis: str) -> dict:
    p = c.p
    return st(n, basis, "browser_click", {"ref": p["ref"]}, f"clicked {p['ref']}; {p['verb']} enabled")


def _fill_note_step(c: _Scene, n: int) -> dict:
    p, host = c.p, c.host
    return st(n, f"Observation: fill {p['verb'].lower()} note.",
              "browser_fill_form", {"fields": [{"ref": p["note_ref"], "value": f"{p['item']} {host[:4]}"}]},
              f"filled {p['note_ref']}='{p['item']} {host[:4]}'")


def _click_verb_step(c: _Scene, n: int, basis: str) -> dict:
    p = c.p
    return st(n, basis,
              "browser_click", {"ref": p["act_ref"]},
              f"clicked {p['act_ref']}; POST https://{c.s}/ui/keep → 201 {{\"{p['verb'].lower()}_id\":\"{c.keep}\",\"item\":\"{p['item']}\"}}")


def _receipt_step(c: _Scene, n: int, basis: str, tail: str) -> dict:
    p = c.p
    return st(n, basis,
              "http_request", {"method": "GET", "url": f"https://{c.api}/{p['verb'].lower()}s/{c.keep}", "headers": {"Accept": _JSON}},
              f"200 {{\"{p['verb'].lower()}_id\":\"{c.keep}\",\"item\":\"{p['item']}\",{tail}}}")


def _kept_step(c: _Scene, n: int, basis: str) -> dict:
    return st(n, basis, "browser_snapshot", {"interactive": True}, f"[a11y]\n- status 'Kept {c.keep}' ref=s1")


def _findings_step(c: _Scene, n: int, source: str) -> dict:
    p, host, keep = c.p, c.host, c.keep
    return st(n, f"Observation: {keep}. Write findings.",
              "write", {"path": f"findings/{host}-{p['item']}.json", "contents": json.dumps({"keep_id": keep, "item": p["item"], "source": source}) + "\n"},
              f"wrote findings/{host}-{p['item']}.json")


_TailWords = namedtuple("_TailWords", "click_item receipt receipt_tail kept source")


def _keep_tail(c: _Scene, words: _TailWords) -> list[dict]:
    """Steps 9-14 shared by the click-by-ref shapes: ref, note, verb, receipt, status, findings."""
    p = c.p
    return [
        _click_item_step(c, 9, words.click_item),
        _fill_note_step(c, 10),
        _click_verb_step(c, 11, f"Observation: click {p['verb']} {p['act_ref']}."),
        _receipt_step(c, 12, words.receipt, words.receipt_tail),
        _kept_step(c, 13, words.kept),
        _findings_step(c, 14, words.source),
    ]


def _shift_steps(c: _Scene) -> tuple[list[dict], str]:
    p, host, keep, x0, x1, y = c.p, c.host, c.keep, c.x0, c.x1, c.y
    steps = [
        _open_step(c, f"using a pre-{p['css_short']} x", "hint", "shift"),
        st(2, f"Observation: snapshot {p['from_v']} row.",
           "browser_snapshot", {"interactive": True},
           f"[a11y]\n- article '{p['item']}' ref={p['ref']}\n- article '{p['item_b']}' ref={p['ref_b']}"),
        _evaluate_step(c, 3, f"Observation: measure {p['item']} before {p['css_short']}.",
                       {p["js_prop"][:6]: p["from_v"], "x": x0, "y": y}),
        st(4, f"Observation: GET {p['css_short']} contract.",
           "http_request", {"method": "GET", "url": f"https://{c.css_s}/shift", "headers": {"Accept": _JSON}},
           f"200 {{\"from\":{p['from_v']!r},\"to\":{p['to_v']!r},\"warn\":{p['warn']!r}}}"),
        _click_trig_step(c, 5, f"{p['css_short']}={p['to_v']}; {p['item']} x {x0}→{x1}"),
        st(6, f"Observation: click stored x={x0}.",
           "browser_click", {"position": {"x": x0, "y": y}},
           f"Error: click hit {p['item_b']} (now at {x0}); {p['item']} is at {x1}"),
        st(7, f"Observation: screenshot {p['css_short']} shift.",
           "browser_screenshot", {"filename": f"findings/{host}-{p['css_short'].replace(':','-')}.png"},
           f"png: {p['item_b']} under old x; {p['item']} at {x1}"),
        _evaluate_step(c, 8, f"Observation: remeasure after {p['to_v']}.",
                       {p["js_prop"][:6]: p["to_v"], "x": x1, "y": c.y1}),
        *_keep_tail(c, _TailWords(
            f"Observation: click {p['item']} {p['ref']}.", f"Observation: GET api {p['verb'].lower()}.",
            f"\"{p['css_short']}\":{p['to_v']!r}", f"Observation: snapshot kept {keep}.", f"ref_after_{p['css_short']}")),
    ]
    outcome = f"{p['css']} moved {p['item']}. Stored x hit {p['item_b']}. Clicked {p['ref']}. POST: {keep}."
    return steps, outcome


def _backface_steps(c: _Scene, steps: list[dict]) -> None:
    """Trig is "Show face" — do not flip before proving the hidden backface miss."""
    p = c.p
    steps[4] = st(5, f"Observation: click {p['item']} {p['ref']} while rotateY=180.",
                  "browser_click", {"ref": p["ref"]},
                  f"Error: locator.click: {p['item']} backface-hidden; a11y node exists, paint is the back")
    steps[5] = st(6, "Observation: click stored face x (empty paint).",
                  "browser_click", {"position": {"x": c.vis_x, "y": c.y}},
                  f"Error: click hit empty transformed face; {p['item']} backface-visibility=hidden")
    steps.insert(7, st(8, f"Observation: click {p['trig']} {p['trig_ref']} to rotateY(0).",
                       "browser_click", {"ref": p["trig_ref"]},
                       "clicked e4; rotateY=0; face visible; Flip enabled"))
    for i, step in enumerate(steps, 1):
        step["n"] = i
    if not (13 <= len(steps) <= 16):
        raise BrwError(f"visual/backface step count {len(steps)}")


def _visual_steps(c: _Scene) -> tuple[list[dict], str]:
    p, host, keep, x0, y, vis_x = c.p, c.host, c.keep, c.x0, c.y, c.vis_x
    steps = [
        _open_step(c, "treating painted pixels as the hit box", "paint", "paint"),
        st(2, f"Observation: snapshot {p['noun']}s and {p['css_short']}.",
           "browser_snapshot", {"interactive": True},
           f"[a11y]\n- article '{p['item']}' ref={p['ref']}\n- article '{p['item_b']}' ref={p['ref_b']}\n- button '{p['verb']}' ref={p['act_ref']}"),
        _evaluate_step(c, 3, f"Observation: evaluate {p['css_short']} vs box.",
                       {p["js_prop"][:6]: p["to_v"], "x": x0, "y": y, "width": 72}),
        _contract_step(c, 4, "Observation: GET paint-vs-hit contract.", "paint"),
        _click_trig_step(c, 5, f"{p['css_short']} live; paint ≠ box"),
        st(6, f"Observation: click visual blob at x={vis_x}.",
           "browser_click", {"position": {"x": vis_x, "y": y}},
           f"Error: click hit {p['item']} box at {x0} (paint was at {vis_x}); not {p['item_b']}"),
        st(7, "Observation: screenshot paint vs used box.",
           "browser_screenshot", {"filename": f"findings/{host}-paint.png"},
           f"png: painted face offset; a11y still {p['item']} at {x0}"),
        _evaluate_step(c, 8, "Observation: remeasure unfiltered/unmasked box.",
                       {p["js_prop"][:6]: p["to_v"], "x": x0, "y": y}),
        *_keep_tail(c, _TailWords(
            f"Observation: click {p['item']} {p['ref']} not the blob.", _RECEIPT_BASIS,
            "\"via\":\"a11y_ref\"", f"Observation: snapshot {keep}.", f"ref_not_paint_{p['css_short']}")),
    ]
    if p["css_short"] == "backface-visibility":
        _backface_steps(c, steps)
    outcome = f"{p['css']} split paint from the used box. Clicked {p['ref']}. POST: {keep}."
    return steps, outcome


def _overlay_steps(c: _Scene) -> tuple[list[dict], str]:
    p, host, keep, x0, y = c.p, c.host, c.keep, c.x0, c.y
    steps = [
        _open_step(c, f"clicking through {p['css_short']}", "layer", "layer"),
        st(2, f"Observation: snapshot overlay covering {p['verb']}.",
           "browser_snapshot", {"interactive": True},
           f"[a11y]\n- article '{p['item']}' ref={p['ref']}\n- generic overlay ref=ov1\n- button '{p['verb']}' ref={p['act_ref']}\n- button '{p['trig']}' ref={p['trig_ref']}"),
        _evaluate_step(c, 3, f"Observation: evaluate overlay vs {p['verb']} box.",
                       {p["js_prop"][:6]: p["from_v"], "x": x0, "y": y, "overlay": True}),
        _contract_step(c, 4, f"Observation: GET {p['css_short']} contract.", "layer"),
        st(5, f"Observation: click {p['verb']} px through the overlay.",
           "browser_click", {"position": {"x": x0, "y": y}},
           f"Error: click hit overlay ({p['css_short']}); {p['verb']} not received"),
        st(6, "Observation: screenshot overlay capture.",
           "browser_screenshot", {"filename": f"findings/{host}-overlay.png"},
           f"png: {p['css_short']} covering {p['verb']}"),
        _click_trig_step(c, 7, f"overlay cleared or stage scrolled; {p['verb']} free"),
        _evaluate_step(c, 8, "Observation: remeasure after overlay gone.",
                       {p["js_prop"][:6]: p["to_v"], "x": c.x1, "y": c.y1}),
        *_keep_tail(c, _TailWords(
            f"Observation: click {p['item']} {p['ref']}.", _RECEIPT_BASIS,
            "\"overlay\":\"cleared\"", f"Observation: snapshot {keep}.", f"clear_{p['css_short']}")),
    ]
    outcome = f"{p['css']} captured the click. Cleared overlay, clicked {p['ref']}. POST: {keep}."
    return steps, outcome


def _viewport_steps(c: _Scene) -> tuple[list[dict], str]:
    p, host, keep, x0, y, y1 = c.p, c.host, c.keep, c.x0, c.y, c.y1
    vpl = p.get("vp_label", "closed-chrome y")
    steps = [
        _open_step(c, f"trusting a {vpl}", "vp", "vp"),
        st(2, f"Observation: snapshot layout under {vpl}.",
           "browser_snapshot", {"interactive": True},
           f"[a11y]\n- article '{p['item']}' ref={p['ref']}\n- button '{p['verb']}' ref={p['act_ref']} y≈{y}"),
        _evaluate_step(c, 3, f"Observation: measure {p['css_short']} before the viewport/env change.",
                       {p["js_prop"][:6]: p["from_v"], "x": x0, "y": y}),
        _contract_step(c, 4, "Observation: GET viewport/env contract.", "vp"),
        _click_trig_step(c, 5, f"chrome/keyboard changed; {p['item']} y {y}→{y1}"),
        st(6, f"Observation: click stored y={y}.",
           "browser_click", {"position": {"x": x0, "y": y}},
           f"Error: click hit chrome/keyboard or {p['item_b']}; {p['item']} now at y={y1}"),
        st(7, "Observation: screenshot after viewport change.",
           "browser_screenshot", {"filename": f"findings/{host}-vp.png"},
           f"png: {p['verb']} lifted/grown; old y is leftover chrome"),
        _evaluate_step(c, 8, "Observation: remeasure dvh/inset box.",
                       {p["js_prop"][:6]: p["to_v"], "x": c.x1, "y": y1}),
        *_keep_tail(c, _TailWords(
            f"Observation: click {p['item']} {p['ref']}.", _RECEIPT_BASIS,
            f"\"unit\":{p['to_v']!r}", f"Observation: snapshot {keep}.", f"ref_after_{p['css_short']}")),
    ]
    outcome = f"{p['css']} moved the used y. Stored y missed. Clicked {p['ref']}. POST: {keep}."
    return steps, outcome


def _text_steps(c: _Scene) -> tuple[list[dict], str]:
    p, host, keep = c.p, c.host, c.keep
    steps = [
        _open_step(c, f"trusting OCR after {p['css_short']}", "type", "type"),
        st(2, "Observation: snapshot unwrapped label.",
           "browser_snapshot", {"interactive": True},
           f"[a11y]\n- article '{p['item']}' ref={p['ref']} name='締約 Post'\n- button '{p['verb']}' ref={p['act_ref']}"),
        _evaluate_step(c, 3, "Observation: measure wrap before auto-phrase.",
                       {p["js_prop"][:6]: p["from_v"], "lines": 1, "x": c.x0, "y": c.y}),
        _contract_step(c, 4, "Observation: GET phrase-wrap contract.", "type"),
        _click_trig_step(c, 5, f"{p['css_short']}={p['to_v']}; label now 2 lines covering {p['verb']}"),
        st(6, "Observation: OCR the wrapped fragment.",
           "browser_evaluate", {"expression": "document.querySelector('[data-ref=" + p['ref'] + "]').innerText"},
           "締\\n約 Post"),
        st(7, f"Observation: screenshot phrase wrap over {p['verb']}.",
           "browser_screenshot", {"filename": f"findings/{host}-phrase.png"},
           f"png: second line covers {p['verb']}; glyph '締' is not the token"),
        _click_item_step(c, 8, f"Observation: click {p['item']} {p['ref']} not the fragment."),
        st(9, f"Observation: fill {p['verb'].lower()} with full token.",
           "browser_fill_form", {"fields": [{"ref": p["note_ref"], "value": p["item"]}]},
           f"filled {p['note_ref']}='{p['item']}'"),
        _click_verb_step(c, 10, f"Observation: click {p['verb']} {p['act_ref']} by ref under wrap."),
        _receipt_step(c, 11, _RECEIPT_BASIS, "\"token\":\"full\""),
        st(12, "Observation: GET OpenAPI 415 clause.",
           "http_request", {"method": "GET", "url": f"https://{c.api}/openapi.json", "headers": {"Accept": _JSON}},
           f"200\nPOST /{p['sub']} 415 phrase_ocr if token is a wrap fragment"),
        _kept_step(c, 13, f"Observation: snapshot {keep}."),
        _findings_step(c, 14, "ref_not_ocr_fragment"),
    ]
    outcome = f"{p['css']} wrapped the label. OCR fragment ignored. Clicked {p['act_ref']}. POST: {keep}."
    return steps, outcome


def _box_steps(c: _Scene) -> tuple[list[dict], str]:
    p, host, keep, x0, y = c.p, c.host, c.keep, c.x0, c.y
    steps = [
        _open_step(c, "clicking a vanished or cloned box", "box", "box"),
        st(2, "Observation: snapshot principal box.",
           "browser_snapshot", {"interactive": True},
           f"[a11y]\n- article '{p['item']}' ref={p['ref']}\n- generic parent ref=par\n- button '{p['verb']}' ref={p['act_ref']}"),
        _evaluate_step(c, 3, f"Observation: measure box before {p['css_short']}.",
                       {p["js_prop"][:6]: p["from_v"], "x": x0, "y": y, "w": 72, "h": 40}),
        _contract_step(c, 4, "Observation: GET box contract.", "box"),
        _click_trig_step(c, 5, f"{p['css_short']}={p['to_v']}; principal box changed"),
        st(6, f"Observation: click old parent/lobe x={x0}.",
           "browser_click", {"position": {"x": x0 if p['css_short'] != 'overflow-clip-margin' else x0 + 32, "y": y if p['css_short'] != 'box-decoration-break' else y + 34}},
           f"Error: {p['css_short']} — empty parent, cloned fragment, or leaked lobe; not {p['item']} hit"),
        st(7, "Observation: screenshot box change.",
           "browser_screenshot", {"filename": f"findings/{host}-box.png"},
           f"png: {p['css_short']} altered the painted box; child/ref still {p['item']}"),
        _evaluate_step(c, 8, "Observation: remeasure used child box.",
                       {p["js_prop"][:6]: p["to_v"], "x": c.x1, "y": c.y1, "w": 0 if p["css_short"] == "display:contents" else 72}),
        *_keep_tail(c, _TailWords(
            f"Observation: click child {p['item']} {p['ref']}.", _RECEIPT_BASIS,
            "\"box\":\"child\"", f"Observation: snapshot {keep}.", f"child_ref_{p['css_short']}")),
    ]
    outcome = f"{p['css']} changed the principal box. Clicked child {p['ref']}. POST: {keep}."
    return steps, outcome


_SHAPE_STEPS = (("shift", _shift_steps), ("visual", _visual_steps), ("overlay", _overlay_steps),
                ("viewport", _viewport_steps), ("text", _text_steps))


def build_success(n: int, p: dict) -> dict:
    c = _scene(p)
    build = next((steps_of for shape, steps_of in _SHAPE_STEPS if c.shape == shape), _box_steps)
    steps, outcome = build(c)
    reward = {
        "success": True,
        p["css_short"].split(":")[0].replace("-", "_")[:24]: 1,
        "ref_recovery": 1,
        "cost_steps": len(steps),
    }
    return rec(
        f"brw-r{n}-{p['ok_slug']}",
        f"On the designed {c.host.capitalize()} {p['noun']} desk, {p['verb'].lower()} {p['item']} after {p['css']}, and return the {p['verb'].lower()} id.",
        p["teach"],
        steps,
        outcome,
        reward,
        meta(n, p["seed_ok"], c.s),
    )


_FailScene = namedtuple("_FailScene", "p host s css_s api code item")


def _fail_scene(p: dict) -> _FailScene:
    host = p["bad_host"]
    s, css_s, api = site(p["sub"], host), site("css", host), site("api", host)
    if p["code"] == 409:
        raise BrwError("409-only fails are banned")
    return _FailScene(p, host, s, css_s, api, p["code"], p["item_fail"])


def _fail_probe_steps(c: _FailScene) -> list[dict]:
    p, host, item = c.p, c.host, c.item
    return [
        st(1, f"Plan: open the designed {host.capitalize()} {p['noun']}s before posting a stale {p['css_short']} box.",
           "browser_navigate", {"url": f"https://{c.s}/keep"},
           _nav_obs(p, host, f"link rel='gate' href='https://{c.css_s}/gate'"),
           p["reflect"] + " Stale geometry is a failed dependency."),
        st(2, f"Observation: snapshot live {p['css_short']}.",
           "browser_snapshot", {"interactive": True},
           f"[a11y]\n- article '{item}' ref={p['ref_fail']}\n- button '{p['verb']}' ref={p['act_ref']}"),
        st(3, f"Observation: GET {p['css_short']} gate.",
           "http_request", {"method": "GET", "url": f"https://{c.css_s}/gate", "headers": {"Accept": _JSON}},
           f"200 {p['gate']}"),
        st(4, "Observation: evaluate live box.",
           "browser_evaluate", {"expression": _eval_expr(p)},
           json.dumps({p["js_prop"][:6]: p["to_v"], "x": p["x1"], "y": p.get("y1", p["y"])})),
        st(5, f"Observation: fill {item}.",
           "browser_fill_form", {"fields": [{"ref": p["note_ref"], "value": item}]},
           f"filled {p['note_ref']}='{item}'"),
        st(6, "Observation: screenshot stale vs live.",
           "browser_screenshot", {"filename": f"findings/{host}-stale.png"},
           f"png: live {p['css_short']}={p['to_v']}; old geometry still painted as a trap"),
    ]


def _fail_post_steps(c: _FailScene) -> list[dict]:
    p, host, item, code = c.p, c.host, c.item, c.code
    return [
        st(7, f"Observation: POST stale {p['css_short']} payload.",
           "http_request",
           {"method": "POST", "url": f"https://{c.s}/ui/keep", "headers": {"Content-Type": _JSON, f"X-{host[:4].capitalize()}-Key": f"{host[:4]}-write"}, "body": json.loads(p["fail_body"]) if p["fail_body"].startswith("{") else {"code": item}},
           f"{code} {{\"error\":\"{p['err']}\",\"have\":{p['to_v']!r}}}"),
        st(8, f"Observation: GET OpenAPI {code}.",
           "http_request", {"method": "GET", "url": f"https://{c.api}/openapi.json", "headers": {"Accept": _JSON}},
           f"200\nPOST /{p['sub']} {code} {p['err']}"),
        st(9, f"Observation: GET {item}.",
           "http_request", {"method": "GET", "url": f"https://{c.api}/{p['sub']}/{item}", "headers": {"Accept": _JSON}},
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


def build_fail(n: int, p: dict) -> dict:
    c = _fail_scene(p)
    host, code, item = c.host, c.code, c.item
    steps = _fail_probe_steps(c) + _fail_post_steps(c)
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
        meta(n, p["seed_bad"], c.s),
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


def _refuse_banned_seed(p: dict) -> None:
    for host in (p["ok_host"], p["bad_host"]):
        if host in BANNED_HOSTS:
            raise BrwError(f"banned host {host}")
    seed_blob = f"{p['css']} {p['seed_ok']} {p['seed_bad']} {p['css_short']}".lower()
    for token in BANNED_CSS:
        if token in seed_blob:
            raise BrwError(f"banned css as this-round seed: {token}")


def _mentions_409(fail_blob: str, p: dict) -> bool:
    """A 409 counter key, or any "409" in the record when the plant's code is 409."""
    if '"http_409s"' in fail_blob:
        return True
    return bool(fail_blob.count("409")) and p["code"] == 409


def _refuse_wrong_outcomes(ok: dict, bad: dict, p: dict) -> None:
    if ok["reward"]["success"] is not True:
        raise BrwError("success episode not success")
    if bad["reward"]["success"] is not False:
        raise BrwError("fail episode not fail")
    if _mentions_409(json.dumps(bad, ensure_ascii=False), p):
        raise BrwError("409 fail banned")


def _refuse_wrong_shape(n: int, ok: dict, bad: dict) -> None:
    for rec_ in (ok, bad):
        if not (13 <= len(rec_["steps"]) <= 16):
            raise BrwError("step count")
        if rec_["meta"]["generator"] != GEN:
            raise BrwError("generator")
        if rec_["meta"]["round"] != n:
            raise BrwError("round")


def validate_pair(n: int, ok: dict, bad: dict, p: dict) -> None:
    _refuse_banned_seed(p)
    _refuse_wrong_outcomes(ok, bad, p)
    _refuse_wrong_shape(n, ok, bad)


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
