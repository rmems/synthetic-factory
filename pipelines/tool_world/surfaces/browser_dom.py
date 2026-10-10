#!/usr/bin/env python3
"""A deterministic DOM over ``html.parser`` and its accessibility snapshot.

The node tree, the parser and the structural queries live in
``browser_dom_tree``; roles, accessible names, refs and the snapshot in
``browser_dom_a11y``. This facade is the one namespace the surface reads the
DOM through; the tree's own structural helpers are reached on ``browser_dom_tree``.
"""

from .._contract import bind_import_twin
from .browser_dom_a11y import assign_refs, find, name_of, role_of, snapshot
from .browser_dom_tree import (
    Node,
    blocking_dialog,
    enclosing_form,
    form_inputs,
    next_link,
    parse_html,
    prepend_to_body,
    title_of,
)

__all__ = [
    "Node",
    "assign_refs",
    "blocking_dialog",
    "enclosing_form",
    "find",
    "form_inputs",
    "name_of",
    "next_link",
    "parse_html",
    "prepend_to_body",
    "role_of",
    "snapshot",
    "title_of",
]

bind_import_twin(__name__)
