#!/usr/bin/env python3
"""Bind CST catalog constructors and assignments without calling ``exec``.

Constructor bodies are compiled and called. Only the catalog subset below is
evaluated: constants, names, lists, tuples, dicts, calls, ``+``, and a
single-target list comprehension. Keyword-only defaults are kept. Anything
else raises ``ValueError`` before a catalog record is built.
"""

from __future__ import annotations

import ast
import types
from collections.abc import Callable
from typing import Any

_MISSING = object()
_UNSUPPORTED_COMPREHENSION = "unsupported catalog comprehension"
_Evaluator = Callable[[ast.expr, dict[str, Any], dict[str, Any]], Any]


def define_constructor(
    node: ast.FunctionDef,
    filename: str,
    globals_ns: dict[str, Any],
    namespace: dict[str, Any],
) -> None:
    """Bind ``node`` after its defaults, into both namespaces."""

    if node.decorator_list:
        raise ValueError("unsupported catalog decorator")
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    code = compile(module, filename, "exec")
    defaults = tuple(_eval_expr(item, namespace, globals_ns) for item in node.args.defaults)
    function = types.FunctionType(
        _function_code(code, node.name), globals_ns, node.name, defaults or None
    )
    keywords = _keyword_defaults(node, namespace, globals_ns)
    if keywords:
        function.__kwdefaults__ = keywords
    globals_ns[node.name] = function
    namespace[node.name] = function


def bind_catalog_assignment(
    node: ast.stmt, namespace: dict[str, Any], globals_ns: dict[str, Any]
) -> None:
    value_node = _assigned_value(node)
    if value_node is None:
        return
    value = _eval_expr(value_node, namespace, globals_ns)
    for name in assignment_names(node):
        namespace[name] = value


def assignment_names(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
        return [target.id for target in node.targets if isinstance(target, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def _assigned_value(node: ast.stmt) -> ast.expr | None:
    if isinstance(node, ast.Assign):
        return node.value
    if isinstance(node, ast.AnnAssign):
        return node.value
    return None


def _function_code(code: types.CodeType, name: str) -> types.CodeType:
    for item in code.co_consts:
        if _is_named_code(item, name):
            return item
    raise ValueError(f"missing compiled function {name}")


def _is_named_code(item: object, name: str) -> bool:
    if not isinstance(item, types.CodeType):
        return False
    return item.co_name == name


def _keyword_defaults(
    node: ast.FunctionDef, namespace: dict[str, Any], globals_ns: dict[str, Any]
) -> dict[str, Any]:
    bound: dict[str, Any] = {}
    pairs = zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True)
    for arg, default in pairs:
        if default is None:
            continue
        bound[arg.arg] = _eval_expr(default, namespace, globals_ns)
    return bound


def _lookup(name: str, namespace: dict[str, Any], globals_ns: dict[str, Any]) -> Any:
    if name in namespace:
        return namespace[name]
    if _in_globals(name, globals_ns):
        return globals_ns[name]
    found = _builtin(name, globals_ns)
    if found is not _MISSING:
        return found
    raise NameError(name)


def _in_globals(name: str, globals_ns: dict[str, Any]) -> bool:
    if name == "__builtins__":
        return False
    return name in globals_ns


def _builtin(name: str, globals_ns: dict[str, Any]) -> Any:
    builtins = globals_ns.get("__builtins__")
    if not isinstance(builtins, dict):
        return _MISSING
    if name not in builtins:
        return _MISSING
    return builtins[name]


def _eval_expr(node: ast.expr, namespace: dict[str, Any], globals_ns: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    for kind, evaluator in _EVALUATORS:
        if isinstance(node, kind):
            return evaluator(node, namespace, globals_ns)
    raise ValueError(f"unsupported catalog expression: {type(node).__name__}")


def _eval_name(node: ast.expr, namespace: dict[str, Any], globals_ns: dict[str, Any]) -> Any:
    if not isinstance(node, ast.Name):
        raise ValueError("unsupported catalog expression: Name")
    return _lookup(node.id, namespace, globals_ns)


def _eval_list(node: ast.expr, namespace: dict[str, Any], globals_ns: dict[str, Any]) -> list[Any]:
    if not isinstance(node, ast.List):
        raise ValueError("unsupported catalog expression: List")
    return [_eval_expr(item, namespace, globals_ns) for item in node.elts]


def _eval_tuple(
    node: ast.expr, namespace: dict[str, Any], globals_ns: dict[str, Any]
) -> tuple[Any, ...]:
    if not isinstance(node, ast.Tuple):
        raise ValueError("unsupported catalog expression: Tuple")
    return tuple(_eval_expr(item, namespace, globals_ns) for item in node.elts)


def _eval_dict(
    node: ast.expr, namespace: dict[str, Any], globals_ns: dict[str, Any]
) -> dict[Any, Any]:
    if not isinstance(node, ast.Dict):
        raise ValueError("unsupported catalog expression: Dict")
    evaluated: dict[Any, Any] = {}
    for key, value in zip(node.keys, node.values, strict=True):
        evaluated[_eval_expr(_dict_key(key), namespace, globals_ns)] = _eval_expr(
            value, namespace, globals_ns
        )
    return evaluated


def _dict_key(key: ast.expr | None) -> ast.expr:
    if key is None:
        raise ValueError("unsupported catalog dict unpack")
    return key


def _eval_add(node: ast.expr, namespace: dict[str, Any], globals_ns: dict[str, Any]) -> Any:
    if not isinstance(node, ast.BinOp):
        raise ValueError("unsupported catalog expression: BinOp")
    if not isinstance(node.op, ast.Add):
        raise ValueError(f"unsupported catalog operator: {type(node.op).__name__}")
    left = _eval_expr(node.left, namespace, globals_ns)
    right = _eval_expr(node.right, namespace, globals_ns)
    return left + right


def _eval_listcomp(
    node: ast.expr, namespace: dict[str, Any], globals_ns: dict[str, Any]
) -> list[Any]:
    if not isinstance(node, ast.ListComp):
        raise ValueError("unsupported catalog expression: ListComp")
    generator = _one_generator(node.generators)
    target = _target_name(generator)
    iterable = _eval_expr(generator.iter, namespace, globals_ns)
    built: list[Any] = []
    for item in iterable:
        local = dict(namespace)
        local[target] = item
        built.append(_eval_expr(node.elt, local, globals_ns))
    return built


def _one_generator(generators: list[ast.comprehension]) -> ast.comprehension:
    if len(generators) != 1:
        raise ValueError(_UNSUPPORTED_COMPREHENSION)
    generator = generators[0]
    if generator.ifs:
        raise ValueError(_UNSUPPORTED_COMPREHENSION)
    return generator


def _target_name(generator: ast.comprehension) -> str:
    if not isinstance(generator.target, ast.Name):
        raise ValueError(_UNSUPPORTED_COMPREHENSION)
    return generator.target.id


def _eval_call(node: ast.expr, namespace: dict[str, Any], globals_ns: dict[str, Any]) -> Any:
    if not isinstance(node, ast.Call):
        raise ValueError("unsupported catalog expression: Call")
    args = _positional(node, namespace, globals_ns)
    kwargs = _keywords(node, namespace, globals_ns)
    return _lookup(_call_name(node), namespace, globals_ns)(*args, **kwargs)


def _call_name(node: ast.Call) -> str:
    if not isinstance(node.func, ast.Name):
        raise ValueError("unsupported catalog call")
    return node.func.id


def _positional(node: ast.Call, namespace: dict[str, Any], globals_ns: dict[str, Any]) -> list[Any]:
    args: list[Any] = []
    for arg in node.args:
        if isinstance(arg, ast.Starred):
            raise ValueError("unsupported catalog call")
        args.append(_eval_expr(arg, namespace, globals_ns))
    return args


def _keywords(
    node: ast.Call, namespace: dict[str, Any], globals_ns: dict[str, Any]
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    for keyword in node.keywords:
        if keyword.arg is None:
            raise ValueError("unsupported catalog keyword unpack")
        kwargs[keyword.arg] = _eval_expr(keyword.value, namespace, globals_ns)
    return kwargs


_EVALUATORS: tuple[tuple[type[ast.expr], _Evaluator], ...] = (
    (ast.Name, _eval_name),
    (ast.List, _eval_list),
    (ast.Tuple, _eval_tuple),
    (ast.Dict, _eval_dict),
    (ast.BinOp, _eval_add),
    (ast.ListComp, _eval_listcomp),
    (ast.Call, _eval_call),
)
