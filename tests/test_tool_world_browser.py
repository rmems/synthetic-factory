#!/usr/bin/env python3
"""The browser surface: its DOM model, the catalog-browser pack, and the fault recoveries."""

import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_test_support import (
    CATALOG_DIR,
    PRODUCED_AT,
    catalog_mod,
    cv,
    load_pack,
    make_env,
    private_catalog,
    refusal,
)

# The support module goes first: it puts pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import faults as faults_mod
from tool_world import generate, replay
from tool_world._contract import contains_hidden_reasoning_key, load_strict_json
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


SITE = {"origin": ORIGIN, "pages": {"/": "page.html", "/end": "end.html"}}
CONSENT = (
    '<div role="dialog" aria-label="Cookie consent" id="consent">'
    '<button data-effect="dismiss:consent">Accept</button></div>'
)
OVERLAY_SITE = {**SITE, "overlays": {"consent": CONSENT}}
BAD_SITES = {
    "pages value list": ({"origin": ORIGIN, "pages": {"/": ["page.html"]}}, "pages must map"),
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
    "origin bare": ({**SITE, "origin": "parts"}, "origin must be"),
    "origin with path": ({**SITE, "origin": f"{ORIGIN}/x"}, "origin must be"),
    "origin int": ({**SITE, "origin": 5}, "origin must be"),
}


class _StubPack:
    def __init__(self, site=None, pages=None):
        self.pack_id = "stub"
        self.site = SITE if site is None else site
        self.pages = {"page.html": EFFECTS_PAGE, "end.html": END_PAGE} if pages is None else pages


class _StubTask:
    def __init__(self, faults=()):
        self.task_id = "stub.task"
        self.faults = tuple(faults)


def stub_surface(site=None, pages=None, faults=()):
    return browser_mod.BrowserSurface(_StubPack(site, pages), _StubTask(faults), None)


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


class DomTests(unittest.TestCase):
    def setUp(self):
        self.root = dom.parse_html(FORM_PAGE)

    def test_parse_keeps_tags_attributes_and_text(self):
        form = self.root.find_id("login")
        self.assertEqual(
            (self.root.tag, form.tag, form.attrs["action"]), ("document", "form", "/login")
        )
        textarea = next(node for node in self.root.walk() if node.tag == "textarea")
        self.assertIs(textarea.parent, form)
        panel = self.root.find_id("panel")
        self.assertEqual((panel.text(), panel.direct_text()), ("Panel text More", "Panel text"))
        self.assertEqual(dom.title_of(self.root), "Form page")
        self.assertIsNone(self.root.find_id("absent"))

    def test_roles_follow_tag_and_input_type(self):
        self.assertEqual(
            roles_of(self.root),
            [
                ("title", "text"),
                ("h2", "heading"),
                ("div", "dialog"),
                ("p", "text"),
                ("button", "button"),
                ("form", "form"),
                ("input", "textbox"),
                ("input", "checkbox"),
                ("textarea", "textbox"),
                ("input", "button"),
                ("button", "button"),
                ("p", "text"),
                ("a", "link"),
            ],
        )

    def test_names_prefer_labels_then_placeholders_then_attributes(self):
        names = [
            dom.name_of(node, dom.role_of(node)) for node in self.root.walk() if dom.role_of(node)
        ]
        self.assertEqual(
            names,
            [
                "Form page",
                "Sign in",
                "Notice",
                "Read me.",
                "Close",
                "login",
                "User name",
                "Remember me",
                "note",
                "Sign in",
                "Panel",
                "Panel text",
                "More",
            ],
        )

    def test_refs_number_snapshotted_elements_in_document_order(self):
        refs = dom.assign_refs(self.root)
        self.assertEqual(list(refs), [f"e{n}" for n in range(1, 14)])
        self.assertEqual(refs["e3"].attrs["id"], "notice")
        refs["e3"].remove()
        self.assertEqual(len(dom.assign_refs(self.root)), 10)
        self.assertEqual(dom.dialogs(self.root), [])

    def test_header_rows_get_no_ref_but_their_cells_do(self):
        root = dom.parse_html(load_pack(PACK).pages["items-1.html"])
        dom.assign_refs(root)
        rows = [node for node in root.walk() if node.tag == "tr"]
        self.assertIsNone(rows[0].ref)
        self.assertTrue(all(cell.ref for cell in rows[0].children if isinstance(cell, dom.Node)))
        self.assertTrue(all(row.ref for row in rows[1:]))

    def test_snapshot_shows_roles_names_refs_state_and_nesting(self):
        dom.assign_refs(self.root)
        lines = dom.snapshot(self.root).splitlines()
        self.assertIn('- dialog "Notice" [ref=e3]', lines)
        self.assertIn('  - button "Close" [ref=e5]', lines)
        self.assertIn("  - textbox \"User name\" [ref=e7] [value='ann']", lines)
        self.assertIn('  - checkbox "Remember me" [ref=e8] [checked]', lines)
        self.assertIn('- button "Panel" [ref=e11] [state=on]', lines)
        self.assertEqual(lines[-2:], ['- text "Panel text" [ref=e12]', '- link "More" [ref=e13]'])
        self.assertEqual(dom.snapshot(dom.parse_html("<html><body></body></html>")), "(empty page)")

    def test_dialogs_forms_and_pager_helpers(self):
        form = self.root.find_id("login")
        textarea = next(node for node in self.root.walk() if node.tag == "textarea")
        self.assertEqual([node.attrs["id"] for node in dom.dialogs(self.root)], ["notice"])
        self.assertIs(dom.enclosing_form(textarea), form)
        self.assertIs(dom.enclosing_form(form), form)
        self.assertIsNone(dom.enclosing_form(self.root.find_id("panel")))
        self.assertTrue(dom.inside(textarea, form))
        self.assertFalse(dom.inside(form, textarea))
        self.assertEqual(
            [field.attrs["name"] for field in dom.form_inputs(form)],
            ["user", "remember", "scope", "note"],
        )
        self.assertEqual(dom.next_link(self.root).attrs["href"], "/next")


class BrowserSurfaceTests(unittest.TestCase):
    def test_navigate_reports_url_title_and_snapshot(self):
        text = browse(quiet_env(SEARCH), action="navigate", url="/")
        self.assertTrue(text.startswith(f"url: {ORIGIN}/\ntitle: Parts catalog\n"))
        for line in ('- form "search"', '  - textbox "Search parts"', '- link "All items"'):
            self.assertIn(line, text)

    def test_actions_need_a_page_and_navigation_stays_inside_the_origin(self):
        env = quiet_env(SEARCH)
        self.assertEqual(
            browse(env, action="find", role="link"), "error: no page is open; navigate first"
        )
        self.assertEqual(
            browse(env, action="navigate", url="https://other.example/"),
            f"error: navigation blocked: https://other.example/ is outside {ORIGIN}",
        )
        self.assertEqual(browse(env, action="navigate", url=""), "error: navigate needs url")
        self.assertEqual(env.surface(cv.SURFACE_BROWSER).url, "")
        browse(env, action="navigate", url=f"{ORIGIN}/items")
        self.assertEqual(env.surface(cv.SURFACE_BROWSER).url, f"{ORIGIN}/items")
        with refusal(self, cv.FINDING_SURFACE_UNKNOWN):
            env.surface(cv.SURFACE_MCP)

    def test_unknown_paths_show_the_pack_404_page(self):
        env = quiet_env(SEARCH)
        text = browse(env, action="navigate", url="/missing")
        self.assertTrue(text.startswith(f"url: {ORIGIN}/missing\ntitle: Page not found\n"))
        self.assertIn('- link "Back to the catalog"', text)

    def test_redirects_follow_the_declared_chain(self):
        env = quiet_env(SEARCH)
        text = browse(env, action="navigate", url="/parts")
        self.assertTrue(text.startswith(f"url: {ORIGIN}/items\ntitle: Parts list, page 1\n"))
        self.assertEqual(
            env.surface(cv.SURFACE_BROWSER).state_view()["visited"], [f"{ORIGIN}/items"]
        )

    def test_find_filters_by_role_and_case_folded_name(self):
        env = quiet_env(PRICE)
        browse(env, action="navigate", url="/items")
        self.assertEqual(
            browse(env, action="find", role="row", name="wn-10"),
            '- row "Wing nut M10 WN-10 0.45" [ref=e11]',
        )
        self.assertEqual(browse(env, action="find", role="link"), '- link "Next page" [ref=e19]')
        self.assertEqual(
            browse(env, action="find", role="text", name="sku"), '- text "SKU" [ref=e5]'
        )
        self.assertEqual(
            browse(env, action="find", name="nothing"), "no elements match role=None name='nothing'"
        )

    def test_click_follows_links_and_old_refs_go_stale(self):
        env = quiet_env(SEARCH)
        browse(env, action="navigate", url="/")
        box = ref_in(browse(env, action="find", role="textbox"))
        link = ref_in(browse(env, action="find", role="link", name="All items"))
        self.assertTrue(browse(env, action="click", ref=link).startswith(f"url: {ORIGIN}/items\n"))
        browse(env, action="type", ref=box, text="x")
        browse(env, action="navigate", url="/search?q=nut")
        self.assertEqual(
            browse(env, action="click", ref=box),
            f"error: stale or unknown ref {box}; take a new snapshot",
        )
        self.assertEqual(
            browse(env, action="click", ref="e99"),
            "error: stale or unknown ref e99; take a new snapshot",
        )
        self.assertEqual(browse(env, action="click"), "error: this action needs ref")

    def test_dialog_blocks_actions_until_dismissed(self):
        env = firing_env(SEARCH, "consent-overlay", "/")
        text = browse(env, action="navigate", url="/")
        self.assertEqual(env.events[-1].fault_id, "consent-overlay")
        self.assertIn('- dialog "Cookie consent"', text)
        link = ref_in(browse(env, action="find", role="link", name="All items"))
        box = ref_in(browse(env, action="find", role="textbox"))
        blocked = "error: action blocked by dialog 'Cookie consent'; dismiss it first"
        self.assertEqual(browse(env, action="click", ref=link), blocked)
        self.assertEqual(browse(env, action="type", ref=box, text="bolt"), blocked)
        accept = ref_in(browse(env, action="find", role="button", name="Accept cookies"))
        dismissed = browse(env, action="click", ref=accept)
        self.assertTrue(dismissed.startswith("dismissed dialog 'consent'\nurl: "))
        self.assertNotIn("- dialog", dismissed)
        link = ref_in(browse(env, action="find", role="link", name="All items"))
        self.assertTrue(browse(env, action="click", ref=link).startswith(f"url: {ORIGIN}/items\n"))

    def test_type_then_submit_honors_the_required_field(self):
        env = quiet_env(SEARCH)
        surface = env.surface(cv.SURFACE_BROWSER)
        browse(env, action="navigate", url="/")
        box = ref_in(browse(env, action="find", role="textbox", name="Search parts"))
        self.assertEqual(
            browse(env, action="submit", ref=box), "error: form 'search' requires field 'q'"
        )
        self.assertEqual(surface.state_view()["submitted"], [])
        self.assertEqual(
            browse(env, action="type", ref=box, text="bolt"),
            'typed into textbox "Search parts": bolt',
        )
        self.assertEqual(surface.state_view()["fields"], {"q": "bolt"})
        self.assertIn("[value='bolt']", browse(env, action="snapshot"))
        text = browse(env, action="submit", ref=box)
        self.assertTrue(text.startswith(f"url: {ORIGIN}/search?q=bolt\ntitle: Search results\n"))
        self.assertEqual(surface.state_view()["submitted"], ["search"])
        self.assertEqual(surface.state_view()["fields"], {})

    def test_the_submit_button_submits_its_enclosing_form(self):
        env = quiet_env(SEARCH)
        browse(env, action="navigate", url="/")
        heading = ref_in(browse(env, action="find", role="heading"))
        self.assertEqual(
            browse(env, action="submit", ref=heading), "error: no form encloses that element"
        )
        browse(
            env,
            action="type",
            ref=ref_in(browse(env, action="find", role="textbox")),
            text="hex bolt",
        )
        button = ref_in(browse(env, action="find", role="button", name="Run search"))
        text = browse(env, action="click", ref=button)
        self.assertTrue(text.startswith(f"url: {ORIGIN}/search?q=hex+bolt\n"))
        self.assertIn('- heading "Results for hex bolt"', text)

    def test_placeholders_render_from_the_query_string(self):
        text = browse(quiet_env(SEARCH), action="navigate", url="/search?q=washer")
        self.assertIn('- heading "Results for washer" [ref=e2]', text)
        self.assertIn('- text "Showing parts whose name contains washer."', text)

    def test_extract_logs_the_element_text(self):
        env = quiet_env(PRICE)
        browse(env, action="navigate", url="/items?page=2")
        cell = ref_in(browse(env, action="find", role="text", name="1.25"))
        row = ref_in(browse(env, action="find", role="row", name="HB-08"))
        self.assertEqual(browse(env, action="extract", ref=cell), "extracted: 1.25")
        self.assertEqual(
            browse(env, action="extract", ref=row), "extracted: Hex bolt M8 HB-08 1.25"
        )
        self.assertEqual(
            env.surface(cv.SURFACE_BROWSER).extracted, ["1.25", "Hex bolt M8 HB-08 1.25"]
        )

    def test_back_to_a_missing_page_shows_the_same_404_as_navigate(self):
        env = quiet_env(SEARCH)
        first = browse(env, action="navigate", url="/missing")
        self.assertIn("title: Page not found\n", first)
        browse(env, action="navigate", url="/")
        again = browse(env, action="back")
        self.assertEqual(without_refs(again), without_refs(first))
        self.assertNotEqual(again, first, "refs are never reused across page loads")

    def test_back_walks_the_history_one_page_at_a_time(self):
        env = quiet_env(PRICE)
        surface = env.surface(cv.SURFACE_BROWSER)
        self.assertEqual(browse(env, action="back"), "error: no page is open; navigate first")
        for url in ("/", "/items", "/items?page=2"):
            browse(env, action="navigate", url=url)
        self.assertTrue(
            browse(env, action="back").startswith(f"url: {ORIGIN}/items\ntitle: Parts list, page 1")
        )
        self.assertTrue(
            browse(env, action="back").startswith(f"url: {ORIGIN}/\ntitle: Parts catalog")
        )
        self.assertEqual(browse(env, action="back"), "error: no earlier page in history")
        self.assertEqual(surface.history, [])
        self.assertEqual(
            [item.removeprefix(ORIGIN) for item in surface.visited],
            ["/", "/items", "/items?page=2", "/items", "/"],
        )

    def test_selector_drift_renames_the_declared_text(self):
        env = firing_env(PRICE, "items-link-drift", "/")
        text = browse(env, action="navigate", url="/")
        self.assertEqual(env.events[-1].fault_id, "items-link-drift")
        self.assertIn('- link "Browse the item list"', text)
        self.assertNotIn("All items", text)
        self.assertEqual(
            browse(env, action="find", role="link", name="All items"),
            "no elements match role='link' name='All items'",
        )

    def test_not_found_fault_serves_the_404_page_once(self):
        env = firing_env(LEGACY, "page-two-not-found", "/items?page=2")
        text = browse(env, action="navigate", url="/items?page=2")
        self.assertEqual(env.events[-1].fault_id, "page-two-not-found")
        self.assertTrue(text.startswith(f"url: {ORIGIN}/items?page=2\ntitle: Page not found\n"))
        again = browse(env, action="navigate", url="/items?page=2")
        self.assertIsNone(env.events[-1].fault_id)
        self.assertIn("title: Parts list, page 2\n", again)

    def test_redirect_loop_fault_is_an_error_without_navigation(self):
        env = firing_env(LEGACY, "legacy-redirect-loop", "/catalog")
        self.assertEqual(
            browse(env, action="navigate", url="/catalog"),
            "error: redirect loop detected after 3 hops while loading /catalog",
        )
        self.assertEqual(env.events[-1].fault_id, "legacy-redirect-loop")
        self.assertEqual(env.surface(cv.SURFACE_BROWSER).state_view()["visited"], [])
        self.assertIn(f"url: {ORIGIN}/items\n", browse(env, action="navigate", url="/catalog"))

    def test_state_view_and_digests_are_deterministic(self):
        views, digests = [], []
        for _ in range(2):
            env = make_env(PACK, PRICE, 5)
            browse(env, action="navigate", url="/items?page=2")
            browse(
                env,
                action="extract",
                ref=ref_in(browse(env, action="find", role="text", name="0.95")),
            )
            views.append(env.surface(cv.SURFACE_BROWSER).state_view())
            digests.append(env.snapshot_digest())
        self.assertEqual(views[0], views[1])
        self.assertEqual(digests[0], digests[1])
        self.assertEqual(set(views[0]), {"url", "visited", "extracted", "submitted", "fields"})
        self.assertEqual(
            (views[0]["url"], views[0]["extracted"]), (f"{ORIGIN}/items?page=2", ["0.95"])
        )

    def test_identical_seeds_give_identical_observation_digests(self):
        for task_id in TASKS:
            first, second = gold_run(task_id, 7)[0], gold_run(task_id, 7)[0]
            self.assertEqual(
                [event.observation_sha256 for event in first.events],
                [event.observation_sha256 for event in second.events],
            )
            self.assertEqual(first.replay_digest(), second.replay_digest())
            self.assertEqual(first.snapshot_digest(), second.snapshot_digest())


class DeclaredEffectTests(unittest.TestCase):
    def setUp(self):
        self.surface = stub_surface()
        self.surface.execute("browser", {"action": "navigate", "url": "/"}, None)

    def press(self, name, role=None):
        query = (
            {"action": "find", "name": name, "role": role}
            if role
            else {"action": "find", "name": name}
        )
        ref = ref_in(self.surface.execute("browser", query, None))
        return self.surface.execute("browser", {"action": "click", "ref": ref}, None)

    def test_checkbox_and_toggle_effects_change_state(self):
        self.assertEqual(self.press("Option"), 'toggled checkbox "Option": checked')
        self.assertEqual(self.press("Option"), 'toggled checkbox "Option": unchecked')
        self.assertEqual(self.press("Panel"), "toggled panel: on")
        self.assertEqual(self.press("Panel"), "toggled panel: off")
        self.assertEqual(
            self.press("Ghost"), 'error: button "Ghost" targets missing element missing'
        )
        self.assertEqual(self.press("Plain"), 'error: button "Plain" has no declared effect')
        self.assertEqual(
            self.press("Effects", "heading"), "error: ref e2 (heading) is not clickable"
        )

    def test_next_and_navigate_effects_follow_the_pager(self):
        self.assertTrue(self.press("Older").startswith(f"url: {ORIGIN}/end\ntitle: End\n"))
        self.assertEqual(self.press("Older"), "error: no next page")
        self.surface.execute("browser", {"action": "back"}, None)
        self.assertTrue(self.press("Jump").startswith(f"url: {ORIGIN}/end\n"))


class SiteAndFaultCheckTests(unittest.TestCase):
    def test_a_pack_without_a_site_is_refused(self):
        with refusal(self, cv.FINDING_PACK_FIELD_INVALID, "pages/site.json"):
            browser_mod.BrowserSurface(
                type("NoSite", (), {"pack_id": "x", "site": None})(), _StubTask(), None
            )

    def test_every_malformed_site_shape_is_refused_with_a_code(self):
        for label, (site, needle) in BAD_SITES.items():
            with self.subTest(label), refusal(self, cv.FINDING_PACK_FIELD_INVALID, needle):
                stub_surface(site)

    def test_redirects_may_chain_and_land_on_a_page_with_a_query(self):
        surface = stub_surface({**SITE, "redirects": {"/a": "/b", "/b": "/end?x=1"}})
        text = surface.execute("browser", {"action": "navigate", "url": "/a"}, None)
        self.assertTrue(text.startswith(f"url: {ORIGIN}/end?x=1\ntitle: End\n"))

    def test_fault_kinds_and_overlay_params_are_checked(self):
        surface = stub_surface(OVERLAY_SITE, faults=[fault_spec()])
        surface.check_fault(fault_spec(kind="not_found", params={}))
        with refusal(self, cv.FINDING_FAULT_UNKNOWN, "timeout"):
            surface.check_fault(fault_spec(kind="timeout"))
        with refusal(self, cv.FINDING_TASK_FIELD_INVALID, "selector"):
            surface.check_fault(fault_spec(selector={"url": "/"}))
        for params in ({"overlay": "nope"}, {}, {"overlay": 5}):
            with self.subTest(params), refusal(self, cv.FINDING_TASK_FIELD_INVALID, "overlay"):
                stub_surface(OVERLAY_SITE, faults=[fault_spec(params=params)])
        with refusal(self, cv.FINDING_TASK_FIELD_INVALID, "params.overlay must name one of []"):
            stub_surface(faults=[fault_spec()])

    def test_overlay_is_inserted_into_the_dom_whatever_the_body_tag_carries(self):
        page = EFFECTS_PAGE.replace("<body>", '<body class="x" data-page="effects">')
        pages = {"page.html": page, "end.html": END_PAGE}
        surface = stub_surface(OVERLAY_SITE, pages, [fault_spec()])
        text = surface.execute(
            "browser", {"action": "navigate", "url": "/"}, scheduled(fault_spec())
        )
        lines = text.splitlines()
        self.assertEqual(
            lines[2:5],
            [
                '- text "Effects" [ref=e1]',
                '- dialog "Cookie consent" [ref=e11]',
                '  - button "Accept" [ref=e12]',
            ],
        )
        self.assertEqual(
            lines[5], '- heading "Effects" [ref=e2]', "existing refs survive an insert"
        )
        body = dom.body_of(surface.root)
        self.assertEqual(body.attrs, {"class": "x", "data-page": "effects"})
        self.assertIs(body.children[0].parent, body)
        self.assertEqual(
            surface.execute("browser", {"action": "click", "ref": "e4"}, None),
            "error: action blocked by dialog 'Cookie consent'; dismiss it first",
        )


class CatalogBrowserPackTests(unittest.TestCase):
    def test_pack_header_license_and_size(self):
        pack = load_pack(PACK)
        counter = load_strict_json((CATALOG_DIR / "counter-workspace" / "PACK.json").read_text())
        self.assertEqual(pack.surfaces, (cv.SURFACE_BROWSER,))
        self.assertEqual(pack.license, counter["license"])
        self.assertEqual({task.factory for task in pack.tasks}, {"tool-world-browser-factory"})
        self.assertEqual(sorted(task.task_id for task in pack.tasks), sorted(TASKS))
        total = sum(path.stat().st_size for path in pack.directory.rglob("*") if path.is_file())
        self.assertLess(total, 60_000)

    def test_tasks_cover_every_fault_kind_and_carry_no_hidden_reasoning(self):
        pack = load_pack(PACK)
        kinds = {spec.kind for task in pack.tasks for spec in task.faults}
        self.assertEqual(kinds, browser_mod.BrowserSurface.FAULT_KINDS)
        for path in sorted((pack.directory / "tasks").glob("*.json")):
            self.assertFalse(
                contains_hidden_reasoning_key(load_strict_json(path.read_text())), path.name
            )
        self.assertTrue(all(task.perturbations for task in pack.tasks))

    def test_gold_plans_succeed_for_the_sample_seeds(self):
        for task_id in TASKS:
            for seed in SAMPLE_SEEDS:
                env, trajectory = gold_run(task_id, seed)
                verdict = env.verdict()
                self.assertTrue(verdict["success"], (task_id, seed, verdict))
                self.assertFalse(trajectory.gave_up)
                self.assertLessEqual(len(trajectory.steps), env.task.max_steps)

    def test_every_fault_fires_and_is_recovered_in_a_gold_trajectory(self):
        for task in load_pack(PACK).tasks:
            for spec in task.faults:
                recovered = False
                for seed in range(60):
                    env, trajectory = gold_run(task.task_id, seed)
                    if spec.fault_id not in env.fault_engine.fired:
                        continue
                    self.assertTrue(env.verdict()["success"], (task.task_id, spec.fault_id, seed))
                    self.assertGreaterEqual(trajectory.faults_recovered, 1)
                    recovered = True
                    break
                self.assertTrue(recovered, f"{spec.fault_id} never fired in 60 gold seeds")

    def test_perturbed_variants_are_labelled_by_the_environment(self):
        env = make_env(PACK, LEGACY, firing_env(LEGACY, "legacy-redirect-loop", "/catalog").seed)
        trajectory = scripted.run(env, cv.PERTURBATION_GIVE_UP)
        self.assertTrue(trajectory.gave_up)
        self.assertIs(env.verdict()["success"], False)
        self.assertEqual(env.reported, scripted._GIVE_UP_TEXT)
        for task_id in (SEARCH, PRICE):
            env = quiet_env(task_id)
            scripted.run(env, cv.PERTURBATION_SKIP_VERIFICATION)
            verdict = env.verdict()
            self.assertFalse(verdict["success"])
            extracted = next(
                value for key, value in verdict["hidden"].items() if "extracted" in key
            )
            self.assertFalse(extracted)

    def test_wrong_arg_type_is_a_schema_error_the_gold_recovers_from(self):
        envs = (quiet_env(SEARCH), quiet_env(PRICE), make_env(PACK, LEGACY, 1))
        for env in envs:
            trajectory = scripted.run(env, cv.PERTURBATION_WRONG_ARG_TYPE)
            first = trajectory.steps[0]
            self.assertTrue(
                first.observation.startswith("error: invalid arguments for browser"), first
            )
            self.assertEqual((first.fault_id, env.events[0].fault_id), (None, None))
            self.assertEqual(first.tool_call["args"]["action"], 7)
            self.assertIs(env.verdict()["success"], True, env.task.task_id)
            self.assertEqual(len(env.events), len(trajectory.steps))

    def test_markers_appear_only_when_their_fault_fired(self):
        for task in load_pack(PACK).tasks:
            for seed in range(60):
                env, trajectory = gold_run(task.task_id, seed)
                quiet = [
                    spec for spec in task.faults if spec.fault_id not in env.fault_engine.fired
                ]
                for step in trajectory.steps:
                    for spec in quiet:
                        self.assertNotIn(
                            spec.marker, step.observation, (task.task_id, seed, spec.fault_id)
                        )

    def test_generate_and_replay_a_private_catalog_run(self):
        with tempfile.TemporaryDirectory() as temp:
            catalog_dir = private_catalog(Path(temp) / "catalog", (PACK,))
            out_dir = Path(temp) / "run"
            summary = generate.run(
                generate.RunRequest(
                    catalog_dir, out_dir, 1, 3, "tool-world-browser-factory", "all", PRODUCED_AT
                )
            )
            self.assertEqual((summary["records"], summary["accepted"]), (11, 3))
            golds = [row for row in summary["rows"] if row["variant"] == cv.VARIANT_GOLD]
            self.assertTrue(all(row["decision"] == cv.DECISION_ACCEPT for row in golds))
            report = replay.replay_run(out_dir, catalog_mod.load_catalog(catalog_dir))
            self.assertTrue(report["passed"], report)


if __name__ == "__main__":
    unittest.main()
