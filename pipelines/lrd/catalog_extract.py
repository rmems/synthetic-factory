#!/usr/bin/env python3
"""AST-only extractors for lrd leftover mills. Never compile, exec, or eval them."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

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


def _literal(node: ast.AST, where: str) -> str | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)) and not isinstance(
        node.value, bool
    ):
        return node.value
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


def _call_kwargs(node: ast.AST, where: str, names: frozenset[str]) -> dict[str, str | int]:
    refuse_when(
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id not in names
        or node.args
        or any(kw.arg is None for kw in node.keywords),
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
        FINDING_HOPPER_REFUSED,
        f"{source} defines mill_and_publish; hopper exec is refused",
    )


def _pos_args(node: ast.Call, count: int, where: str) -> tuple[str | int, ...]:
    refuse_when(
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id != "P",
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{where}: expected P(...) call",
    )
    refuse_when(
        len(node.args) != count or node.keywords,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{where}: P(...) must have {count} positional literals",
    )
    return tuple(_literal(arg, f"{where}[{index}]") for index, arg in enumerate(node.args))


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
    plat = f"platform-{sdk}"
    ok = {
        "slug": f"{sdk}-{okm}-idtoken",
        "domain": f"{sdk}-{okm}-idtoken-vs-level-off",
        "stack": f"{sdk} {okm} leftover leftover leftover id_token vs level off",
        "seed": f"{str(sdk)[:6]}-{str(okm)[:6]}-pay-idtok-off",
        "ticket": f"{tk}-9",
        "root": f"{root}ok",
        "src": src,
        "cfg": cfg,
        "rg": rg,
        "goal": (
            f"{sdk} pay-api {okm} dumped leftover leftover leftover id_token. "
            f"Redact the field; do not mute the logger (that blinds warn). "
            f"Distinct from r81 Authorization and r100-r122 Set-Cookie."
        ),
        "plan": f"Prove id_token dump. Try mute; if warn tests fail, redact {okm} id_token.",
        "outcome": (
            f"mute blinded warn. {okm} redact. Tests 3/3. Residual {tk}-9: one path still raw. "
            f"Distinct from leftover3d Set-Cookie stacks."
        ),
        "plan_basis": (
            f"pay-api {sdk} {okm} leaked leftover leftover leftover id_token. Inspect before mute."
        ),
        "list_obs": f"{src} {okm} id_token\nkept",
        "test_fail": "FAIL test_no_id_token: leaked. FAIL test_keep_warn.",
        "read1": ok_fo,
        "read2": ok_wo,
        "rb": "cached: omit leftover leftover leftover id_token. mute blinds warn. Not Set-Cookie leftover3d.",
        "wrong": "mute logger",
        "wo": ok_wo,
        "wn": ok_wn,
        "wto": "FAILED test_keep_warn: warn gone. leak would vanish for the wrong reason.",
        "pc": (
            f"Plan change: mute is the wrong layer. Redact leftover leftover leftover id_token in {okm}."
        ),
        "rr": f"Need {okm} without id_token. Restore warn.",
        "fb": "Redact leftover leftover leftover id_token; keep warn.",
        "fo": ok_fo,
        "fn": ok_fn,
        "right": f"{okm} redact",
        "residual": f"one path raw; not leftover3d {sdk} cookie",
        "distinct": "Distinct from leftover3d Set-Cookie stacks.",
        "rk": "leaked",
        "rv": rv,
    }
    fail = {
        "slug": f"{sdk}-{failm}-idtoken-handoff",
        "domain": f"{sdk}-{failm}-idtoken-vs-disable",
        "stack": f"{sdk} {failm} leftover leftover leftover id_token vs disable {sdk}",
        "seed": f"{str(sdk)[:6]}-{str(failm)[:6]}-pay-idtok-handoff",
        "ticket": f"{tk}-10",
        "root": f"{root}hf",
        "src": src,
        "cfg": cfg,
        "rg": rg,
        "platform": plat,
        "goal": (
            f"{sdk} pay-api {failm} leftover leftover leftover dumped id_token. "
            f"Do not disable {sdk}. Hand off {failm} to {plat}."
        ),
        "plan": (
            f"Prove {failm} dump. Try disable {sdk}; if tests fail, request {failm}. {failm} is {plat}."
        ),
        "outcome": (
            f"Disabling {sdk} blinded {failm}. {failm} is cluster. Reverted. "
            f"Handoff {tk}-10 to {plat}. Distinct from {okm} leftover leftover leftover."
        ),
        "plan_basis": (
            f"pay-api {sdk} {failm} leaked leftover leftover leftover id_token. Inspect before disable."
        ),
        "list_obs": f"{src} {failm} id_token\n# @{plat}",
        "test_fail": f"FAIL test_no_id_token: leaked. FAIL test_keep_{failm}.",
        "read1": fail_fo,
        "read2": f"{fail_wo}  # @{plat}",
        "rb": (
            f"cached: omit leftover leftover leftover id_token {failm}. "
            f"Disable {sdk} blinds {failm}. Distinct from {okm}."
        ),
        "wrong": f"disable {sdk}",
        "wo": fail_wo,
        "wn": fail_wn,
        "wto": f"FAILED test_keep_{failm}: {failm} gone. leak would vanish for the wrong reason.",
        "pc": f"Plan change: disabling {sdk} is the wrong layer. {failm} is {plat}.",
        "rr": f"Need {failm} redact leftover leftover leftover id_token. Config is {plat}.",
        "fb": f"Draft {failm}; config still unsigned.",
        "fo": fail_fo,
        "fn": fail_fn,
        "slo": f"FAILED: {failm} unsigned. Need {plat}.",
        "hb": (
            f"Handoff {tk}-10: {plat} must not dump leftover leftover leftover id_token {failm}. "
            f"Distinct from {okm}."
        ),
        "right": f"{failm} redact",
        "distinct": f"Not {okm} leftover leftover leftover.",
        "rk": "leaked",
        "rv": rv - 1,
    }
    return ok, fail


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
    plat = f"platform-{sdk}"
    ok = {
        "slug": f"{sdk}-{okm}-cookie",
        "domain": f"{sdk}-{okm}-setcookie-vs-level-off",
        "stack": f"{sdk} {okm} leftover Set-Cookie vs level off",
        "seed": f"{str(sdk)[:6]}-{str(okm)[:6]}-pay-cookie-off",
        "ticket": f"{tk}-7",
        "root": f"{root}ok",
        "src": src,
        "cfg": cfg,
        "rg": rg,
        "goal": (
            f"{sdk} pay-api {okm} dumped Set-Cookie. Redact the field; do not mute "
            f"the logger (that blinds warn). Distinct from r100-r115 leftover3d stacks."
        ),
        "plan": f"Prove cookie dump. Try mute; if warn tests fail, redact {okm} Set-Cookie.",
        "outcome": (
            f"mute blinded warn. {okm} redact. Tests 3/3. Residual {tk}-7: one path still raw. "
            f"Distinct from leftover3d stacks."
        ),
        "plan_basis": f"pay-api {sdk} {okm} leaked Set-Cookie. Inspect before mute.",
        "list_obs": f"{src} {okm} Set-Cookie\nkept",
        "test_fail": "FAIL test_no_set_cookie: leaked. FAIL test_keep_warn.",
        "read1": ok_fo,
        "read2": ok_wo,
        "rb": f"cached: omit Set-Cookie {okm}. mute blinds warn. Distinct from leftover3d.",
        "wrong": "mute logger",
        "wo": ok_wo,
        "wn": ok_wn,
        "wto": "FAILED test_keep_warn: warn gone. leak would vanish for the wrong reason.",
        "pc": f"Plan change: mute is the wrong layer. Redact Set-Cookie in {okm}.",
        "rr": f"Need {okm} without Set-Cookie. Restore warn.",
        "fb": "Redact Set-Cookie; keep warn.",
        "fo": ok_fo,
        "fn": ok_fn,
        "right": f"{okm} redact",
        "residual": f"one path raw; not leftover3d {sdk}",
        "distinct": "Distinct from leftover3d stacks.",
        "rk": "leaked",
        "rv": rv,
    }
    fail = {
        "slug": f"{sdk}-{failm}-handoff",
        "domain": f"{sdk}-{failm}-setcookie-vs-disable",
        "stack": f"{sdk} {failm} leftover Set-Cookie vs disable {sdk}",
        "seed": f"{str(sdk)[:6]}-{str(failm)[:6]}-pay-cookie-handoff",
        "ticket": f"{tk}-8",
        "root": f"{root}hf",
        "src": src,
        "cfg": cfg,
        "rg": rg,
        "platform": plat,
        "goal": (
            f"{sdk} pay-api {failm} leftover dumped Set-Cookie. Do not disable {sdk}. "
            f"Hand off {failm} to {plat}."
        ),
        "plan": (
            f"Prove {failm} dump. Try disable {sdk}; if tests fail, request {failm}. {failm} is {plat}."
        ),
        "outcome": (
            f"Disabling {sdk} blinded {failm}. {failm} is cluster. Reverted. "
            f"Handoff {tk}-8 to {plat}. Distinct from {okm} leftover."
        ),
        "plan_basis": f"pay-api {sdk} {failm} leaked Set-Cookie. Inspect before disable.",
        "list_obs": f"{src} {failm} Set-Cookie\n# @{plat}",
        "test_fail": f"FAIL test_no_set_cookie: leaked. FAIL test_keep_{failm}.",
        "read1": fail_fo,
        "read2": f"{fail_wo}  # @{plat}",
        "rb": f"cached: omit Set-Cookie {failm}. Disable {sdk} blinds {failm}. Distinct from {okm}.",
        "wrong": f"disable {sdk}",
        "wo": fail_wo,
        "wn": fail_wn,
        "wto": f"FAILED test_keep_{failm}: {failm} gone. leak would vanish for the wrong reason.",
        "pc": f"Plan change: disabling {sdk} is the wrong layer. {failm} is {plat}.",
        "rr": f"Need {failm} redact. Config is {plat}.",
        "fb": f"Draft {failm}; config still unsigned.",
        "fo": fail_fo,
        "fn": fail_fn,
        "slo": f"FAILED: {failm} unsigned. Need {plat}.",
        "hb": (
            f"Handoff {tk}-8: {plat} must not dump Set-Cookie {failm}. Distinct from {okm} leftover."
        ),
        "right": f"{failm} redact",
        "distinct": f"Not {okm} leftover.",
        "rk": "leaked",
        "rv": rv - 1,
    }
    return ok, fail


def _leftover3_pair_row(
    ok: dict[str, str | int],
    fail: dict[str, str | int],
    *,
    mill_id: str,
    source: str,
    base_round: int,
    shape: str,
) -> dict[str, Any]:
    slug = ok["slug"]
    assert isinstance(slug, str)
    return {
        "base_round": base_round,
        "mill_id": mill_id,
        "plant_id": f"{mill_id}:{slug}",
        "shape": shape,
        "slug": slug,
        "source": source,
        "payload": {"ok": ok, "fail": fail},
    }


def _lll_pair_row(
    left: dict[str, str | int],
    right: dict[str, str | int],
    *,
    mill_id: str,
    source: str,
    base_round: int,
) -> dict[str, Any]:
    slug = left["slug"]
    assert isinstance(slug, str)
    missing = [key for key in LLL_PAIR_KEYS if key not in left or key not in right]
    refuse_when(
        bool(missing),
        FINDING_SOURCE_NOT_PARSEABLE,
        f"lll pair missing keys {missing[0] if missing else ''}",
    )
    return {
        "base_round": base_round,
        "mill_id": mill_id,
        "plant_id": f"{mill_id}:{slug}",
        "shape": SHAPE_LLL,
        "slug": slug,
        "source": source,
        "payload": {"ok": left, "fail": right},
    }


def _source_filename(source: str) -> str:
    return Path(source).name.lower()


def refuse_hopper_source(source: str) -> None:
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
    _refuse_loop_source(path)
    if shape == SHAPE_LEGACY:
        return _legacy_rows(source, mill_id=mill_id, path=path, base_round=base_round)
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
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(payload.elts):
        if shape == SHAPE_LEFTOVER3:
            refuse_when(
                not isinstance(item, (ast.Tuple, ast.List)) or len(item.elts) != 2,
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{path} PAIRS[{index}] must be (OK, FAIL)",
            )
            assert isinstance(item, (ast.Tuple, ast.List))
            ok = _call_kwargs(item.elts[0], f"{path} PAIRS[{index}].ok", LEFTOVER3_CALLS)
            fail = _call_kwargs(item.elts[1], f"{path} PAIRS[{index}].fail", LEFTOVER3_CALLS)
            rows.append(
                _leftover3_pair_row(
                    ok, fail, mill_id=mill_id, source=path, base_round=base_round, shape=shape
                )
            )
        elif shape == SHAPE_P_IDTOKEN:
            refuse_when(
                not isinstance(item, ast.Call),
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{path} PAIRS[{index}] must be P(...)",
            )
            args = _pos_args(item, P_IDTOKEN_ARG_COUNT, f"{path} PAIRS[{index}]")
            ok, fail = expand_p_idtoken_call(args)
            rows.append(
                _leftover3_pair_row(
                    ok, fail, mill_id=mill_id, source=path, base_round=base_round, shape=shape
                )
            )
        elif shape == SHAPE_P_COOKIE:
            refuse_when(
                not isinstance(item, ast.Call),
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{path} PAIRS[{index}] must be P(...)",
            )
            args = _pos_args(item, P_COOKIE_ARG_COUNT, f"{path} PAIRS[{index}]")
            ok, fail = expand_p_cookie_call(args)
            rows.append(
                _leftover3_pair_row(
                    ok, fail, mill_id=mill_id, source=path, base_round=base_round, shape=shape
                )
            )
        elif shape == SHAPE_LLL:
            refuse_when(
                not isinstance(item, (ast.Tuple, ast.List)) or len(item.elts) != 2,
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{path} PAIRS[{index}] must be (dict, dict)",
            )
            assert isinstance(item, (ast.Tuple, ast.List))
            left = _literal_dict(item.elts[0], f"{path} PAIRS[{index}][0]")
            right = _literal_dict(item.elts[1], f"{path} PAIRS[{index}][1]")
            rows.append(
                _lll_pair_row(left, right, mill_id=mill_id, source=path, base_round=base_round)
            )
        else:
            refuse(FINDING_SOURCE_NOT_PARSEABLE, f"{path}: unknown extract shape {shape!r}")
    refuse_when(not rows, FINDING_SOURCE_NOT_PARSEABLE, f"{path} has no extractable plants")
    seen: set[str] = set()
    for row in rows:
        refuse_when(
            row["plant_id"] in seen,
            FINDING_PLANT_FIELD_INVALID,
            f"duplicate plant_id {row['plant_id']}",
        )
        seen.add(row["plant_id"])
    return tuple(rows)


bind_import_twin(__name__)
