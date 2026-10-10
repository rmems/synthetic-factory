#!/usr/bin/env python3
"""Shared fixtures and helpers for the catalog-browser test modules.

The browser surface is exercised through the committed ``catalog-browser``
pack and through stub packs whose pages are authored here. The DOM, surface,
and pack modules share the task ids, the page fixtures, the malformed-site
table, and the environment builders that pick a seed by what it arms.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_test_support import cv, make_env

# The support module goes first: it puts pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import faults as faults_mod
from tool_world.policies import scripted
from tool_world.surfaces import browser as browser_mod
from tool_world.surfaces import browser_dom as dom

PACK = "catalog-browser"
SEARCH = "catalog.search-bolt"
PRICE = "catalog.price-of-hb08"
LEGACY = "catalog.wn10-via-legacy-path"
TASKS = (SEARCH, PRICE, LEGACY)
ORIGIN = "https://parts.example"
SAMPLE_SEEDS = (1, 2, 3, 7)
REF_RE = re.compile(r"\[ref=(e\d+)\]")

FORM_PAGE = """<html><head><title>Form page</title></head><body>
<h2>Sign in</h2>
<div role="dialog" aria-label="Notice" id="notice"><p>Read me.</p>
<button data-effect="dismiss:notice">Close</button></div>
<form id="login" action="/login">
<input type="text" name="user" placeholder="User name" value="ann">
<input type="checkbox" name="remember" aria-label="Remember me" checked>
<input type="hidden" name="scope" value="all">
<textarea name="note"></textarea>
<input type="submit" value="Sign in">
</form>
<button data-state="on" data-effect="toggle:panel">Panel</button>
<p id="panel">Panel text <a href="/next" rel="next">More</a></p>
<a>no href</a>
</body></html>"""

EFFECTS_PAGE = """<html><head><title>Effects</title></head><body>
<h1>Effects</h1>
<input type="checkbox" name="opt" aria-label="Option">
<button data-effect="toggle:panel">Panel</button>
<button data-effect="toggle:missing">Ghost</button>
<button>Plain</button>
<button data-effect="next">Older</button>
<button data-effect="navigate:/end">Jump</button>
<p id="panel">Panel body</p>
<a rel="next" href="/end">More</a>
</body></html>"""
END_PAGE = """<html><head><title>End</title></head><body>
<button data-effect="next">Older</button>
</body></html>"""


PAGE_FILE = "page.html"
END_FILE = "end.html"
ORIGIN_NEEDLE = "origin must be"
SITE = {"origin": ORIGIN, "pages": {"/": PAGE_FILE, "/end": END_FILE}}
CONSENT = (
    '<div role="dialog" aria-label="Cookie consent" id="consent">'
    '<button data-effect="dismiss:consent">Accept</button></div>'
)
OVERLAY_SITE = {**SITE, "overlays": {"consent": CONSENT}}
BAD_SITES = {
    "pages value list": ({"origin": ORIGIN, "pages": {"/": [PAGE_FILE]}}, "pages must map"),
    "pages missing": ({"origin": ORIGIN}, "pages must be a nonempty table"),
    "pages empty": ({"origin": ORIGIN, "pages": {}}, "pages must be a nonempty table"),
    "not_found list": ({**SITE, "not_found": ["x"]}, "not_found must name"),
    "redirects list": ({**SITE, "redirects": ["/a"]}, "redirects must map"),
    "redirect value int": ({**SITE, "redirects": {"/a": 5}}, "redirects must map"),
    "overlays list": ({**SITE, "overlays": ["x"]}, "overlays must map"),
    "overlay value int": ({**SITE, "overlays": {"c": 5}}, "overlays must map"),
    "drift list": ({**SITE, "drift": ["x"]}, "drift must map"),
    "drift value int": ({**SITE, "drift": {"a": 5}}, "drift must map"),
    "missing member": ({**SITE, "pages": {"/": "nope.html"}}, "missing page members ['nope.html']"),
    "not_found missing": ({**SITE, "not_found": "nope.html"}, "missing page members"),
    "redirect to missing": ({**SITE, "redirects": {"/a": "/zz"}}, "undeclared paths ['/zz']"),
    "origin bare": ({**SITE, "origin": "parts"}, ORIGIN_NEEDLE),
    "origin with path": ({**SITE, "origin": f"{ORIGIN}/x"}, ORIGIN_NEEDLE),
    "origin int": ({**SITE, "origin": 5}, ORIGIN_NEEDLE),
}


def site_pages(page):
    """The two-member page table every stub site serves: ``page`` at "/", the end page at "/end"."""
    return {PAGE_FILE: page, END_FILE: END_PAGE}


class StubPack:
    def __init__(self, site=None, pages=None):
        self.pack_id = "stub"
        self.site = SITE if site is None else site
        self.pages = site_pages(EFFECTS_PAGE) if pages is None else pages


class StubTask:
    def __init__(self, faults=()):
        self.task_id = "stub.task"
        self.faults = tuple(faults)


def stub_surface(site=None, pages=None, faults=()):
    return browser_mod.BrowserSurface(StubPack(site, pages), StubTask(faults), None)


def fault_spec(**overrides):
    """A browser overlay fault row, parsed the way the pack loader parses it."""
    row = {
        "id": "f",
        "surface": "browser",
        "kind": "overlay",
        "tool": "browser",
        "selector": {"action": "navigate", "url": "/"},
        "params": {"overlay": "consent"},
        "marker": "m",
    }
    row.update(overrides)
    return faults_mod.fault_spec_from_row(row, "test")


def scheduled(spec):
    return faults_mod.ScheduledFault(spec, True, 1)


def navigate(url):
    return {"name": cv.TOOL_BROWSER, "args": {"action": "navigate", "url": url}}


def browse(env, **args):
    """One browser call; the bounded observation text."""
    return env.step({"name": cv.TOOL_BROWSER, "args": args}).text


def without_refs(text: str) -> str:
    return re.sub(r"\[ref=e\d+\]", "[ref]", text)


def ref_in(text):
    match = REF_RE.search(text)
    if match is None:
        raise AssertionError(f"no ref in {text!r}")
    return match.group(1)


def seed_where(task_id, condition):
    """The first seed under 200 whose fresh environment satisfies ``condition``."""
    for seed in range(200):
        if condition(make_env(PACK, task_id, seed)):
            return seed
    raise AssertionError(f"no seed under 200 satisfies the condition for {task_id}")


def quiet_env(task_id):
    """An environment whose seed arms no fault at all."""
    return make_env(
        PACK, task_id, seed_where(task_id, lambda env: not env.fault_engine.armed_ids())
    )


def firing_env(task_id, fault_id, url):
    """A fresh environment whose first navigate to ``url`` fires ``fault_id``."""
    return make_env(
        PACK, task_id, seed_where(task_id, lambda env: env.step(navigate(url)).fault_id == fault_id)
    )


def gold_run(task_id, seed):
    env = make_env(PACK, task_id, seed)
    trajectory = scripted.run(env)
    return env, trajectory


def roles_of(root):
    return [(node.tag, dom.role_of(node)) for node in root.walk() if dom.role_of(node)]
