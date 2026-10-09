#!/usr/bin/env python3
"""The accessibility view of a browser DOM: roles, names, refs, and the snapshot.

The snapshot lists the elements an agent can act on or read, each with a
role, an accessible name, and a ``ref`` that is valid until the DOM changes.
A button's behavior is not part of the view: it is the ``data-effect``
attribute its author declared, applied by ``browser_effects``.
"""

from __future__ import annotations

from collections.abc import Mapping

from .._contract import bind_import_twin
from .browser_dom_tree import Node

__all__ = ["assign_refs", "find", "name_of", "role_of", "snapshot"]

_HEADINGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
_TEXT_TAGS = frozenset(
    {"p", "span", "li", "td", "th", "label", "div", "strong", "em", "code", "pre", "title"}
)
_TEXTBOX_TYPES = frozenset({"text", "search", "email", "password", "number", "url"})
# A container's children are listed one level deeper; a leaf's children are its name.
_CONTAINER_ROLES = frozenset({"dialog", "form"})
_LEAF_ROLES = frozenset({"row", "heading", "link", "button"})

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


def _checkbox_state(node: Node) -> str:
    return " [checked]" if "checked" in node.attrs else ""


def _button_state(node: Node) -> str:
    return f" [state={node.attrs['data-state']}]" if "data-state" in node.attrs else ""


def _textbox_state(node: Node) -> str:
    return f" [value={node.attrs['value']!r}]" if node.attrs.get("value") else ""


_STATE_BY_ROLE = {"checkbox": _checkbox_state, "button": _button_state, "textbox": _textbox_state}


def _state_of(node: Node, role: str) -> str:
    renderer = _STATE_BY_ROLE.get(role)
    return "" if renderer is None else renderer(node)


def _row_inside_header(node: Node) -> bool:
    return any(child.tag == "th" for child in node.children if isinstance(child, Node))


def _is_snapshotted(node: Node, role: str | None) -> bool:
    """Whether an element gets a ref: it has a role, and a row is not the table's header."""
    if role is None:
        return False
    return role != "row" or not _row_inside_header(node)


def assign_refs(root: Node, start: int = 1) -> dict[str, Node]:
    """The ref map of every snapshotted element, numbering new ones from ``start``.

    An element keeps its ref for as long as it is in the document and a number
    is never reused, so a ref from an earlier page or an earlier DOM revision
    is reported stale rather than resolving to a different element.
    """
    refs: dict[str, Node] = {}
    number = start
    for node in root.walk():
        if not _is_snapshotted(node, role_of(node)):
            node.ref = None
            continue
        if node.ref is None:
            node.ref = f"e{number}"
            number += 1
        refs[node.ref] = node
    return refs


def _entry(role: str, name: str, ref: str) -> str:
    return f'- {role} "{name}" [ref={ref}]'


def snapshot(root: Node) -> str:
    lines: list[str] = []
    _snapshot_into(root, lines, 0)
    return "\n".join(lines) if lines else "(empty page)"


def _snapshot_into(node: Node, lines: list[str], depth: int) -> None:
    for child in node.children:
        if isinstance(child, Node):
            _snapshot_node(child, lines, depth)


def _snapshot_node(node: Node, lines: list[str], depth: int) -> None:
    role = role_of(node)
    if role is None or node.ref is None:
        _snapshot_into(node, lines, depth)
        return
    lines.append(
        f"{'  ' * depth}{_entry(role, name_of(node, role), node.ref)}{_state_of(node, role)}"
    )
    if role in _CONTAINER_ROLES:
        _snapshot_into(node, lines, depth + 1)
    elif role not in _LEAF_ROLES:
        _snapshot_into(node, lines, depth)


def find(refs: Mapping[str, Node], role: str | None, name: str | None) -> list[str]:
    """Snapshot entries of the refs with ``role`` (any when None) whose name contains ``name``."""
    needle = (name or "").casefold()
    lines = []
    for ref, node in refs.items():
        node_role = role_of(node)
        node_name = name_of(node, node_role)
        if _matches(node_role, node_name, role, needle):
            lines.append(_entry(node_role, node_name, ref))
    return lines


def _matches(node_role: str | None, node_name: str, role: str | None, needle: str) -> bool:
    if role is not None and node_role != role:
        return False
    return not needle or needle in node_name.casefold()


bind_import_twin(__name__)
