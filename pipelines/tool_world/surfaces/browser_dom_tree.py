#!/usr/bin/env python3
"""The browser DOM tree: ``html.parser`` nodes and the structural queries over them.

Pages are static pack members, so the tree is exactly what the author wrote:
elements with their attributes, text runs, and the ``ref`` the accessibility
pass (``browser_dom_a11y``) assigns to each element an agent can act on. No
script runs; nothing here changes a page except the surface's own edits.
"""

from __future__ import annotations

from collections.abc import Iterator
from html.parser import HTMLParser

from .._contract import bind_import_twin

__all__ = [
    "Node",
    "blocking_dialog",
    "body_of",
    "dialogs",
    "enclosing_form",
    "form_inputs",
    "inside",
    "next_link",
    "parse_html",
    "prepend_to_body",
    "title_of",
]

_VOID = frozenset({"input", "br", "img", "meta", "link", "hr"})


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


def dialogs(root: Node) -> list[Node]:
    return [node for node in root.walk() if node.attrs.get("role") == "dialog"]


def blocking_dialog(root: Node, node: Node) -> Node | None:
    """The open dialog that blocks actions on ``node``: any dialog the node is not inside."""
    return next((dialog for dialog in dialogs(root) if not inside(node, dialog)), None)


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


bind_import_twin(__name__)
