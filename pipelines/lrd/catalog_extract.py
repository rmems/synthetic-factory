#!/usr/bin/env python3
"""AST-only extractors for lrd leftover mills. Never compile, exec, or eval them."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, NamedTuple, TypeGuard

from ._contract import (
    FINDING_HOPPER_REFUSED,
    FINDING_LOOP_REFUSED,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_SOURCE_NOT_PARSEABLE,
    HOPPER_DEF_NAMES,
    HOPPER_NAME_MARKERS,
    LLL_PAIR_KEYS,
    LEFTOVER3_CALLS,
    LOOP_NAME_MARKERS,
    P_COOKIE_ARG_COUNT,
    P_IDTOKEN_ARG_COUNT,
    SHAPE_LEGACY,
    SHAPE_LEFTOVER3,
    SHAPE_LLL,
    SHAPE_P_COOKIE,
    SHAPE_P_IDTOKEN,
    bind_import_twin,
    refuse,
    refuse_when,
)

MILL_ID_RE = re.compile(r"^lrd_r[0-9]+$")

__all__ = [
    "ast_extract_plants",
    "expand_p_cookie_call",
    "expand_p_idtoken_call",
]


def _str_or_int_constant(node: ast.AST) -> str | int | None:
    """The value of a non-bool str or int constant node, else None."""

    if not isinstance(node, ast.Constant) or isinstance(node.value, bool):
        return None
    value = node.value
    return value if isinstance(value, (str, int)) else None


def _literal(node: ast.AST, where: str) -> str | int:
    constant = _str_or_int_constant(node)
    if constant is not None:
        return constant
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _literal(node.operand, where)
        refuse_when(
            not isinstance(value, int),
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{where}: expected int after unary minus",
        )
        return -value
    refuse(FINDING_SOURCE_NOT_PARSEABLE, f"{where}: expected str or int literal")


def _literal_dict(node: ast.AST, where: str) -> dict[str, str | int]:
    refuse_when(
        not isinstance(node, ast.Dict),
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{where}: expected dict literal",
    )
    assert isinstance(node, ast.Dict)
    out: dict[str, str | int] = {}
    for key, value in zip(node.keys, node.values, strict=True):
        refuse_when(key is None, FINDING_SOURCE_NOT_PARSEABLE, f"{where}: starred dict")
        assert key is not None
        out[_literal(key, where)] = _literal(value, where)
    return out


def _is_named_call(node: ast.AST, names: frozenset[str]) -> TypeGuard[ast.Call]:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return False
    return node.func.id in names


def _is_kwargs_call(node: ast.AST, names: frozenset[str]) -> TypeGuard[ast.Call]:
    if not _is_named_call(node, names) or node.args:
        return False
    return all(kw.arg is not None for kw in node.keywords)


def _call_kwargs(node: ast.AST, where: str, names: frozenset[str]) -> dict[str, str | int]:
    refuse_when(
        not _is_kwargs_call(node, names),
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{where}: expected {names}(**kwargs)",
    )
    assert isinstance(node, ast.Call)
    plant: dict[str, str | int] = {}
    for index, kw in enumerate(node.keywords):
        assert kw.arg is not None
        plant[kw.arg] = _literal(kw.value, f"{where}.{kw.arg}#{index}")
    return plant


def _pairs_assignment(tree: ast.Module) -> ast.AST:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PAIRS":
                    return node.value
    refuse(FINDING_SOURCE_NOT_PARSEABLE, "source has no PAIRS assignment")


def _refuse_hopper_defs(source: str, tree: ast.AST) -> None:
    defs = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    refuse_when(
        bool(defs & HOPPER_DEF_NAMES),
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{source} defines hopper publish seam",
    )


_P_CALL_NAMES = frozenset({"P"})


def _pos_args(node: ast.Call, count: int, where: str) -> tuple[str | int, ...]:
    refuse_when(
        not _is_named_call(node, _P_CALL_NAMES),
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{where}: expected P(...) call",
    )
    refuse_when(
        len(node.args) != count or node.keywords,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{where}: P(...) must have {count} positional literals",
    )
    return tuple(_literal(arg, f"{where}[{index}]") for index, arg in enumerate(node.args))


class _PArgs(NamedTuple):
    """The positional literals of a mill ``P(...)`` call, named as the legacy mills name them."""

    sdk: str | int
    okm: str | int
    failm: str | int
    src: str | int
    cfg: str | int
    ok_fo: str | int
    ok_fn: str | int
    fail_fo: str | int
    fail_fn: str | int
    ok_wo: str | int
    ok_wn: str | int
    fail_wo: str | int
    fail_wn: str | int
    rg: str | int
    tk: str | int
    root: str | int
    rv: int


def expand_p_idtoken_call(args: tuple[str | int, ...]) -> tuple[dict[str, str | int], dict[str, str | int]]:
    """Expand ``P(...)`` from ``lrd-mill-leftover3-idtoken.py`` without executing it."""

    refuse_when(
        len(args) != P_IDTOKEN_ARG_COUNT,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"idtoken P(...) expects {P_IDTOKEN_ARG_COUNT} args",
    )
    sdk, okm, failm, src, cfg = args[0:5]
    ok_fo, ok_fn, fail_fo, fail_fn = args[5:9]
    ok_wo, ok_wn, fail_wo, fail_wn = args[9:13]
    rg, tk, root, rv = args[13:17]
    assert all(isinstance(item, str) for item in (sdk, okm, failm, src, cfg))
    assert isinstance(rv, int)
    p = _PArgs(
        sdk, okm, failm, src, cfg, ok_fo, ok_fn, fail_fo, fail_fn,
        ok_wo, ok_wn, fail_wo, fail_wn, rg, tk, root, rv,
    )
    return _idtoken_ok(p), _idtoken_fail(p)


def _idtoken_ok(p: _PArgs) -> dict[str, str | int]:
    return {
        "slug": f"{p.sdk}-{p.okm}-idtoken",
        "domain": f"{p.sdk}-{p.okm}-idtoken-vs-level-off",
        "stack": f"{p.sdk} {p.okm} leftover leftover leftover id_token vs level off",
        "seed": f"{str(p.sdk)[:6]}-{str(p.okm)[:6]}-pay-idtok-off",
        "ticket": f"{p.tk}-9",
        "root": f"{p.root}ok",
        "src": p.src,
        "cfg": p.cfg,
        "rg": p.rg,
        "goal": (
            f"{p.sdk} pay-api {p.okm} dumped leftover leftover leftover id_token. "
            f"Redact the field; do not mute the logger (that blinds warn). "
            f"Distinct from r81 Authorization and r100-r122 Set-Cookie."
        ),
        "plan": f"Prove id_token dump. Try mute; if warn tests fail, redact {p.okm} id_token.",
        "outcome": (
            f"mute blinded warn. {p.okm} redact. Tests 3/3. Residual {p.tk}-9: one path still raw. "
            f"Distinct from leftover3d Set-Cookie stacks."
        ),
        "plan_basis": (
            f"pay-api {p.sdk} {p.okm} leaked leftover leftover leftover id_token. "
            f"Inspect before mute."
        ),
        "list_obs": f"{p.src} {p.okm} id_token\nkept",
        "test_fail": "FAIL test_no_id_token: leaked. FAIL test_keep_warn.",
        "read1": p.ok_fo,
        "read2": p.ok_wo,
        "rb": "cached: omit leftover leftover leftover id_token. mute blinds warn. Not Set-Cookie leftover3d.",
        "wrong": "mute logger",
        "wo": p.ok_wo,
        "wn": p.ok_wn,
        "wto": "FAILED test_keep_warn: warn gone. leak would vanish for the wrong reason.",
        "pc": (
            f"Plan change: mute is the wrong layer. "
            f"Redact leftover leftover leftover id_token in {p.okm}."
        ),
        "rr": f"Need {p.okm} without id_token. Restore warn.",
        "fb": "Redact leftover leftover leftover id_token; keep warn.",
        "fo": p.ok_fo,
        "fn": p.ok_fn,
        "right": f"{p.okm} redact",
        "residual": f"one path raw; not leftover3d {p.sdk} cookie",
        "distinct": "Distinct from leftover3d Set-Cookie stacks.",
        "rk": "leaked",
        "rv": p.rv,
    }


def _idtoken_fail(p: _PArgs) -> dict[str, str | int]:
    return {**_idtoken_fail_episode(p), **_idtoken_fail_steps(p)}


def _idtoken_fail_episode(p: _PArgs) -> dict[str, str | int]:
    plat = f"platform-{p.sdk}"
    return {
        "slug": f"{p.sdk}-{p.failm}-idtoken-handoff",
        "domain": f"{p.sdk}-{p.failm}-idtoken-vs-disable",
        "stack": f"{p.sdk} {p.failm} leftover leftover leftover id_token vs disable {p.sdk}",
        "seed": f"{str(p.sdk)[:6]}-{str(p.failm)[:6]}-pay-idtok-handoff",
        "ticket": f"{p.tk}-10",
        "root": f"{p.root}hf",
        "src": p.src,
        "cfg": p.cfg,
        "rg": p.rg,
        "platform": plat,
        "goal": (
            f"{p.sdk} pay-api {p.failm} leftover leftover leftover dumped id_token. "
            f"Do not disable {p.sdk}. Hand off {p.failm} to {plat}."
        ),
        "plan": (
            f"Prove {p.failm} dump. Try disable {p.sdk}; if tests fail, request {p.failm}. "
            f"{p.failm} is {plat}."
        ),
        "outcome": (
            f"Disabling {p.sdk} blinded {p.failm}. {p.failm} is cluster. Reverted. "
            f"Handoff {p.tk}-10 to {plat}. Distinct from {p.okm} leftover leftover leftover."
        ),
        "plan_basis": (
            f"pay-api {p.sdk} {p.failm} leaked leftover leftover leftover id_token. "
            f"Inspect before disable."
        ),
    }


def _idtoken_fail_steps(p: _PArgs) -> dict[str, str | int]:
    plat = f"platform-{p.sdk}"
    return {
        "list_obs": f"{p.src} {p.failm} id_token\n# @{plat}",
        "test_fail": f"FAIL test_no_id_token: leaked. FAIL test_keep_{p.failm}.",
        "read1": p.fail_fo,
        "read2": f"{p.fail_wo}  # @{plat}",
        "rb": (
            f"cached: omit leftover leftover leftover id_token {p.failm}. "
            f"Disable {p.sdk} blinds {p.failm}. Distinct from {p.okm}."
        ),
        "wrong": f"disable {p.sdk}",
        "wo": p.fail_wo,
        "wn": p.fail_wn,
        "wto": (
            f"FAILED test_keep_{p.failm}: {p.failm} gone. "
            f"leak would vanish for the wrong reason."
        ),
        "pc": f"Plan change: disabling {p.sdk} is the wrong layer. {p.failm} is {plat}.",
        "rr": f"Need {p.failm} redact leftover leftover leftover id_token. Config is {plat}.",
        "fb": f"Draft {p.failm}; config still unsigned.",
        "fo": p.fail_fo,
        "fn": p.fail_fn,
        "slo": f"FAILED: {p.failm} unsigned. Need {plat}.",
        "hb": (
            f"Handoff {p.tk}-10: {plat} must not dump leftover leftover leftover id_token "
            f"{p.failm}. Distinct from {p.okm}."
        ),
        "right": f"{p.failm} redact",
        "distinct": f"Not {p.okm} leftover leftover leftover.",
        "rk": "leaked",
        "rv": p.rv - 1,
    }


def expand_p_cookie_call(args: tuple[str | int, ...]) -> tuple[dict[str, str | int], dict[str, str | int]]:
    """Expand ``P(...)`` from ``lrd-mill-r116.py`` without executing it."""

    refuse_when(
        len(args) != P_COOKIE_ARG_COUNT,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"cookie P(...) expects {P_COOKIE_ARG_COUNT} args",
    )
    sdk, okm, failm, src, cfg = args[0:5]
    ok_fo, ok_fn, fail_fo, fail_fn = args[5:9]
    ok_wo, ok_wn, fail_wo, fail_wn = args[9:13]
    rg, tk, root, rv = args[13:17]
    assert all(isinstance(item, str) for item in (sdk, okm, failm, src, cfg))
    assert isinstance(rv, int)
    p = _PArgs(
        sdk, okm, failm, src, cfg, ok_fo, ok_fn, fail_fo, fail_fn,
        ok_wo, ok_wn, fail_wo, fail_wn, rg, tk, root, rv,
    )
    return _cookie_ok(p), _cookie_fail(p)


def _cookie_ok(p: _PArgs) -> dict[str, str | int]:
    return {
        "slug": f"{p.sdk}-{p.okm}-cookie",
        "domain": f"{p.sdk}-{p.okm}-setcookie-vs-level-off",
        "stack": f"{p.sdk} {p.okm} leftover Set-Cookie vs level off",
        "seed": f"{str(p.sdk)[:6]}-{str(p.okm)[:6]}-pay-cookie-off",
        "ticket": f"{p.tk}-7",
        "root": f"{p.root}ok",
        "src": p.src,
        "cfg": p.cfg,
        "rg": p.rg,
        "goal": (
            f"{p.sdk} pay-api {p.okm} dumped Set-Cookie. Redact the field; do not mute "
            f"the logger (that blinds warn). Distinct from r100-r115 leftover3d stacks."
        ),
        "plan": f"Prove cookie dump. Try mute; if warn tests fail, redact {p.okm} Set-Cookie.",
        "outcome": (
            f"mute blinded warn. {p.okm} redact. Tests 3/3. Residual {p.tk}-7: one path still raw. "
            f"Distinct from leftover3d stacks."
        ),
        "plan_basis": f"pay-api {p.sdk} {p.okm} leaked Set-Cookie. Inspect before mute.",
        "list_obs": f"{p.src} {p.okm} Set-Cookie\nkept",
        "test_fail": "FAIL test_no_set_cookie: leaked. FAIL test_keep_warn.",
        "read1": p.ok_fo,
        "read2": p.ok_wo,
        "rb": f"cached: omit Set-Cookie {p.okm}. mute blinds warn. Distinct from leftover3d.",
        "wrong": "mute logger",
        "wo": p.ok_wo,
        "wn": p.ok_wn,
        "wto": "FAILED test_keep_warn: warn gone. leak would vanish for the wrong reason.",
        "pc": f"Plan change: mute is the wrong layer. Redact Set-Cookie in {p.okm}.",
        "rr": f"Need {p.okm} without Set-Cookie. Restore warn.",
        "fb": "Redact Set-Cookie; keep warn.",
        "fo": p.ok_fo,
        "fn": p.ok_fn,
        "right": f"{p.okm} redact",
        "residual": f"one path raw; not leftover3d {p.sdk}",
        "distinct": "Distinct from leftover3d stacks.",
        "rk": "leaked",
        "rv": p.rv,
    }


def _cookie_fail(p: _PArgs) -> dict[str, str | int]:
    return {**_cookie_fail_episode(p), **_cookie_fail_steps(p)}


def _cookie_fail_episode(p: _PArgs) -> dict[str, str | int]:
    plat = f"platform-{p.sdk}"
    return {
        "slug": f"{p.sdk}-{p.failm}-handoff",
        "domain": f"{p.sdk}-{p.failm}-setcookie-vs-disable",
        "stack": f"{p.sdk} {p.failm} leftover Set-Cookie vs disable {p.sdk}",
        "seed": f"{str(p.sdk)[:6]}-{str(p.failm)[:6]}-pay-cookie-handoff",
        "ticket": f"{p.tk}-8",
        "root": f"{p.root}hf",
        "src": p.src,
        "cfg": p.cfg,
        "rg": p.rg,
        "platform": plat,
        "goal": (
            f"{p.sdk} pay-api {p.failm} leftover dumped Set-Cookie. Do not disable {p.sdk}. "
            f"Hand off {p.failm} to {plat}."
        ),
        "plan": (
            f"Prove {p.failm} dump. Try disable {p.sdk}; if tests fail, request {p.failm}. "
            f"{p.failm} is {plat}."
        ),
        "outcome": (
            f"Disabling {p.sdk} blinded {p.failm}. {p.failm} is cluster. Reverted. "
            f"Handoff {p.tk}-8 to {plat}. Distinct from {p.okm} leftover."
        ),
        "plan_basis": f"pay-api {p.sdk} {p.failm} leaked Set-Cookie. Inspect before disable.",
    }


def _cookie_fail_steps(p: _PArgs) -> dict[str, str | int]:
    plat = f"platform-{p.sdk}"
    return {
        "list_obs": f"{p.src} {p.failm} Set-Cookie\n# @{plat}",
        "test_fail": f"FAIL test_no_set_cookie: leaked. FAIL test_keep_{p.failm}.",
        "read1": p.fail_fo,
        "read2": f"{p.fail_wo}  # @{plat}",
        "rb": (
            f"cached: omit Set-Cookie {p.failm}. Disable {p.sdk} blinds {p.failm}. "
            f"Distinct from {p.okm}."
        ),
        "wrong": f"disable {p.sdk}",
        "wo": p.fail_wo,
        "wn": p.fail_wn,
        "wto": (
            f"FAILED test_keep_{p.failm}: {p.failm} gone. "
            f"leak would vanish for the wrong reason."
        ),
        "pc": f"Plan change: disabling {p.sdk} is the wrong layer. {p.failm} is {plat}.",
        "rr": f"Need {p.failm} redact. Config is {plat}.",
        "fb": f"Draft {p.failm}; config still unsigned.",
        "fo": p.fail_fo,
        "fn": p.fail_fn,
        "slo": f"FAILED: {p.failm} unsigned. Need {plat}.",
        "hb": (
            f"Handoff {p.tk}-8: {plat} must not dump Set-Cookie {p.failm}. "
            f"Distinct from {p.okm} leftover."
        ),
        "right": f"{p.failm} redact",
        "distinct": f"Not {p.okm} leftover.",
        "rk": "leaked",
        "rv": p.rv - 1,
    }


class _MillSource(NamedTuple):
    """The mill a row is extracted from: its id, source path, and base round."""

    mill_id: str
    path: str
    base_round: int


def _pair_slug(side: dict[str, str | int]) -> str:
    slug = side["slug"]
    assert isinstance(slug, str)
    return slug


def _pair_row(
    ok: dict[str, str | int], fail: dict[str, str | int], mill: _MillSource, shape: str
) -> dict[str, Any]:
    slug = _pair_slug(ok)
    return {
        "base_round": mill.base_round,
        "mill_id": mill.mill_id,
        "plant_id": f"{mill.mill_id}:{slug}",
        "shape": shape,
        "slug": slug,
        "source": mill.path,
        "payload": {"ok": ok, "fail": fail},
    }


def _lll_pair_row(
    left: dict[str, str | int], right: dict[str, str | int], mill: _MillSource
) -> dict[str, Any]:
    _pair_slug(left)  # a left side without a slug fails before the key check
    missing = [key for key in LLL_PAIR_KEYS if key not in left or key not in right]
    refuse_when(
        bool(missing),
        FINDING_SOURCE_NOT_PARSEABLE,
        f"lll pair missing keys {missing[0] if missing else ''}",
    )
    return _pair_row(left, right, mill, SHAPE_LLL)


def _pair_elts(item: ast.AST, where: str, expected: str) -> list[ast.expr]:
    if isinstance(item, (ast.Tuple, ast.List)) and len(item.elts) == 2:
        return item.elts
    refuse(FINDING_SOURCE_NOT_PARSEABLE, f"{where} must be {expected}")


def _leftover3_item_row(
    item: ast.AST, where: str, mill: _MillSource, shape: str
) -> dict[str, Any]:
    ok_node, fail_node = _pair_elts(item, where, "(OK, FAIL)")
    ok = _call_kwargs(ok_node, f"{where}.ok", LEFTOVER3_CALLS)
    fail = _call_kwargs(fail_node, f"{where}.fail", LEFTOVER3_CALLS)
    return _pair_row(ok, fail, mill, shape)


_P_CALL_SHAPES = {
    SHAPE_P_IDTOKEN: (P_IDTOKEN_ARG_COUNT, expand_p_idtoken_call),
    SHAPE_P_COOKIE: (P_COOKIE_ARG_COUNT, expand_p_cookie_call),
}


def _p_call_item_row(item: ast.AST, where: str, mill: _MillSource, shape: str) -> dict[str, Any]:
    if not isinstance(item, ast.Call):
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"{where} must be P(...)")
    count, expand = _P_CALL_SHAPES[shape]
    ok, fail = expand(_pos_args(item, count, where))
    return _pair_row(ok, fail, mill, shape)


def _lll_item_row(item: ast.AST, where: str, mill: _MillSource, shape: str) -> dict[str, Any]:
    left_node, right_node = _pair_elts(item, where, "(dict, dict)")
    left = _literal_dict(left_node, f"{where}[0]")
    right = _literal_dict(right_node, f"{where}[1]")
    return _lll_pair_row(left, right, mill)


_ITEM_EXTRACTORS = (
    (SHAPE_LEFTOVER3, _leftover3_item_row),
    (SHAPE_P_IDTOKEN, _p_call_item_row),
    (SHAPE_P_COOKIE, _p_call_item_row),
    (SHAPE_LLL, _lll_item_row),
)


def _item_extractor(shape: str) -> Any:
    for name, extract in _ITEM_EXTRACTORS:
        if shape == name:
            return extract
    return None


def _source_filename(source: str) -> str:
    return Path(source).name.lower()


def refuse_hopper_source(source: str) -> None:
    """Refuse dpr-lrd hoppers. They stay with dpr; this package never execs them."""

    name = _source_filename(source)
    hopper = any(marker in name for marker in HOPPER_NAME_MARKERS)
    refuse_when(
        hopper,
        FINDING_HOPPER_REFUSED,
        f"{source} is a dpr hopper; hopper exec stays with dpr",
    )


def _refuse_loop_source(source: str) -> None:
    name = _source_filename(source)
    loop = any(marker in name for marker in LOOP_NAME_MARKERS)
    refuse_when(
        loop,
        FINDING_LOOP_REFUSED,
        f"{source} is an lrd loop, not a mill catalog",
    )


def _legacy_rows(source: str, *, mill_id: str, path: str, base_round: int) -> tuple[dict[str, Any], ...]:
    from . import catalog as cat

    refuse_hopper_source(path)
    _refuse_loop_source(path)
    rows = cat.plants_from_source(source, mill_id=mill_id, source=path, base_round=base_round)
    return tuple({**row, "shape": SHAPE_LEGACY} for row in rows)


def ast_extract_plants(
    source: str,
    *,
    mill_id: str,
    path: str,
    base_round: int,
    shape: str,
) -> tuple[dict[str, Any], ...]:
    """Return catalog rows from legacy-mill-lane lrd source text. Never execute it."""

    refuse_when(not MILL_ID_RE.fullmatch(mill_id), FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id}")
    refuse_hopper_source(path)
    if shape == SHAPE_LEGACY:
        return _legacy_rows(source, mill_id=mill_id, path=path, base_round=base_round)
    payload = _pairs_list(source, path)
    mill = _MillSource(mill_id, path, base_round)
    extract = _item_extractor(shape)
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(payload.elts):
        if extract is None:
            refuse(FINDING_SOURCE_NOT_PARSEABLE, f"{path}: unknown extract shape {shape!r}")
        rows.append(extract(item, f"{path} PAIRS[{index}]", mill, shape))
    refuse_when(not rows, FINDING_SOURCE_NOT_PARSEABLE, f"{path} has no extractable plants")
    _refuse_duplicate_plant_ids(rows)
    return tuple(rows)


def _pairs_list(source: str, path: str) -> ast.List:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"{path} does not parse: {exc}")
    _refuse_hopper_defs(path, tree)
    payload = _pairs_assignment(tree)
    refuse_when(
        not isinstance(payload, ast.List),
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{path} PAIRS must be a list",
    )
    assert isinstance(payload, ast.List)
    return payload


def _refuse_duplicate_plant_ids(rows: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for row in rows:
        refuse_when(
            row["plant_id"] in seen,
            FINDING_PLANT_FIELD_INVALID,
            f"duplicate plant_id {row['plant_id']}",
        )
        seen.add(row["plant_id"])


bind_import_twin(__name__)
