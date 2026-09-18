"""Prove literal source behavior or select one independently pinned text projection."""

from __future__ import annotations

import ast
import hashlib
from itertools import takewhile

from ._contract import CsvRefusal, FINDING_SOURCE_NOT_PARSEABLE, LEGACY_SOURCE, bind_import_twin

# Independently hashed Git bytes at LEGACY_COMMIT, not caller-reported metadata.
_ARCHIVE_SHA256 = "98faa233ffe331fbd1d563c0aa3e190b48e40f18c5939939eab07d078d0ba570"
_SCRIPT_GUARD = ast.dump(ast.parse("__name__ == '__main__'", mode="eval").body)
_FUTURE_ANNOTATIONS = ast.dump(ast.parse("from __future__ import annotations").body[0])
_ANNOTATIONS = frozenset({"str", "int", "float", "bool", "list", "dict", "tuple", "set"})
SOURCE_PINS = frozenset({"PAIRS", "CATALOG_FIRST", "FAC", "FACTORY", "PREFIX"})
_RESERVED = frozenset({"__name__", "__builtins__"})


def _refuse(detail):
    raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, detail)


def _parse_source(text, source):
    if type(text) is not str or type(source) is not str:
        _refuse("catalog source and path must be plain strings")
    try:
        tree = ast.parse(text, filename="<catalog-source>")
        compile(tree, "<catalog-source>", "exec", dont_inherit=True)
        return tree
    except (SyntaxError, UnicodeError, RecursionError) as exc:
        raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}") from exc


def _is_future(node):
    return isinstance(node, ast.ImportFrom) and node.module == "__future__"


def _require_future_header(tree):
    start = int(ast.get_docstring(tree) is not None)
    allowed = set(takewhile(_is_future, tree.body[start:]))
    if any(_is_future(node) and node not in allowed for node in ast.walk(tree)):
        _refuse("future imports must occur in the original module header")


def source_statements(statements):
    """Exact script bodies defer; their import-time else branch remains active."""
    for node in statements:
        if isinstance(node, ast.If) and ast.dump(node.test) == _SCRIPT_GUARD:
            yield from source_statements(node.orelse)
        else:
            yield node


def literal_source_tree(text, source, dict_call):
    tree = _parse_source(text, source)
    _require_future_header(tree)
    archive = type(source) is str and source == LEGACY_SOURCE
    archive = archive and hashlib.sha256(text.encode("utf-8")).hexdigest() == _ARCHIVE_SHA256
    if not archive:
        proof = _LiteralStatements(dict_call)
        for node in source_statements(tree.body):
            proof.require(node)
    return tree


class _LiteralStatements:
    """Ordered binding proof for unpinned text; never run a recovered publisher."""

    def __init__(self, dict_call):
        self.dict_call = dict_call
        self.bound = set()

    def require(self, node):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            self._assignment(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._definition(node)
        elif not _inert(node):
            _refuse("unsupported module-time statement in literal catalog")

    def _assignment(self, node):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if len(targets) != 1 or not isinstance(targets[0], ast.Name):
            _refuse("literal assignments require one named target")
        name = targets[0].id
        if name in _RESERVED:
            _refuse(f"reserved module binding {name} is not a literal catalog")
        if isinstance(node, ast.AnnAssign):
            self._annotation(node.annotation)
        if node.value is not None:
            self._value(node.value)
            self.bound.add(name)

    def _definition(self, node):
        if node.name in SOURCE_PINS | _RESERVED:
            _refuse(f"definition overwrites catalog binding {node.name}")
        if node.decorator_list or getattr(node, "type_params", ()):
            _refuse("definition-time decorators or type parameters are not literal")
        self._arguments(node.args)
        self._annotation(node.returns)
        self.bound.add(node.name)

    def _arguments(self, arguments):
        for default in filter(None, [*arguments.defaults, *arguments.kw_defaults]):
            self._value(default)
        args = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs,
                arguments.vararg, arguments.kwarg]
        for arg in filter(None, args):
            self._annotation(arg.annotation)

    def _annotation(self, node):
        if node is None or isinstance(node, ast.Constant):
            return
        if self._annotation_name(node):
            return
        _refuse("unproven definition-time annotation in literal catalog")

    def _annotation_name(self, node):
        if not isinstance(node, ast.Name):
            return False
        return node.id in _ANNOTATIONS and node.id not in self.bound

    def _value(self, node):
        if isinstance(node, (ast.List, ast.Tuple)):
            for item in node.elts:
                self._value(item)
        elif isinstance(node, ast.Lambda):
            self._arguments(node.args)
        elif isinstance(node, ast.Call):
            self._constructor(node)
        else:
            _require_constant(node)

    def _constructor(self, node):
        if "dict" in self.bound:
            _refuse("dict constructor is shadowed")
        self.dict_call(node, "literal catalog")


def _require_constant(node):
    try:
        ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, RecursionError) as exc:
        raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, "unproven module-time expression") from exc


def _inert(node):
    if isinstance(node, ast.Pass):
        return True
    if isinstance(node, ast.Expr):
        return isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
    return ast.dump(node) == _FUTURE_ANNOTATIONS


bind_import_twin(__name__)
