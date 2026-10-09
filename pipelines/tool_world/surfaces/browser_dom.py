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


_ROLE_BY_TAG = {
    "button": "button",
    "textarea": "textbox",
    "form": "form",
    "tr": "row",
    **dict.fromkeys(_HEADINGS, "heading"),
}
_ROLE_BY_INPUT_TYPE = {
    **dict.fromkeys(_TEXTBOX_TYPES, "textbox"),
    "checkbox": "checkbox",
    "submit": "button",
}


def _link_role(node: Node) -> str | None:
    return "link" if "href" in node.attrs else None


def _input_role(node: Node) -> str | None:
    return _ROLE_BY_INPUT_TYPE.get(node.attrs.get("type", "text"))


def _text_role(node: Node) -> str | None:
    return "text" if node.direct_text() else None


def _tag_role(node: Node) -> str | None:
    return _ROLE_BY_TAG.get(node.tag)


_ROLE_RESOLVERS = {"a": _link_role, "input": _input_role, **dict.fromkeys(_TEXT_TAGS, _text_role)}


def role_of(node: Node) -> str | None:
    """The accessibility role an element is snapshotted under, or None for plain containers."""
    if node.attrs.get("role") == "dialog":
        return "dialog"
    return _ROLE_RESOLVERS.get(node.tag, _tag_role)(node)


def _label_or_id(node: Node) -> str:
    return node.attrs.get("aria-label") or node.attrs.get("id", "")


def _field_name(node: Node) -> str:
    attrs = node.attrs
    return attrs.get("aria-label") or attrs.get("placeholder") or attrs.get("name", "")


_NAME_BY_ROLE = {
    "dialog": _label_or_id,
    "form": _label_or_id,
    "textbox": _field_name,
    "checkbox": _field_name,
    "text": Node.direct_text,
}


def name_of(node: Node, role: str) -> str:
    """The accessible name: a label, placeholder, id, value, or the element's text."""
    if role == "button" and node.tag == "input":
        return node.attrs.get("value", "")
    return _NAME_BY_ROLE.get(role, Node.text)(node)


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
        elif role not in ("row", "heading", "link", "button"):
            _snapshot_into(child, lines, depth)


def dialogs(root: Node) -> list[Node]:
    return [node for node in root.walk() if node.attrs.get("role") == "dialog"]


def enclosing_form(node: Node) -> Node | None:
    if node.tag == "form":
        return node
    return next((ancestor for ancestor in node.ancestors() if ancestor.tag == "form"), None)


def inside(node: Node, container: Node) -> bool:
    return node is container or any(ancestor is container for ancestor in node.ancestors())


def body_of(root: Node) -> Node:
    """The body element, or the document itself when the page declares none."""
    return next((node for node in root.walk() if node.tag == "body"), root)


def prepend_to_body(root: Node, fragment: Node) -> None:
    """Move a parsed fragment's children to the front of the body, keeping their order."""
    body = body_of(root)
    for child in fragment.children:
        if isinstance(child, Node):
            child.parent = body
    body.children[:0] = fragment.children
    fragment.children = []


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
