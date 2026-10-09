#!/usr/bin/env python3
"""The browser surface: navigation, refs and actions, declared effects, and site checks."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_browser_support import (
    BAD_SITES,
    EFFECTS_PAGE,
    END_PAGE,
    LEGACY,
    ORIGIN,
    OVERLAY_SITE,
    PACK,
    PRICE,
    SEARCH,
    SITE,
    TASKS,
    StubTask,
    browse,
    fault_spec,
    firing_env,
    gold_run,
    quiet_env,
    ref_in,
    scheduled,
    stub_surface,
    without_refs,
)
from tool_world_test_support import cv, make_env, refusal

# The support modules go first: they put pipelines/ on sys.path for the imports below.
# isort: split
from tool_world.surfaces import browser as browser_mod
from tool_world.surfaces import browser_dom as dom


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
                type("NoSite", (), {"pack_id": "x", "site": None})(), StubTask(), None
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


if __name__ == "__main__":
    unittest.main()
