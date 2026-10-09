#!/usr/bin/env python3
"""The browser DOM model: parsing, roles and names, refs, snapshots, and the form helpers."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_browser_support import FORM_PAGE, PACK, roles_of
from tool_world_test_support import load_pack

# The support modules go first: they put pipelines/ on sys.path for the import below.
# isort: split
from tool_world.surfaces import browser_dom as dom


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

    def test_a_label_names_its_field_before_the_placeholder(self):
        root = dom.parse_html(
            '<html><body><form id="f">'
            '<label for="a">Email address</label><input id="a" name="email" placeholder="you@x">'
            '<label>Nickname <input name="nick" placeholder="nick"></label>'
            '<label for="c">Ignored</label><input id="c" name="c" aria-label="Spoken">'
            '<label for="d">Dangling</label><input id="e" name="e" placeholder="Typed">'
            '<label><input type="checkbox" name="tos"> I agree</label>'
            "</form></body></html>"
        )
        fields = [node for node in root.walk() if node.tag == "input"]
        self.assertEqual(
            [dom.name_of(node, dom.role_of(node)) for node in fields],
            ["Email address", "Nickname", "Spoken", "Typed", "I agree"],
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


if __name__ == "__main__":
    unittest.main()
