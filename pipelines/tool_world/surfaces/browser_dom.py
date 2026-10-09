#!/usr/bin/env python3
"""A deterministic DOM over ``html.parser`` and its accessibility snapshot.

Pages are static pack members. The snapshot lists the elements an agent can
act on or read, each with a role, an accessible name, and a ``ref`` that is
valid until the DOM changes. No script runs; a button's behavior is the
``data-effect`` attribute its author declared.
"""

from __future__ import annotations

from collections.abc import Iterator
from html.parser import HTMLParser
from typing import Any

from .._contract import bind_import_twin

__all__ = ["Node", "parse_html", "snapshot"]

_VOID = frozenset({"input", "br", "img", "meta", "link", "hr"})
_HEADINGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
_TEXT_TAGS = frozenset(
    {"p", "span", "li", "td", "th", "label", "div", "strong", "em", "code", "pre", "title"}
)
_TEXTBOX_TYPES = frozenset({"text", "search", "email", "password", "number", "url"})


class Node:
    __slots__ = ("attrs", "children", "parent", "ref", "tag")

    def __init__(self, tag: str, attrs: dict[str, str], parent: Node | None) -> None:
        self.tag = tag
        self.attrs = attrs
        self.children: list[Node | str] = []
        self.parent = parent
        self.ref: str | None = None

    def text(self) -> str:
        parts = []
        for child in self.children:
            parts.append(child if isinstance(child, str) else child.text())
        return " ".join(" ".join(parts).split())

    def direct_text(self) -> str:
        return " ".join(
            " ".join(child for child in self.children if isinstance(child, str)).split()
        )

    def walk(self) -> Iterator[Node]:
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def find_id(self, identifier: str) -> Node | None:
        return next((node for node in self.walk() if node.attrs.get("id") == identifier), None)

    def ancestors(self) -> Iterator[Node]:
        current = self.parent
        while current is not None:
            yield current
            current = current.parent

    def remove(self) -> None:
        if self.parent is not None:
            self.parent.children = [child for child in self.parent.children if child is not self]


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {}, None)
        self.current = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, {key: value or "" for key, value in attrs}, self.current)
        self.current.children.append(node)
        if tag not in _VOID:
            self.current = node

    def handle_endtag(self, tag: str) -> None:
        node = self.current
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self.current = node.parent

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.current.children.append(data)


def parse_html(html: str) -> Node:
    builder = _TreeBuilder()
    builder.feed(html)
    builder.close()
    return builder.root


def role_of(node: Node) -> str | None:
    """The accessibility role an element is snapshotted under, or None for plain containers."""
    tag, attrs = node.tag, node.attrs
    if attrs.get("role") == "dialog":
        return "dialog"
    if tag == "a" and "href" in attrs:
        return "link"
    if tag == "button":
        return "button"
    if tag == "input":
        kind = attrs.get("type", "text")
        if kind in _TEXTBOX_TYPES:
            return "textbox"
        if kind == "checkbox":
            return "checkbox"
        if kind == "submit":
            return "button"
        return None
    if tag == "textarea":
        return "textbox"
    if tag == "form":
        return "form"
    if tag in _HEADINGS:
        return "heading"
    if tag == "tr":
        return "row"
    if tag in _TEXT_TAGS and node.direct_text():
        return "text"
    return None


def name_of(node: Node, role: str) -> str:
    attrs = node.attrs
    if role == "dialog":
        return attrs.get("aria-label") or attrs.get("id", "")
    if role == "form":
        return attrs.get("aria-label") or attrs.get("id", "")
    if role in ("textbox", "checkbox"):
        return attrs.get("aria-label") or attrs.get("placeholder") or attrs.get("name", "")
    if role == "button" and node.tag == "input":
        return attrs.get("value", "")
    if role == "text":
        return node.direct_text()
    return node.text()


def _state_of(node: Node, role: str) -> str:
    if role == "checkbox":
        return " [checked]" if "checked" in node.attrs else ""
    if role == "button" and "data-state" in node.attrs:
        return f" [state={node.attrs['data-state']}]"
    if role == "textbox" and node.attrs.get("value"):
        return f" [value={node.attrs['value']!r}]"
    return ""


def assign_refs(root: Node) -> dict[str, Node]:
    """Number every snapshotted element in document order; returns the ref map."""
    refs: dict[str, Node] = {}
    for node in root.walk():
        node.ref = None
        role = role_of(node)
        if role is not None and not (role == "row" and _row_inside_header(node)):
            node.ref = f"e{len(refs) + 1}"
            refs[node.ref] = node
    return refs


def _row_inside_header(node: Node) -> bool:
    return any(child.tag == "th" for child in node.children if isinstance(child, Node))


def snapshot(root: Node) -> str:
    lines: list[str] = []
    _snapshot_into(root, lines, 0)
    return "\n".join(lines) if lines else "(empty page)"


def _snapshot_into(node: Node, lines: list[str], depth: int) -> None:
    for child in node.children:
        if not isinstance(child, Node):
            continue
        role = role_of(child)
        if role is None or child.ref is None:
            _snapshot_into(child, lines, depth)
            continue
        name = name_of(child, role)
        lines.append(f'{"  " * depth}- {role} "{name}" [ref={child.ref}]{_state_of(child, role)}')
        if role in ("dialog", "form"):
            _snapshot_into(child, lines, depth + 1)
        elif role not in ("text", "row", "heading", "link", "button"):
            _snapshot_into(child, lines, depth)


def dialogs(root: Node) -> list[Node]:
    return [node for node in root.walk() if node.attrs.get("role") == "dialog"]


def enclosing_form(node: Node) -> Node | None:
    if node.tag == "form":
        return node
    return next((ancestor for ancestor in node.ancestors() if ancestor.tag == "form"), None)


def inside(node: Node, container: Node) -> bool:
    return node is container or any(ancestor is container for ancestor in node.ancestors())


def title_of(root: Node) -> str:
    node = next((item for item in root.walk() if item.tag == "title"), None)
    return node.text() if node is not None else ""


def next_link(root: Node) -> Node | None:
    return next(
        (item for item in root.walk() if item.tag == "a" and item.attrs.get("rel") == "next"), None
    )


def form_inputs(form: Node) -> list[Node]:
    return [
        item for item in form.walk() if item.tag in ("input", "textarea") and item.attrs.get("name")
    ]


def unused(_value: Any) -> None:
    """Keep the module's public helpers referenced for linters that scan star imports."""


bind_import_twin(__name__)
