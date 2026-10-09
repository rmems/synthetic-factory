#!/usr/bin/env python3
"""The browser surface: a static site navigated through one ``browser`` tool.

The pack's ``pages/site.json`` maps paths to page members, declares forms,
redirects, overlays, and drift renames. Observations are the URL, the title,
and the accessibility snapshot of the current DOM. Refs expire whenever the
DOM changes; an action on an expired ref is an error the agent must recover
from by taking a new snapshot.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit

from .. import vocabulary as cv
from .._contract import bind_import_twin
from . import browser_dom as dom
from .base import Surface, ToolSpec, error_text

__all__ = ["BrowserSurface"]

FAULT_OVERLAY = "overlay"
FAULT_SELECTOR_DRIFT = "selector_drift"
FAULT_NOT_FOUND = "not_found"
FAULT_REDIRECT_LOOP = "redirect_loop"
_ACTIONS = ("navigate", "snapshot", "find", "click", "type", "submit", "extract", "back")
_NOT_FOUND_HTML = (
    "<html><head><title>404 Not Found</title></head><body><h1>404 Not Found</h1>"
    "<p>The page does not exist.</p></body></html>"
)
_ORIGIN_RE = re.compile(r"^[a-z][a-z0-9+.-]*://[^/?#]+$")
_SITE_TABLES = ("pages", "redirects", "overlays", "drift")
_MAX_REDIRECT_HOPS = 3


def _is_text_table(value: Any) -> bool:
    return isinstance(value, Mapping) and all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    )


def _check_site(pack: Any) -> None:
    """Refuse a ``pages/site.json`` the surface could not serve exactly as written."""
    site, where = pack.site, f"pack {pack.pack_id}"
    cv.refuse_when(
        not isinstance(site, Mapping),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: needs pages/site.json with origin and pages",
    )
    origin = site.get("origin")
    cv.refuse_when(
        not isinstance(origin, str) or _ORIGIN_RE.match(origin) is None,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: origin must be scheme://host with no path",
    )
    for key in _SITE_TABLES:
        cv.refuse_when(
            not _is_text_table(site.get(key, {})),
            cv.FINDING_PACK_FIELD_INVALID,
            f"{where}: {key} must map strings to strings",
        )
    _check_members(site, pack.pages, where)
    _check_redirects(site, where)


def _check_members(site: Mapping[str, Any], pages: Mapping[str, str], where: str) -> None:
    not_found = site.get("not_found")
    cv.refuse_when(
        not_found is not None and not isinstance(not_found, str),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: not_found must name a page member",
    )
    members = list(site["pages"].values()) + ([] if not_found is None else [not_found])
    missing = sorted(member for member in members if member not in pages)
    cv.refuse_when(
        bool(missing),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: site names missing page members {missing}",
    )


def _check_redirects(site: Mapping[str, Any], where: str) -> None:
    redirects = site.get("redirects", {})
    pages = site["pages"]
    dangling = sorted(
        target
        for target in redirects.values()
        if target not in redirects and target not in pages and target.partition("?")[0] not in pages
    )
    cv.refuse_when(
        bool(dangling),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: redirects lead to undeclared paths {dangling}",
    )


class BrowserSurface(Surface):
    NAME = cv.SURFACE_BROWSER
    FAULT_KINDS = frozenset(
        {FAULT_OVERLAY, FAULT_SELECTOR_DRIFT, FAULT_NOT_FOUND, FAULT_REDIRECT_LOOP}
    )

    def __init__(self, pack: Any, task: Any, env: Any) -> None:
        super().__init__(pack, task, env)
        _check_site(pack)
        self.site = pack.site
        self.origin = self.site["origin"]
        self.redirects = dict(self.site.get("redirects", {}))
        self.overlays = dict(self.site.get("overlays", {}))
        self.drift = dict(self.site.get("drift", {}))
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
        overlay = spec.params.get("overlay")
        cv.refuse_when(
            spec.kind == FAULT_OVERLAY
            and (not isinstance(overlay, str) or overlay not in self.overlays),
            cv.FINDING_TASK_FIELD_INVALID,
            f"fault {spec.fault_id}: params.overlay must name one of {sorted(self.overlays)}",
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

    def _path_of(self, url: str) -> str | None:
        parts = urlsplit(url)
        if (parts.scheme or parts.netloc) and f"{parts.scheme}://{parts.netloc}" != self.origin:
            return None
        path = parts.path or "/"
        return path + (f"?{parts.query}" if parts.query else "")

    def _navigate(
        self, args: Mapping[str, Any], kind: str | None, params: Mapping[str, Any]
    ) -> str:
        url = args.get("url")
        if not isinstance(url, str) or not url:
            return error_text("navigate needs url")
        path = self._path_of(url)
        if path is None:
            return error_text(f"navigation blocked: {url} is outside {self.origin}")
        if kind == FAULT_REDIRECT_LOOP:
            return error_text(
                f"redirect loop detected after {_MAX_REDIRECT_HOPS} hops while loading {path}"
            )
        path, html = self._resolve(path, missing=kind == FAULT_NOT_FOUND)
        self._load(path, self._drifted(html) if kind == FAULT_SELECTOR_DRIFT else html)
        if kind == FAULT_OVERLAY:
            self._inject_overlay(params["overlay"])
        return self._page_text()

    def _resolve(self, path: str, *, missing: bool) -> tuple[str, str]:
        """Follow the declared redirect hops; the page html, or the not-found page."""
        hops = 0
        while path in self.redirects and hops < _MAX_REDIRECT_HOPS:
            path, hops = self.redirects[path], hops + 1
        html = None if missing else self._page_html(path)
        return path, self._not_found_html() if html is None else html

    def _page_html(self, path: str) -> str | None:
        pages = self.site["pages"]
        bare, _, query = path.partition("?")
        member = pages.get(path) or pages.get(bare)
        if member is None:
            return None
        html = self.pack.pages[member]
        for key, value in parse_qsl(query, keep_blank_values=True):
            html = html.replace("{{" + key + "}}", value)
        return html

    def _not_found_html(self) -> str:
        """The pack's declared not-found page, or the built-in one."""
        member = self.site.get("not_found")
        return _NOT_FOUND_HTML if member is None else self.pack.pages[member]

    def _drifted(self, html: str) -> str:
        for old, new in self.drift.items():
            html = html.replace(old, new)
        return html

    def _inject_overlay(self, name: str) -> None:
        dom.prepend_to_body(self.root, dom.parse_html(self.overlays[name]))
        self._reindex()

    def _load(self, path: str, html: str) -> None:
        if self.url:
            self.history.append(self.url)
        self.url = self.origin + path
        self.visited.append(self.url)
        self.root = dom.parse_html(html)
        self.fields = {}
        self._reindex()

    def _reindex(self) -> None:
        """Refresh the ref map; refs are never reused across pages or DOM revisions."""
        self.refs = dom.assign_refs(self.root, self.next_ref)
        self.next_ref = max((int(ref[1:]) for ref in self.refs), default=self.next_ref - 1) + 1

    def _page_text(self) -> str:
        return f"url: {self.url}\ntitle: {dom.title_of(self.root)}\n{dom.snapshot(self.root)}"

    # --- actions -------------------------------------------------------------

    def _snapshot(self, args: Mapping[str, Any]) -> str:
        return self._page_text()

    def _find(self, args: Mapping[str, Any]) -> str:
        role, needle = args.get("role"), (args.get("name") or "").casefold()
        lines = []
        for ref, node in self.refs.items():
            node_role = dom.role_of(node)
            name = dom.name_of(node, node_role)
            if role is not None and node_role != role:
                continue
            if needle and needle not in name.casefold():
                continue
            lines.append(f'- {node_role} "{name}" [ref={ref}]')
        if not lines:
            return f"no elements match role={role!r} name={args.get('name')!r}"
        return "\n".join(lines)

    def _node(self, args: Mapping[str, Any]) -> tuple[dom.Node | None, str | None]:
        ref = args.get("ref")
        if not isinstance(ref, str) or not ref:
            return None, error_text("this action needs ref")
        node = self.refs.get(ref)
        if node is None:
            return None, error_text(f"stale or unknown ref {ref}; take a new snapshot")
        blocking = next(
            (dialog for dialog in dom.dialogs(self.root) if not dom.inside(node, dialog)), None
        )
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

    def _follow_link(self, node: dom.Node) -> str:
        return self._navigate({"url": node.attrs["href"]}, None, {})

    @staticmethod
    def _toggle_checkbox(node: dom.Node) -> str:
        if "checked" in node.attrs:
            del node.attrs["checked"]
        else:
            node.attrs["checked"] = ""
        state = "checked" if "checked" in node.attrs else "unchecked"
        return f'toggled checkbox "{dom.name_of(node, "checkbox")}": {state}'

    # --- declared button effects ---------------------------------------------

    def _press(self, node: dom.Node) -> str:
        kind, _, target = node.attrs.get("data-effect", "").partition(":")
        if kind not in _EFFECTS and node.attrs.get("type") == "submit":
            kind = "submit"
        handler = _EFFECTS.get(kind)
        if handler is None:
            return error_text(f'button "{dom.name_of(node, "button")}" has no declared effect')
        return handler(self, node, target)

    def _effect_navigate(self, node: dom.Node, target: str) -> str:
        return self._navigate({"url": target}, None, {})

    def _effect_dismiss(self, node: dom.Node, target: str) -> str:
        dialog = self.root.find_id(target)
        if dialog is not None:
            dialog.remove()
        self._reindex()
        return f"dismissed dialog '{target}'\n{self._page_text()}"

    def _effect_toggle(self, node: dom.Node, target: str) -> str:
        element = self.root.find_id(target)
        if element is None:
            label = dom.name_of(node, "button")
            return error_text(f'button "{label}" targets missing element {target}')
        element.attrs["data-state"] = "off" if element.attrs.get("data-state") == "on" else "on"
        self._reindex()
        return f"toggled {target}: {element.attrs['data-state']}"

    def _effect_next(self, node: dom.Node, target: str) -> str:
        link = dom.next_link(self.root)
        if link is None:
            return error_text("no next page")
        return self._navigate({"url": link.attrs["href"]}, None, {})

    def _effect_submit(self, node: dom.Node, target: str) -> str:
        form = self.root.find_id(target) if target else dom.enclosing_form(node)
        return self._submit_form(form)

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
        return self._submit_form(dom.enclosing_form(node))

    def _submit_form(self, form: dom.Node | None) -> str:
        if form is None:
            return error_text("no form encloses that element")
        form_id = form.attrs.get("id", "")
        values = []
        for field in dom.form_inputs(form):
            name = field.attrs["name"]
            value = self.fields.get(name, field.attrs.get("value", ""))
            if "required" in field.attrs and not value:
                return error_text(f"form '{form_id}' requires field '{name}'")
            values.append((name, value))
        self.submitted.add(form_id)
        action = form.attrs.get("action", self._path_of(self.url) or "/")
        return self._navigate(
            {"url": f"{action}?{urlencode(values)}" if values else action}, None, {}
        )

    def _extract(self, args: Mapping[str, Any]) -> str:
        node, problem = self._node(args)
        if problem is not None:
            return problem
        text = dom.name_of(node, dom.role_of(node))
        self.extracted.append(text)
        return f"extracted: {text}"

    def _back(self, args: Mapping[str, Any]) -> str:
        if not self.history:
            return error_text("no earlier page in history")
        path, html = self._resolve(self._path_of(self.history.pop()) or "/", missing=False)
        self.url = ""
        self._load(path, html)
        return self._page_text()

    def state_view(self) -> Any:
        return {
            "url": self.url,
            "visited": list(self.visited),
            "extracted": list(self.extracted),
            "submitted": sorted(self.submitted),
            "fields": dict(sorted(self.fields.items())),
        }


_CLICKS = {
    "link": BrowserSurface._follow_link,
    "checkbox": lambda surface, node: surface._toggle_checkbox(node),
    "button": BrowserSurface._press,
}
_EFFECTS = {
    "navigate": BrowserSurface._effect_navigate,
    "dismiss": BrowserSurface._effect_dismiss,
    "toggle": BrowserSurface._effect_toggle,
    "next": BrowserSurface._effect_next,
    "submit": BrowserSurface._effect_submit,
}


bind_import_twin(__name__)
