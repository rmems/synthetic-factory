#!/usr/bin/env python3
"""AST-extract TUP mill sources on ``legacy-mill-lane``. Never exec mills."""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
from collections.abc import Mapping, Sequence
from typing import Any, TypeGuard

from ._contract import FINDING_SOURCE_NOT_PARSEABLE, SOURCE_REF, refuse, refuse_when, repo_root

PRESERVE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
ROW_VAR_NAMES = frozenset({"ROWS", "NEW_ROWS", "SPECS"})
_FAMILY_FN_RE = re.compile(r"^extra(_catalog|_v\d+)?$")

__all__ = [
    "PRESERVE_COMMIT",
    "family_rows_from_source",
    "git_show_mill",
    "leftover_plants_from_source",
    "mill_sha256",
    "plant_rows_from_source",
    "round_plants_from_source",
    "sha256_bytes",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git_show_mill(path: str, *, commit: str = PRESERVE_COMMIT) -> str:
    for ref in (f"{commit}:{path}", f"origin/{SOURCE_REF}:{path}"):
        proc = subprocess.run(
            ["git", "show", ref],
            cwd=repo_root(),
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout.decode("utf-8")
    refuse(FINDING_SOURCE_NOT_PARSEABLE, f"mill source not fetchable: {path}")


def mill_sha256(path: str, *, commit: str = PRESERVE_COMMIT) -> str:
    return sha256_bytes(git_show_mill(path, commit=commit).encode("utf-8"))


def _literal_str(node: ast.AST, label: str) -> str:
    refuse_when(
        not isinstance(node, ast.Constant) or not isinstance(node.value, str) or not node.value,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{label} is not a non-empty string literal",
    )
    return node.value


def _const_eval(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand)
    refuse(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"mill source is not a literal ({type(node).__name__})",
    )


def _is_name(node: ast.expr, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _single_target_value(node: ast.stmt, name: str) -> ast.expr | None:
    """The value a one-target ``Assign`` or a plain-name ``AnnAssign`` binds to ``name``."""

    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        return node.value if _is_name(node.targets[0], name) else None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.value if node.target.id == name else None
    return None


def _assigned_list(tree: ast.Module, name: str) -> ast.List | ast.Tuple | None:
    for node in tree.body:
        value = _single_target_value(node, name)
        if isinstance(value, (ast.List, ast.Tuple)):
            return value
    return None


def _is_families_assign(stmt: ast.stmt) -> TypeGuard[ast.Assign]:
    return isinstance(stmt, ast.Assign) and _is_name(stmt.targets[0], "families")


def _families_list_assign(func: ast.FunctionDef) -> ast.Assign | None:
    return next(
        (
            stmt
            for stmt in func.body
            if _is_families_assign(stmt) and isinstance(stmt.value, (ast.List, ast.Tuple))
        ),
        None,
    )


def _family_function(tree: ast.Module) -> ast.FunctionDef | None:
    best: ast.FunctionDef | None = None
    best_count = -1
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not _FAMILY_FN_RE.fullmatch(node.name):
            continue
        assign = _families_list_assign(node)
        if assign is None:
            continue
        count = len(assign.value.elts)
        if count > best_count:
            best = node
            best_count = count
    return best


def _parse_mill_source(source: str) -> ast.Module:
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"mill source is not parseable: {exc}")


def family_rows_from_source(source: str) -> list[dict[str, Any]]:
    """Return compact family dicts from ``extra_catalog`` / ``extra_v*``."""

    tree = _parse_mill_source(source)
    func = _family_function(tree)
    refuse_when(func is None, FINDING_SOURCE_NOT_PARSEABLE, "missing extra_* catalog function")
    assign = next((node for node in func.body if _is_families_assign(node)), None)
    refuse_when(
        assign is None or not isinstance(assign.value, (ast.List, ast.Tuple)),
        FINDING_SOURCE_NOT_PARSEABLE,
        "missing families list",
    )
    rows = [_family_row(elt, f"families[{index}]") for index, elt in enumerate(assign.value.elts)]
    refuse_when(not rows, FINDING_SOURCE_NOT_PARSEABLE, "extra catalog families is empty")
    return rows


def _family_row(elt: Any, label: str) -> dict[str, Any]:
    refuse_when(
        not isinstance(elt, (ast.List, ast.Tuple)) or len(elt.elts) != 4,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{label} is not a 4-tuple",
    )
    cmds_node = elt.elts[3]
    refuse_when(
        not isinstance(cmds_node, (ast.List, ast.Tuple)) or not cmds_node.elts,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{label}.cmds is empty",
    )
    cmds = [
        _family_cmd(cmd, f"{label}.cmds[{cmd_index}]")
        for cmd_index, cmd in enumerate(cmds_node.elts)
    ]
    return {
        "bin": _literal_str(elt.elts[0], f"{label}.bin"),
        "keep": _literal_str(elt.elts[1], f"{label}.keep"),
        "grep": _literal_str(elt.elts[2], f"{label}.grep"),
        "cmds": cmds,
    }


def _family_cmd(cmd: Any, label: str) -> list[str]:
    refuse_when(
        not isinstance(cmd, (ast.List, ast.Tuple)) or len(cmd.elts) != 3,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{label} is not a 3-tuple",
    )
    return [
        _literal_str(cmd.elts[0], f"{label}.short"),
        _literal_str(cmd.elts[1], f"{label}.verify"),
        _literal_str(cmd.elts[2], f"{label}.destroy"),
    ]


def _row_tuple_to_plant(row: tuple[Any, ...], *, mill_id: str, index: int) -> dict[str, Any]:
    if len(row) >= 13:
        _leftover, slug, tool, good, bad, keep, _resource, wait, _src429, _ver, grep, good_cmd, bad_cmd = row[
            :13
        ]
        verify = str(good_cmd)
        destroy = str(bad_cmd)
    elif len(row) == 8:
        leftover, slug, tool, good, bad, src429, ver, grep = row
        keep = f"/plant/{slug}/pay.conf"
        wait = 3 if index % 2 == 0 else 4
        verify = str(good)
        destroy = str(bad)
        _ = leftover, src429, ver
    else:
        refuse(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"unsupported row width {len(row)} in {mill_id}",
        )
    slug_s = str(slug)
    tool_s = str(tool)
    return {
        "mill_id": mill_id,
        "slug": slug_s,
        "bin": tool_s.split()[0],
        "verify": verify,
        "destroy": destroy,
        "keep": str(keep),
        "wait": int(wait),
        "grep": str(grep),
    }


def plant_rows_from_source(source: str, *, mill_id: str, var: str | None = None) -> list[dict[str, Any]]:
    """AST-extract ``ROWS`` / ``NEW_ROWS`` / ``SPECS`` tuple lists."""

    tree = _parse_mill_source(source)
    chosen = var
    nodes: ast.List | ast.Tuple | None = None
    if chosen:
        nodes = _assigned_list(tree, chosen)
    else:
        for name in ("SPECS", "ROWS", "NEW_ROWS"):
            nodes = _assigned_list(tree, name)
            if nodes is not None:
                chosen = name
                break
    refuse_when(nodes is None, FINDING_SOURCE_NOT_PARSEABLE, f"missing {ROW_VAR_NAMES} in {mill_id}")
    rows: list[dict[str, Any]] = []
    for index, elt in enumerate(nodes.elts):
        row = _const_eval(elt)
        refuse_when(
            not isinstance(row, tuple),
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{mill_id} {chosen}[{index}] is not a tuple",
        )
        rows.append(_row_tuple_to_plant(row, mill_id=mill_id, index=index))
    return rows


def _literal_value(node: ast.AST, label: str) -> Any:
    refuse_when(
        not isinstance(node, ast.Constant),
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{label} is not a literal",
    )
    return node.value


def _grep_from_read_cmd(cmd: Any) -> str:
    if not isinstance(cmd, str):
        return "pay|designed"
    match = re.search(r"grep -nE '([^']+)'", cmd)
    if match:
        return match.group(1)
    match = re.search(r'grep -nE "([^"]+)"', cmd)
    if match:
        return match.group(1)
    return "pay|designed"


def _plant_from_p_call(node: ast.Call, *, mill_id: str, index: int) -> dict[str, Any]:
    fields = {
        kw.arg: _literal_value(kw.value, f"PLANTS[{index}].{kw.arg}")
        for kw in node.keywords
        if kw.arg
    }
    refuse_when("slug" not in fields, FINDING_SOURCE_NOT_PARSEABLE, f"PLANTS[{index}] missing slug")
    verify = fields.get("good_cmd") or fields.get("good") or ""
    destroy = fields.get("bad_cmd") or fields.get("bad") or ""
    tool = str(fields.get("tool", ""))
    return {
        "mill_id": mill_id,
        "slug": str(fields["slug"]),
        "bin": tool.split()[0] if tool else "",
        "verify": str(verify),
        "destroy": str(destroy),
        "keep": str(fields.get("keep", "")),
        "wait": int(fields.get("wait", 3)),
        "grep": _grep_from_read_cmd(fields.get("read_cmd")),
    }


def _plant_from_plant_call(node: ast.Call, *, mill_id: str, index: int) -> dict[str, Any]:
    refuse_when(
        len(node.args) < 13,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"PLANTS[{index}] plant() needs 13 positional literals",
    )
    args = [_literal_value(arg, f"PLANTS[{index}].plant()[{pos}]") for pos, arg in enumerate(node.args[:13])]
    _leftover, slug, tool, _good, _bad, keep, _resource, wait, _src429, _ver, grep, verify, destroy = args
    tool_s = str(tool)
    return {
        "mill_id": mill_id,
        "slug": str(slug),
        "bin": tool_s.split()[0] if tool_s else "",
        "verify": str(verify),
        "destroy": str(destroy),
        "keep": str(keep),
        "wait": int(wait),
        "grep": str(grep),
    }


def _bound_value(node: ast.stmt, name: str) -> ast.expr | None:
    """The value ``node`` binds to ``name`` (any ``Assign`` target or a plain ``AnnAssign``)."""

    if isinstance(node, ast.AnnAssign):
        return node.value if _is_name(node.target, name) else None
    if isinstance(node, ast.Assign):
        return node.value if any(_is_name(target, name) for target in node.targets) else None
    return None


def _assigned_plants_list(tree: ast.Module) -> ast.List | None:
    for node in tree.body:
        value = _bound_value(node, "PLANTS")
        if isinstance(value, ast.List):
            return value
    return None


def leftover_plants_from_source(source: str, *, mill_id: str) -> list[dict[str, Any]]:
    """AST-extract ``PLANTS`` entries built with ``P(...)`` or ``plant(...)``."""

    tree = _parse_mill_source(source)
    nodes = _assigned_plants_list(tree)
    refuse_when(nodes is None, FINDING_SOURCE_NOT_PARSEABLE, f"missing PLANTS in {mill_id}")
    rows: list[dict[str, Any]] = []
    for index, elt in enumerate(nodes.elts):
        refuse_when(
            not isinstance(elt, ast.Call) or not isinstance(elt.func, ast.Name),
            FINDING_SOURCE_NOT_PARSEABLE,
            f"PLANTS[{index}] is not a call",
        )
        if elt.func.id == "P":
            rows.append(_plant_from_p_call(elt, mill_id=mill_id, index=index))
        elif elt.func.id == "plant":
            rows.append(_plant_from_plant_call(elt, mill_id=mill_id, index=index))
        else:
            refuse(
                FINDING_SOURCE_NOT_PARSEABLE,
                f"PLANTS[{index}] uses unsupported builder {elt.func.id!r}",
            )
    refuse_when(not rows, FINDING_SOURCE_NOT_PARSEABLE, f"PLANTS is empty in {mill_id}")
    return rows


def round_plants_from_source(source: str, *, mill_id: str) -> list[dict[str, Any]]:
    """AST-extract nested ``ROUNDS`` triple batches (slug, tool, fork, verify, ...)."""

    tree = _parse_mill_source(source)
    rounds_node = _last_rounds_list(tree)
    refuse_when(rounds_node is None, FINDING_SOURCE_NOT_PARSEABLE, f"missing ROUNDS in {mill_id}")
    rows: list[dict[str, Any]] = []
    for group_index, group in enumerate(rounds_node.elts):
        refuse_when(
            not isinstance(group, ast.List),
            FINDING_SOURCE_NOT_PARSEABLE,
            f"ROUNDS[{group_index}] is not a list",
        )
        rows.extend(
            _round_plant(elt, f"ROUNDS[{group_index}][{plant_index}]", mill_id=mill_id)
            for plant_index, elt in enumerate(group.elts)
        )
    refuse_when(not rows, FINDING_SOURCE_NOT_PARSEABLE, f"ROUNDS is empty in {mill_id}")
    return rows


def _last_rounds_list(tree: ast.Module) -> ast.List | None:
    rounds_node: ast.List | None = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        value = _bound_value(node, "ROUNDS")
        if isinstance(value, ast.List):
            rounds_node = value
    return rounds_node


def _round_plant(elt: Any, label: str, *, mill_id: str) -> dict[str, Any]:
    refuse_when(
        not isinstance(elt, ast.Tuple) or len(elt.elts) != 8,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{label} is not an 8-tuple",
    )
    slug = _literal_value(elt.elts[0], f"{label}.slug")
    tool = _literal_value(elt.elts[1], f"{label}.tool")
    _literal_value(elt.elts[2], f"{label}.fork")
    verify = _literal_value(elt.elts[3], f"{label}.verify")
    destroy = _literal_value(elt.elts[4], f"{label}.destroy")
    keep = _literal_value(elt.elts[5], f"{label}.keep")
    grep = _literal_value(elt.elts[6], f"{label}.grep")
    wait = _literal_value(elt.elts[7], f"{label}.wait")
    tool_s = str(tool)
    return {
        "mill_id": mill_id,
        "slug": str(slug),
        "bin": tool_s.split()[0] if tool_s else "",
        "verify": str(verify),
        "destroy": str(destroy),
        "keep": str(keep),
        "wait": int(wait),
        "grep": str(grep),
    }


def expand_family_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    mill_id: str,
    banned_slugs: Sequence[str],
    banned_prefix: Sequence[str],
) -> list[dict[str, Any]]:
    """Replay inspect-vs-destroy expansion for one family wave."""

    banned = frozenset(banned_slugs)
    prefixes = tuple(banned_prefix)
    plants: list[dict[str, Any]] = []
    index = 0
    for family in rows:
        bin_name = str(family["bin"])
        keep = str(family["keep"])
        grep = str(family["grep"])
        for short, verify_args, destroy in family["cmds"]:
            slug = f"{bin_name}-{short}"
            if _expansion_skips(slug, banned, prefixes):
                continue
            plants.append(
                {
                    "mill_id": mill_id,
                    "slug": slug,
                    "bin": bin_name.split()[0],
                    "verify": f"{bin_name} {verify_args}".strip(),
                    "destroy": _expanded_destroy(bin_name, destroy),
                    "keep": keep,
                    "wait": 3 + (index % 5),
                    "grep": grep,
                }
            )
            index += 1
    return plants


def _expansion_skips(slug: str, banned: frozenset[str], prefixes: tuple[str, ...]) -> bool:
    """Banned slugs and prefixes, plus the ``yq-eval`` / ``pacman`` waves, never expand."""

    if slug in banned or any(slug.startswith(prefix) for prefix in prefixes):
        return True
    return slug.startswith(("yq-eval", "pacman"))


def _expanded_destroy(bin_name: str, destroy: Any) -> Any:
    return destroy if str(destroy).startswith(("rm ", bin_name)) else f"{bin_name} {destroy}"
