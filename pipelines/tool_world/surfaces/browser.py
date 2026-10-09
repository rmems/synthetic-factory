#!/usr/bin/env python3
"""The browser surface: a static site navigated through one ``browser`` tool.

The pack's ``pages/site.json`` maps paths to page members, declares forms,
redirects, overlays, and drift renames. Observations are the URL, the title,
and the accessibility snapshot of the current DOM. Refs expire whenever the
DOM changes; an action on an expired ref is an error the agent must recover
from by taking a new snapshot.
"""

from __future__ import annotations

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


class BrowserSurface(Surface):
    NAME = cv.SURFACE_BROWSER
    FAULT_KINDS = frozenset(
        {FAULT_OVERLAY, FAULT_SELECTOR_DRIFT, FAULT_NOT_FOUND, FAULT_REDIRECT_LOOP}
    )

    def __init__(self, pack: Any, task: Any, env: Any) -> None:
        super().__init__(pack, task, env)
        site = pack.site
        cv.refuse_when(
            not isinstance(site, Mapping)
            or not isinstance(site.get("origin"), str)
            or not isinstance(site.get("pages"), Mapping),
            cv.FINDING_PACK_FIELD_INVALID,
            f"pack {pack.pack_id} needs pages/site.json with origin and pages",
        )
        self.site = site
        self.origin = site["origin"].rstrip("/")
        self.url = ""
        self.history: list[str] = []
        self.root: dom.Node | None = None
        self.refs: dict[str, dom.Node] = {}
        self.fields: dict[str, str] = {}
        self.extracted: list[str] = []
        self.submitted: set[str] = set()
        self.visited: list[str] = []

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
            return error_text(f"redirect loop detected after 3 hops while loading {path}")
        redirects = self.site.get("redirects") or {}
        hops = 0
        while path in redirects and hops < 3:
            path, hops = redirects[path], hops + 1
        html = None if kind == FAULT_NOT_FOUND else self._page_html(path)
        if html is None:
            html = self.pack.pages.get(self.site.get("not_found", ""), _NOT_FOUND_HTML)
        if kind == FAULT_SELECTOR_DRIFT:
            for old, new in (self.site.get("drift") or {}).items():
                html = html.replace(old, new)
        if kind == FAULT_OVERLAY:
            overlay = (self.site.get("overlays") or {}).get(params.get("overlay", ""), "")
            html = html.replace("<body>", "<body>" + overlay, 1)
        self._load(path, html)
        return self._page_text()

    def _page_html(self, path: str) -> str | None:
        pages = self.site["pages"]
        bare, _, query = path.partition("?")
        member = pages.get(path) or pages.get(bare)
        if member is None:
            return None
        html = self.pack.pages.get(member)
        if html is None:
            return None
        for key, value in parse_qsl(query, keep_blank_values=True):
            html = html.replace("{{" + key + "}}", value)
        return html

    def _load(self, path: str, html: str) -> None:
        if self.url:
            self.history.append(self.url)
        self.url = self.origin + path
        self.visited.append(self.url)
        self.root = dom.parse_html(html)
        self.fields = {}
        self._reindex()

    def _reindex(self) -> None:
        self.refs = dom.assign_refs(self.root)

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
        if role == "link":
            return self._navigate({"url": node.attrs["href"]}, None, {})
        if role == "checkbox":
            if "checked" in node.attrs:
                del node.attrs["checked"]
            else:
                node.attrs["checked"] = ""
            return f'toggled checkbox "{dom.name_of(node, role)}": {"checked" if "checked" in node.attrs else "unchecked"}'
        if role == "button":
            return self._press(node)
        return error_text(f"ref {node.ref} ({role}) is not clickable")

    def _press(self, node: dom.Node) -> str:
        effect = node.attrs.get("data-effect", "")
        label = dom.name_of(node, "button")
        kind, _, target = effect.partition(":")
        if kind == "navigate":
            return self._navigate({"url": target}, None, {})
        if kind == "dismiss":
            dialog = self.root.find_id(target)
            if dialog is not None:
                dialog.remove()
            self._reindex()
            return f"dismissed dialog '{target}'\n{self._page_text()}"
        if kind == "toggle":
            element = self.root.find_id(target)
            if element is None:
                return error_text(f'button "{label}" targets missing element {target}')
            element.attrs["data-state"] = "off" if element.attrs.get("data-state") == "on" else "on"
            self._reindex()
            return f"toggled {target}: {element.attrs['data-state']}"
        if kind == "next":
            link = dom.next_link(self.root)
            if link is None:
                return error_text("no next page")
            return self._navigate({"url": link.attrs["href"]}, None, {})
        if kind == "submit" or node.attrs.get("type") == "submit":
            form = self.root.find_id(target) if target else dom.enclosing_form(node)
            return self._submit_form(form)
        return error_text(f'button "{label}" has no declared effect')

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
        previous = self.history.pop()
        path = self._path_of(previous) or "/"
        html = self._page_html(path) or _NOT_FOUND_HTML
        self.url = ""
        self._load(path, html)
        self.history.pop()
        return self._page_text()

    def state_view(self) -> Any:
        return {
            "url": self.url,
            "visited": list(self.visited),
            "extracted": list(self.extracted),
            "submitted": sorted(self.submitted),
            "fields": dict(sorted(self.fields.items())),
        }


bind_import_twin(__name__)
