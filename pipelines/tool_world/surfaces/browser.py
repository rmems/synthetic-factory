#!/usr/bin/env python3
"""The browser surface: a static site navigated through one ``browser`` tool.

The pack's ``pages/site.json`` maps paths to page members, declares forms,
redirects, overlays, and drift renames (``browser_site``). Observations are
the URL, the title, and the accessibility snapshot of the current DOM
(``browser_dom``). Refs expire whenever the DOM changes; an action on an
expired ref is an error the agent must recover from by taking a new
snapshot. What a click does is what the page declared (``browser_effects``).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode

from .. import vocabulary as cv
from .._contract import bind_import_twin
from . import browser_dom as dom
from . import browser_effects, browser_site
from .base import Surface, ToolSpec, error_text

__all__ = ["BrowserSurface"]

FAULT_OVERLAY = "overlay"
FAULT_SELECTOR_DRIFT = "selector_drift"
FAULT_NOT_FOUND = "not_found"
FAULT_REDIRECT_LOOP = "redirect_loop"
_ACTIONS = ("navigate", "snapshot", "find", "click", "type", "submit", "extract", "back")
# The site checks and the click tables live with their siblings; the names stay readable here.
_check_site = browser_site.check_site
_check_members = browser_site.check_members
_check_redirects = browser_site.check_redirects
_CLICKS = browser_effects.CLICKS
_EFFECTS = browser_effects.EFFECTS


class BrowserSurface(Surface):
    NAME = cv.SURFACE_BROWSER
    FAULT_KINDS = frozenset(
        {FAULT_OVERLAY, FAULT_SELECTOR_DRIFT, FAULT_NOT_FOUND, FAULT_REDIRECT_LOOP}
    )

    def __init__(self, pack: Any, task: Any, env: Any) -> None:
        super().__init__(pack, task, env)
        self.site = browser_site.Site(pack)
        for spec in task.faults:
            if spec.surface == self.NAME:
                self.check_fault(spec)
        self.url = ""
        self.history: list[str] = []
        self.root: dom.Node | None = None
        self.refs: dict[str, dom.Node] = {}
        self.next_ref = 1
        self.fields: dict[str, str] = {}
        self.extracted: list[str] = []
        self.submitted: set[str] = set()
        self.visited: list[str] = []

    def check_fault(self, spec: Any) -> None:
        """Refuse a declared fault this surface could not turn into a symptom."""
        self.check_fault_kind(spec.kind)
        cv.refuse_when(
            spec.selector.get("action") != "navigate",
            cv.FINDING_TASK_FIELD_INVALID,
            f"fault {spec.fault_id}: browser faults fire on navigate, so the selector "
            "must pin action to navigate",
        )
        cv.refuse_when(
            spec.kind == FAULT_OVERLAY and not self.site.has_overlay(spec.params.get("overlay")),
            cv.FINDING_TASK_FIELD_INVALID,
            f"fault {spec.fault_id}: params.overlay must name one of {sorted(self.site.overlays)}",
        )

    def tools(self) -> tuple[ToolSpec, ...]:
        return (
            ToolSpec(
                cv.TOOL_BROWSER,
                self.NAME,
                "Drive the browser: navigate, snapshot, find, click, type, submit, extract, back.",
                {
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": {"type": "string", "enum": list(_ACTIONS)},
                        "url": {"type": "string"},
                        "ref": {"type": "string"},
                        "text": {"type": "string"},
                        "role": {"type": "string"},
                        "name": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                actions=_ACTIONS,
            ),
        )

    # --- dispatch ----------------------------------------------------------

    def execute(self, name: str, args: Mapping[str, Any], fault: Any) -> str:
        action = args["action"]
        kind = fault.spec.kind if fault is not None else None
        params = fault.spec.params if fault is not None else {}
        if action == "navigate":
            return self._navigate(args, kind, params)
        if self.root is None:
            return error_text("no page is open; navigate first")
        handlers = {
            "snapshot": self._snapshot,
            "find": self._find,
            "click": self._click,
            "type": self._type,
            "submit": self._submit,
            "extract": self._extract,
            "back": self._back,
        }
        return handlers[action](args)

    # --- navigation ----------------------------------------------------------

    def _navigate(
        self, args: Mapping[str, Any], kind: str | None, params: Mapping[str, Any]
    ) -> str:
        url = args.get("url")
        if not isinstance(url, str) or not url:
            return error_text("navigate needs url")
        path = self.site.path_of(url)
        if path is None:
            return error_text(f"navigation blocked: {url} is outside {self.site.origin}")
        if kind == FAULT_REDIRECT_LOOP:
            return error_text(
                f"redirect loop detected after {browser_site.MAX_REDIRECT_HOPS} hops "
                f"while loading {path}"
            )
        path, html = self.site.resolve(path, missing=kind == FAULT_NOT_FOUND)
        self._load(path, self.site.drifted(html) if kind == FAULT_SELECTOR_DRIFT else html)
        if kind == FAULT_OVERLAY:
            self._inject_overlay(params["overlay"])
        return self.page_text()

    def follow(self, url: str) -> str:
        """Navigate as a click does: no fault fires on a navigation the page itself started."""
        return self._navigate({"url": url}, None, {})

    def _inject_overlay(self, name: str) -> None:
        dom.prepend_to_body(self.root, dom.parse_html(self.site.overlays[name]))
        self.reindex()

    def _load(self, path: str, html: str) -> None:
        if self.url:
            self.history.append(self.url)
        self.url = self.site.origin + path
        self.visited.append(self.url)
        self.root = dom.parse_html(html)
        self.fields = {}
        self.reindex()

    def reindex(self) -> None:
        """Refresh the ref map; refs are never reused across pages or DOM revisions."""
        self.refs = dom.assign_refs(self.root, self.next_ref)
        highest = max((int(ref[1:]) for ref in self.refs), default=0)
        self.next_ref = max(self.next_ref, highest + 1)

    def page_text(self) -> str:
        """The observation of the open page: its url, its title, and the snapshot."""
        return f"url: {self.url}\ntitle: {dom.title_of(self.root)}\n{dom.snapshot(self.root)}"

    # --- actions -------------------------------------------------------------

    def _snapshot(self, _args: Mapping[str, Any]) -> str:
        return self.page_text()

    def _find(self, args: Mapping[str, Any]) -> str:
        role, name = args.get("role"), args.get("name")
        lines = dom.find(self.refs, role, name)
        if not lines:
            return f"no elements match role={role!r} name={name!r}"
        return "\n".join(lines)

    def _node(self, args: Mapping[str, Any]) -> tuple[dom.Node | None, str | None]:
        ref = args.get("ref")
        if not isinstance(ref, str) or not ref:
            return None, error_text("this action needs ref")
        node = self.refs.get(ref)
        if node is None:
            return None, error_text(f"stale or unknown ref {ref}; take a new snapshot")
        blocking = dom.blocking_dialog(self.root, node)
        if blocking is not None:
            name = dom.name_of(blocking, "dialog")
            return None, error_text(f"action blocked by dialog '{name}'; dismiss it first")
        return node, None

    def _click(self, args: Mapping[str, Any]) -> str:
        node, problem = self._node(args)
        if problem is not None:
            return problem
        role = dom.role_of(node)
        handler = _CLICKS.get(role)
        if handler is None:
            return error_text(f"ref {node.ref} ({role}) is not clickable")
        return handler(self, node)

    # --- forms, extraction, history -----------------------------------------

    def _type(self, args: Mapping[str, Any]) -> str:
        node, problem = self._node(args)
        if problem is not None:
            return problem
        if dom.role_of(node) != "textbox":
            return error_text(f"ref {node.ref} is not a textbox")
        text = args.get("text")
        if not isinstance(text, str):
            return error_text("type needs text")
        field = node.attrs.get("name") or dom.name_of(node, "textbox")
        self.fields[field] = text
        node.attrs["value"] = text
        return f'typed into textbox "{dom.name_of(node, "textbox")}": {text}'

    def _submit(self, args: Mapping[str, Any]) -> str:
        node, problem = self._node(args)
        if problem is not None:
            return problem
        return self.submit_form(dom.enclosing_form(node))

    def submit_form(self, form: dom.Node | None) -> str:
        """Submit ``form`` with the typed values: its action url carries them as the query."""
        if form is None:
            return error_text("no form encloses that element")
        form_id = form.attrs.get("id", "")
        fields = dom.form_inputs(form)
        missing = next((field for field in fields if self._lacks_required(field)), None)
        if missing is not None:
            return error_text(f"form '{form_id}' requires field '{missing.attrs['name']}'")
        self.submitted.add(form_id)
        action = form.attrs.get("action", self.site.path_of(self.url) or "/")
        return self.follow(self._submission_url(action, fields))

    def _submission_url(self, action: str, fields: list[dom.Node]) -> str:
        """The action url carrying the submitting fields as its query, when there are any."""
        values = [
            (field.attrs["name"], self._value_of(field)) for field in fields if _submits(field)
        ]
        return f"{action}?{urlencode(values)}" if values else action

    def _value_of(self, field: dom.Node) -> str:
        """What the field submits: the typed text, else the value its author gave it.

        A checkbox submits its declared value, even an empty one, or ``on``
        when it declares none, and only while it is checked (``_submits``).
        """
        if _is_checkbox(field):
            return field.attrs.get("value", "on")
        return self.fields.get(field.attrs["name"], field.attrs.get("value", ""))

    def _lacks_required(self, field: dom.Node) -> bool:
        """A required checkbox must be checked; any other required field must carry a value."""
        if "required" not in field.attrs:
            return False
        return not _submits(field) if _is_checkbox(field) else not self._value_of(field)

    def _extract(self, args: Mapping[str, Any]) -> str:
        node, problem = self._node(args)
        if problem is not None:
            return problem
        text = dom.name_of(node, dom.role_of(node))
        self.extracted.append(text)
        return f"extracted: {text}"

    def _back(self, _args: Mapping[str, Any]) -> str:
        if not self.history:
            return error_text("no earlier page in history")
        path, html = self.site.resolve(self.site.path_of(self.history.pop()) or "/", missing=False)
        self.url = ""
        self._load(path, html)
        return self.page_text()

    def state_view(self) -> Any:
        return {
            "url": self.url,
            "visited": list(self.visited),
            "extracted": list(self.extracted),
            "submitted": sorted(self.submitted),
            "fields": dict(sorted(self.fields.items())),
        }


def _is_checkbox(field: dom.Node) -> bool:
    return field.attrs.get("type") == "checkbox"


def _submits(field: dom.Node) -> bool:
    """Whether a form field takes part in the submission: a checkbox only while checked."""
    return not _is_checkbox(field) or "checked" in field.attrs


bind_import_twin(__name__)
