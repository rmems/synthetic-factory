"""Count oracle test ids from suite files the grader controls.

A class counts when it subclasses ``unittest.TestCase`` directly, through an
import alias (``from unittest import TestCase as TC``), or through another
test class in the same file. Inherited ``test*`` methods are included, matching
what ``unittest`` collects from the class.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_ids")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_ids"
    )


def _imported_case_names(node: ast.stmt) -> set[str]:
    if not isinstance(node, ast.ImportFrom):
        return set()
    if node.module != "unittest":
        return set()
    names: set[str] = set()
    for alias in node.names:
        if alias.name == "TestCase":
            names.add(alias.asname or alias.name)
    return names


def _case_seeds(tree: ast.AST) -> set[str]:
    names = {"TestCase"}
    for node in tree.body:
        names |= _imported_case_names(node)
    return names


def _base_is_case(base: ast.expr, names: set[str]) -> bool:
    if isinstance(base, ast.Attribute):
        return base.attr == "TestCase"
    if isinstance(base, ast.Name):
        return base.id in names
    return False


def _extends_case(node: ast.ClassDef, names: set[str]) -> bool:
    for base in node.bases:
        if _base_is_case(base, names):
            return True
    return False


def _grow_cases(classes: dict[str, ast.ClassDef], found: set[str], seeds: set[str]) -> bool:
    grew = False
    known = seeds | found
    for name, node in classes.items():
        if name in found:
            continue
        if _extends_case(node, known):
            found.add(name)
            grew = True
    return grew


def _case_classes(classes: dict[str, ast.ClassDef], seeds: set[str]) -> set[str]:
    found: set[str] = set()
    for _ in range(len(classes)):
        if not _grow_cases(classes, found, seeds):
            return found
    return found


def _class_map(tree: ast.AST) -> dict[str, ast.ClassDef]:
    return {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}


def _test_name(item: ast.stmt) -> str:
    if not isinstance(item, ast.FunctionDef):
        return ""
    if item.name.startswith("test"):
        return item.name
    return ""


def _own_test_names(node: ast.ClassDef) -> set[str]:
    return {name for name in (_test_name(item) for item in node.body) if name}


def _inherited_names(node: ast.ClassDef, classes: dict[str, ast.ClassDef], seen: set[str]) -> set[str]:
    names = _own_test_names(node)
    for base in node.bases:
        if not isinstance(base, ast.Name):
            continue
        parent = classes.get(base.id)
        if parent is None:
            continue
        if base.id in seen:
            continue
        seen.add(base.id)
        names |= _inherited_names(parent, classes, seen)
    return names


def _ids_for(module_name: str, class_name: str, classes: dict[str, ast.ClassDef]) -> list[str]:
    methods = _inherited_names(classes[class_name], classes, {class_name})
    return [f"{module_name}.{class_name}.{name}" for name in sorted(methods)]


def declared_ids_from_text(text: str, filename: str, module_name: str) -> list[str]:
    """Return ``module.Class.method`` ids for source the grader already read."""

    tree = ast.parse(text, filename=filename)
    classes = _class_map(tree)
    cases = _case_classes(classes, _case_seeds(tree))
    ids: list[str] = []
    for name in sorted(cases):
        ids.extend(_ids_for(module_name, name, classes))
    return ids


def declared_test_ids(path: Path, module_name: str) -> list[str]:
    """Return ``module.Class.method`` ids for every collected test."""

    return declared_ids_from_text(path.read_text(encoding="utf-8"), str(path), module_name)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
