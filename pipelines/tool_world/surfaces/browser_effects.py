#!/usr/bin/env python3
"""What a click does: by role, and by the ``data-effect`` a page author declared.

No script runs. A link follows its ``href``, a checkbox toggles, and a
button does exactly what its ``data-effect`` declares: ``navigate:<url>``,
``dismiss:<id>``, ``toggle:<id>``, ``next``, or ``submit[:<form id>]``. An
``<input type="submit">`` with no declared effect submits its enclosing
form. Every effect acts on the surface through the ``Host`` protocol.
"""

from __future__ import annotations

from typing import Protocol

from .._contract import bind_import_twin
from . import browser_dom as dom
from .base import error_text

__all__ = ["CLICKS", "EFFECTS", "Host"]


class Host(Protocol):
    """The surface a click acts on: its open DOM and the moves an effect may make."""

    root: dom.Node | None

    def follow(self, url: str) -> str: ...

    def reindex(self) -> None: ...

    def page_text(self) -> str: ...

    def submit_form(self, form: dom.Node | None) -> str: ...


def _follow_link(surface: Host, node: dom.Node) -> str:
    return surface.follow(node.attrs["href"])


def _toggle_checkbox(surface: Host, node: dom.Node) -> str:
    if "checked" in node.attrs:
        del node.attrs["checked"]
    else:
        node.attrs["checked"] = ""
    state = "checked" if "checked" in node.attrs else "unchecked"
    return f'toggled checkbox "{dom.name_of(node, "checkbox")}": {state}'


def _press(surface: Host, node: dom.Node) -> str:
    """Apply the button's declared effect; a submit input without one submits its form."""
    kind, _, target = node.attrs.get("data-effect", "").partition(":")
    if kind not in EFFECTS and node.attrs.get("type") == "submit":
        kind = "submit"
    handler = EFFECTS.get(kind)
    if handler is None:
        return error_text(f'button "{dom.name_of(node, "button")}" has no declared effect')
    return handler(surface, node, target)


def _navigate(surface: Host, node: dom.Node, target: str) -> str:
    return surface.follow(target)


def _dismiss(surface: Host, node: dom.Node, target: str) -> str:
    dialog = surface.root.find_id(target)
    if dialog is not None:
        dialog.remove()
    surface.reindex()
    return f"dismissed dialog '{target}'\n{surface.page_text()}"


def _toggle(surface: Host, node: dom.Node, target: str) -> str:
    element = surface.root.find_id(target)
    if element is None:
        label = dom.name_of(node, "button")
        return error_text(f'button "{label}" targets missing element {target}')
    element.attrs["data-state"] = "off" if element.attrs.get("data-state") == "on" else "on"
    surface.reindex()
    return f"toggled {target}: {element.attrs['data-state']}"


def _next(surface: Host, node: dom.Node, target: str) -> str:
    link = dom.next_link(surface.root)
    if link is None:
        return error_text("no next page")
    return surface.follow(link.attrs["href"])


def _submit(surface: Host, node: dom.Node, target: str) -> str:
    form = surface.root.find_id(target) if target else dom.enclosing_form(node)
    return surface.submit_form(form)


CLICKS = {"link": _follow_link, "checkbox": _toggle_checkbox, "button": _press}
EFFECTS = {
    "navigate": _navigate,
    "dismiss": _dismiss,
    "toggle": _toggle,
    "next": _next,
    "submit": _submit,
}


bind_import_twin(__name__)
