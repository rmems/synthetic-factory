#!/usr/bin/env python3
"""Pinned CEI pair catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` (identity, factory, mill pins)
and ``plants.jsonl`` (one pair per line). Load verifies the plants digest
and every required field before a pair is trusted. Historical hop-mill
and leftover leftover leftover scripts are read only as text through
:func:`plants_from_source`. Hop-loop and leftover leftover leftover
leftover3 importers are refused.
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple, TypeGuard

from ._contract import (
    BAD_ARG_NAMES,
    BAD_CALL,
    BAD_SIDE_KEYS,
    BANNED_SLUG_BITS,
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    DEFERRED_LEFTOVER3_MARKERS,
    FACTORY,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_LEFTOVER3_EXEC,
    FINDING_LOOP_REFUSED,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_DUPLICATE_ID,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    FOREIGN_LEFTOVER3_IMPORTS,
    LEFTOVER3_BAD_KEYS,
    LEFTOVER3_BANNED_SLUGS,
    LEFTOVER3_CALL,
    LEFTOVER3_OK_KEYS,
    LEFTOVER3_SHAPE,
    LEFTOVER3_WRONG,
    LOOP_NAME_MARKERS,
    MILL_PREFIX,
    NOVEL_COVERAGE_BAD,
    NOVEL_COVERAGE_OK,
    OK_ARG_NAMES,
    OK_CALL,
    OK_SIDE_KEYS,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    SHAPE_OK_BAD,
    SLICE3_SOURCES,
    SOURCE_ROUND,
    S_BAD_ARG_NAMES,
    S_OK_ARG_NAMES,
    CeiRefusal,
    bind_import_twin,
    load_strict_json,
    repo_root,
)

MILL_ID_RE = re.compile(r"^cei_r[0-9]+$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

__all__ = [
    "Catalog",
    "Leftover3Side",
    "Mill",
    "Plant",
    "Side",
    "catalog_check",
    "default_catalog_dir",
    "expand_bad",
    "expand_leftover3",
    "expand_ok",
    "load_catalog",
    "plants_from_source",
    "sha256_bytes",
]


@dataclass(frozen=True)
class Side:
    """One hopper-shaped CEI episode side expanded from ``_ok`` or ``_bad``."""

    slug: str
    goal: str
    plan: str
    mod: str
    test_fn: str
    src_body: str
    test_body: str
    grep_pat: str
    grep_hit: str
    fail_msg: str
    first_old: str
    first_new: str
    first_obs: str
    still_msg: str
    reread_obs: str
    plan_change: str
    fix_new: str
    fix_obs: str
    docs_url: str
    docs_ok: str
    docs_url2: str
    docs_ok2: str
    outcome: str
    domain: str
    stack: str
    seed: str
    residual: str
    coverage: int
    ticket: str | None = None
    ticket_why: str | None = None

    def as_mapping(self) -> dict[str, Any]:
        payload = {key: getattr(self, key) for key in OK_SIDE_KEYS}
        if self.ticket is not None:
            payload["ticket"] = self.ticket
        if self.ticket_why is not None:
            payload["ticket_why"] = self.ticket_why
        return payload


@dataclass(frozen=True)
class Leftover3Side:
    """One leftover leftover leftover ``S()`` spec from ``cei_r48_mill``."""

    slug: str
    mod: str
    file: str
    leftover: str
    naive: str
    wrong: str
    wrong2: str
    fix: str
    test: str
    url: str
    url2: str
    doc: str
    doc2: str
    fail1: str
    fail2: str
    plan: str
    goal: str
    domain: str
    stack: str
    outcome: str
    chg: str
    ticket: str | None = None

    def as_mapping(self) -> dict[str, Any]:
        payload = {key: getattr(self, key) for key in LEFTOVER3_OK_KEYS if key != "ok"}
        payload["ok"] = self.outcome
        if self.ticket is not None:
            payload["ticket"] = self.ticket
        return payload


@dataclass(frozen=True)
class Plant:
    """One AST-extracted CEI pair (success side + handoff side)."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    index: int
    shape: str
    ok: Side | Leftover3Side
    bad: Side | Leftover3Side


@dataclass(frozen=True)
class Mill:
    mill_id: str
    base_round: int
    source: str
    plant_count: int


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    directory: Path
    factory: str
    plants_sha256: str
    plants: tuple[Plant, ...]
    mills: tuple[Mill, ...]
    meta: Mapping[str, Any]

    def plant(self, plant_id: str) -> Plant:
        for item in self.plants:
            if item.plant_id == plant_id:
                return item
        raise CeiRefusal(FINDING_PLANT_NOT_FOUND, f"no plant {plant_id!r} in the catalog")

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        found = tuple(item for item in self.plants if item.mill_id == mill_id)
        if not found:
            raise CeiRefusal(FINDING_MILL_NOT_FOUND, f"no mill {mill_id!r} in the catalog")
        return found


def default_catalog_dir() -> Path:
    return repo_root() / "config" / "cei"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_args(args: Mapping[str, Any], names: tuple[str, ...], call: str) -> None:
    missing = [name for name in names if name not in args]
    if missing:
        raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{call} missing {missing[0]}")


def _extra_args(args: Mapping[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    """Arguments beyond the named ones; they override the expansion's defaults."""

    return {key: args[key] for key in args if key not in names}


def expand_ok(args: Mapping[str, Any]) -> dict[str, Any]:
    """Faithful ``_ok`` expansion from ``cei-mill-r81``. Never exec."""

    _require_args(args, OK_ARG_NAMES, "_ok")
    slug = args["slug"]
    goal = args["goal"]
    mod = args["mod"]
    stack = args["stack"]
    docs = args["docs"]
    first_old = args["first_old"]
    first_new = args["first_new"]
    fix_new = args["fix_new"]
    extra = _extra_args(args, OK_ARG_NAMES)
    row = {
        "slug": slug,
        "goal": goal,
        "plan": f"Read {mod}, try first patch, then {stack}.",
        "mod": mod,
        "test_fn": f"test_{mod}",
        "src_body": f"def parse(blob):\n    {first_old}\n",
        "test_body": f"def test_{mod}():\n    assert parse(b'x')['kind'] == '{mod}'\n",
        "grep_pat": mod,
        "grep_hit": f"src/{mod}.py:2: {first_old.strip()}",
        "fail_msg": f"AssertionError: {mod} naive parse missed {stack}",
        "first_old": first_old,
        "first_new": first_new,
        "first_obs": f"patched first apply still wrong for {stack}",
        "still_msg": f"AssertionError: first patch is not {stack}",
        "reread_obs": f"{stack} is the real index; first patch is display-only",
        "plan_change": f"Plan change: bind {stack}. Display parse is not the index.",
        "fix_new": fix_new,
        "fix_obs": f"patched {stack}",
        "docs_url": docs,
        "docs_ok": f"{stack} is required; naive drop/display is not enough.",
        "docs_url2": docs,
        "docs_ok2": f"Keep {stack}. Not leftover leftover leftover unlink clones.",
        "outcome": f"{stack} bound. Display unused (success).",
        "domain": f"{slug}-dialect-index",
        "stack": stack,
        "seed": slug,
        "residual": f"{stack} is not a naive drop.",
        "coverage": NOVEL_COVERAGE_OK,
    }
    row.update(extra)
    return row


def expand_bad(args: Mapping[str, Any]) -> dict[str, Any]:
    """Faithful ``_bad`` expansion from ``cei-mill-r81``. Never exec."""

    _require_args(args, BAD_ARG_NAMES, "_bad")
    slug = args["slug"]
    goal = args["goal"]
    mod = args["mod"]
    stack = args["stack"]
    docs = args["docs"]
    first_old = args["first_old"]
    first_new = args["first_new"]
    ticket = args["ticket"]
    extra = _extra_args(args, BAD_ARG_NAMES)
    row = {
        "slug": slug,
        "goal": goal,
        "plan": f"Read {mod}, try first patch, then hand off {ticket}.",
        "mod": mod,
        "test_fn": f"test_{mod}",
        "src_body": f"def parse(blob):\n    {first_old}\n",
        "test_body": f"def test_{mod}():\n    assert 'handoff' in parse(b'x')\n",
        "grep_pat": mod,
        "grep_hit": f"src/{mod}.py:2: {first_old.strip()}",
        "fail_msg": f"AssertionError: {mod} still owned by {stack}",
        "first_old": first_old,
        "first_new": first_new,
        "first_obs": f"patched first apply still {stack}-owned",
        "still_msg": f"AssertionError: cannot mint {stack} here",
        "reread_obs": f"{stack} is platform-owned; local parse cannot rewrite it",
        "plan_change": f"Plan change: {stack} is platform. Handoff {ticket}.",
        "fix_new": f"    return {{'handoff': '{ticket}'}}",
        "fix_obs": f"ticket {ticket} filed",
        "docs_url": docs,
        "docs_ok": f"{stack} is platform; hand off {ticket}.",
        "docs_url2": docs,
        "docs_ok2": f"Do not unlink. Handoff {ticket}. Not leftover leftover leftover clones.",
        "outcome": f"Still {stack}-owned — handoff {ticket}.",
        "domain": f"{slug}-handoff",
        "stack": stack,
        "seed": slug,
        "residual": f"{stack} is platform.",
        "ticket": ticket,
        "ticket_why": f"{stack} owned by ingest-plat",
        "coverage": NOVEL_COVERAGE_BAD,
    }
    row.update(extra)
    return row


def expand_leftover3(args: Mapping[str, Any], *, ticket_required: bool) -> dict[str, Any]:
    """Faithful ``S()`` expansion from ``cei_r48_mill``. Never exec."""

    names = S_BAD_ARG_NAMES if ticket_required else S_OK_ARG_NAMES
    _require_args(args, names, "S()")
    extra = _extra_args(args, names)
    row = {key: args[key] for key in names}
    row.setdefault("wrong", LEFTOVER3_WRONG)
    row.update(extra)
    if ticket_required and not isinstance(row.get("ticket"), str):
        raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, "S() handoff missing ticket")
    if not ticket_required and "ticket" in row:
        raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, "S() success side must omit ticket")
    return row


def _const_eval(node: ast.AST) -> Any:
    """Literal values only. Never exec, compile, or eval."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    return _const_dict_or_negated(node)


def _const_dict_or_negated(node: ast.AST) -> Any:
    """A dict display (``**`` unpacking refused) or ``-operand``; other node types are refused."""

    if isinstance(node, ast.Dict):
        # Refuse ``**`` unpacking before any key or value is evaluated.
        pairs: list[tuple[ast.expr, ast.expr]] = []
        for key, value in zip(node.keys, node.values):
            if key is None:
                raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, "pair source uses dict unpacking")
            pairs.append((key, value))
        return {_const_eval(key): _const_eval(value) for key, value in pairs}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        # Apply each minus on the way out, but walk the spine in a loop. A
        # 600-deep chain is the same value, including TypeError on a non-number.
        operand: ast.AST = node
        flips = 0
        while isinstance(operand, ast.UnaryOp) and isinstance(operand.op, ast.USub):
            flips += 1
            operand = operand.operand
        value = _const_eval(operand)
        while flips:
            value = -value
            flips -= 1
        return value
    raise CeiRefusal(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"pair source is not a constant ({type(node).__name__})",
    )


def _assigned_name(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    if (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
    ):
        return node.target.id, node.value
    return None


def _call_args(node: ast.AST, names: tuple[str, ...], where: str) -> dict[str, Any]:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} is not a named call")
    if len(node.args) > len(names):
        raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} has extra positional args")
    mapped: dict[str, Any] = {}
    for index, arg in enumerate(node.args):
        mapped[names[index]] = _const_eval(arg)
    for keyword in node.keywords:
        if keyword.arg is None:
            raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} uses star-kwargs")
        mapped[keyword.arg] = _const_eval(keyword.value)
    return mapped


def _refuse_banned_slug(slug: str, domain: str, where: str) -> None:
    blob = f"{slug} {domain}".lower()
    for bit in BANNED_SLUG_BITS:
        if bit in blob:
            raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} carries banned {bit!r}")


def _refuse_leftover3_slug(slug: str, where: str) -> None:
    if slug in LEFTOVER3_BANNED_SLUGS:
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} slug is banned {slug!r}")


def _source_filename(source: str) -> str:
    return Path(source).name.lower()


def _refuse_loop_or_foreign_leftover3(text: str, source: str) -> None:
    """Refuse hop-loop and leftover leftover leftover leftover3 exec/import."""

    normalized = source.replace("\\", "/")
    if normalized in SLICE3_SOURCES:
        return
    name = _source_filename(source)
    if any(marker in name for marker in LOOP_NAME_MARKERS):
        raise CeiRefusal(FINDING_LOOP_REFUSED, f"{source} is a hop-loop, not a catalog")
    if any(marker in name for marker in DEFERRED_LEFTOVER3_MARKERS):
        raise CeiRefusal(
            FINDING_LEFTOVER3_EXEC,
            f"{source} leftover leftover leftover leftover3 mill is not this slice",
        )
    for marker in FOREIGN_LEFTOVER3_IMPORTS:
        if marker in text:
            raise CeiRefusal(
                FINDING_LEFTOVER3_EXEC,
                f"{source} leftover leftover leftover leftover3 imports a foreign mill",
            )


def _is_named_call(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name


def _is_ok_bad_pair(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Tuple)
        and len(node.elts) == 2
        and _is_named_call(node.elts[0], OK_CALL)
        and _is_named_call(node.elts[1], BAD_CALL)
    )


def _is_s_pair(node: ast.AST) -> TypeGuard[ast.Tuple]:
    return (
        isinstance(node, ast.Tuple)
        and len(node.elts) == 2
        and _is_named_call(node.elts[0], LEFTOVER3_CALL)
        and _is_named_call(node.elts[1], LEFTOVER3_CALL)
    )


def _is_dict_leftover3_pair(node: ast.AST) -> TypeGuard[ast.Tuple]:
    return (
        isinstance(node, ast.Tuple)
        and len(node.elts) == 2
        and isinstance(node.elts[0], ast.Dict)
        and isinstance(node.elts[1], ast.Dict)
    )


class _Origin(NamedTuple):
    """Where one source's extracted pairs come from: mill, source path, and base round."""

    mill_id: str
    source: str
    base: int

    def pair_row(self, index: int, ok: dict[str, Any], bad: dict[str, Any]) -> dict[str, Any]:
        return {
            "plant_id": f"{self.mill_id}:{ok['slug']}",
            "mill_id": self.mill_id,
            "source": self.source,
            "base_round": self.base,
            "index": index,
            "ok": ok,
            "bad": bad,
        }

    def leftover3_row(
        self, index: int, ok: dict[str, Any], bad: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "plant_id": f"{self.mill_id}:{ok['slug']}",
            "mill_id": self.mill_id,
            "source": self.source,
            "base_round": self.base,
            "index": index,
            "shape": LEFTOVER3_SHAPE,
            "ok": ok,
            "bad": bad,
        }


class _SeenIdentities:
    """Slugs, mods, and tickets already claimed by earlier pairs of one source."""

    def __init__(self) -> None:
        self.slugs: set[str] = set()
        self.mods: set[str] = set()
        self.tickets: set[str] = set()

    def claim(self, ok: Mapping[str, Any], bad: Mapping[str, Any]) -> None:
        """Refuse a slug, mod, or ticket an earlier pair already used, then record them."""

        for slug in (ok["slug"], bad["slug"]):
            if slug in self.slugs:
                raise CeiRefusal(FINDING_PLANT_DUPLICATE_ID, f"duplicate slug {slug}")
            self.slugs.add(slug)
        for mod in (ok["mod"], bad["mod"]):
            if mod in self.mods:
                raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"duplicate mod {mod}")
            self.mods.add(mod)
        ticket = bad["ticket"]
        if ticket in self.tickets:
            raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"duplicate ticket {ticket}")
        self.tickets.add(ticket)


def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract ``PAIRS`` of ``_ok``/``_bad`` or leftover leftover leftover ``S()``. Never exec."""

    _refuse_loop_or_foreign_leftover3(text, source)
    tree = _parse_source(text, source)
    raw_pairs, inferred_base = _pairs_assignment(tree)
    if not isinstance(raw_pairs, ast.List) or not raw_pairs.elts:
        raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no PAIRS list")
    if not MILL_ID_RE.fullmatch(mill_id):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not cei_rNNN")
    base = inferred_base if base_round is None else base_round
    origin = _Origin(mill_id, source, _checked_base(base, mill_id, source))
    first = raw_pairs.elts[0]
    if _is_s_pair(first):
        return _plants_from_s_calls(raw_pairs, origin)
    if _is_dict_leftover3_pair(first):
        return _plants_from_dict_leftover3(raw_pairs, origin)
    return _plants_from_ok_bad_calls(raw_pairs, origin)


def _parse_source(text: str, source: str) -> ast.Module:
    try:
        return ast.parse(text)
    except SyntaxError as exc:
        raise CeiRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}"
        ) from exc


def _pairs_assignment(tree: ast.Module) -> tuple[ast.AST | None, Any]:
    """The last ``PAIRS`` value node and the last ``CATALOG_FIRST`` constant, in body order."""

    raw_pairs: ast.AST | None = None
    inferred_base: Any = None
    for node in tree.body:
        assigned = _assigned_name(node)
        if assigned is None:
            continue
        name, value = assigned
        if name == "PAIRS":
            raw_pairs = value
        elif name == "CATALOG_FIRST":
            inferred_base = _const_eval(value)
    return raw_pairs, inferred_base


def _checked_base(base: Any, mill_id: str, source: str) -> int:
    """``CATALOG_FIRST`` (or the caller's round); else the mill's round; a positive int."""

    if base is None:
        suffix = mill_id.removeprefix("cei_r")
        base = int(suffix) if suffix.isdigit() else SOURCE_ROUND
    if not isinstance(base, int) or isinstance(base, bool) or base < 1:
        raise CeiRefusal(
            FINDING_PLANT_FIELD_INVALID, f"{source} CATALOG_FIRST must be a positive int"
        )
    return base


def _called_name(node: ast.AST, where: str) -> str:
    """The function name of a ``name(...)`` call; anything else is refused at ``where``."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, where)
    return node.func.id


def _ok_bad_nodes(raw: ast.AST, where: str) -> tuple[ast.expr, ast.expr]:
    if not isinstance(raw, ast.Tuple) or len(raw.elts) != 2:
        raise CeiRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{where} is not an (_ok, _bad) tuple",
        )
    ok_node, bad_node = raw.elts
    ok_name = _called_name(ok_node, f"{where}[0]")
    bad_name = _called_name(bad_node, f"{where}[1]")
    if ok_name != OK_CALL or bad_name != BAD_CALL:
        raise CeiRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{where} must be {_ok_label()}",
        )
    return ok_node, bad_node


def _ok_bad_sides(raw: ast.AST, where: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Expanded ``(_ok(...), _bad(...))`` sides whose ``first_old`` sits in ``src_body``."""

    ok_node, bad_node = _ok_bad_nodes(raw, where)
    ok = expand_ok(_call_args(ok_node, OK_ARG_NAMES, f"{where}.ok"))
    bad = expand_bad(_call_args(bad_node, BAD_ARG_NAMES, f"{where}.bad"))
    if ok["first_old"] not in ok["src_body"] or bad["first_old"] not in bad["src_body"]:
        raise CeiRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{where} first_old is not in src_body",
        )
    return ok, bad


def _plants_from_ok_bad_calls(
    raw_pairs: ast.List, origin: _Origin
) -> tuple[dict[str, Any], ...]:
    rows = []
    seen = _SeenIdentities()
    for index, raw in enumerate(raw_pairs.elts):
        where = f"{origin.source} PAIRS[{index}]"
        ok, bad = _ok_bad_sides(raw, where)
        _refuse_banned_slug(ok["slug"], ok["domain"], f"{where}.ok")
        _refuse_banned_slug(bad["slug"], bad["domain"], f"{where}.bad")
        seen.claim(ok, bad)
        rows.append(origin.pair_row(index, ok, bad))
    return tuple(rows)


def _plants_from_s_calls(raw_pairs: ast.List, origin: _Origin) -> tuple[dict[str, Any], ...]:
    rows = []
    seen = _SeenIdentities()
    for index, raw in enumerate(raw_pairs.elts):
        where = f"{origin.source} PAIRS[{index}]"
        if not _is_s_pair(raw):
            raise CeiRefusal(
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{where} is not an (S, S) leftover leftover leftover tuple",
            )
        ok_node, bad_node = raw.elts
        ok = expand_leftover3(
            _call_args(ok_node, S_OK_ARG_NAMES, f"{where}.ok"),
            ticket_required=False,
        )
        bad = expand_leftover3(
            _call_args(bad_node, S_BAD_ARG_NAMES, f"{where}.bad"),
            ticket_required=True,
        )
        _refuse_leftover3_slug(ok["slug"], f"{where}.ok")
        _refuse_leftover3_slug(bad["slug"], f"{where}.bad")
        seen.claim(ok, bad)
        rows.append(origin.leftover3_row(index, ok, bad))
    return tuple(rows)


def _plants_from_dict_leftover3(
    raw_pairs: ast.List, origin: _Origin
) -> tuple[dict[str, Any], ...]:
    """Dict-pair leftover3 mills; pairs naming a banned slug are skipped, not refused."""

    source = origin.source
    rows: list[dict[str, Any]] = []
    seen = _SeenIdentities()
    for raw in raw_pairs.elts:
        if not _is_dict_leftover3_pair(raw):
            raise CeiRefusal(
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{source} PAIRS[{len(rows)}] is not a leftover leftover leftover dict tuple",
            )
        ok_raw = _const_eval(raw.elts[0])
        bad_raw = _const_eval(raw.elts[1])
        if ok_raw.get("slug") in LEFTOVER3_BANNED_SLUGS or bad_raw.get("slug") in LEFTOVER3_BANNED_SLUGS:
            continue
        ok = expand_leftover3(ok_raw, ticket_required=False)
        bad = expand_leftover3(bad_raw, ticket_required=True)
        _refuse_leftover3_slug(ok["slug"], f"{source} PAIRS.ok")
        _refuse_leftover3_slug(bad["slug"], f"{source} PAIRS.bad")
        seen.claim(ok, bad)
        rows.append(origin.leftover3_row(len(rows), ok, bad))
    if not rows:
        raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no committable leftover dict pairs")
    return tuple(rows)


def _ok_label() -> str:
    return f"{OK_CALL}(...), {BAD_CALL}(...)"


def _field(mapping: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
    if not isinstance(mapping, dict):
        raise CeiRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where} must be an object")
    if key not in mapping:
        raise CeiRefusal(FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    value = mapping[key]
    if isinstance(value, bool) and kinds is not bool:
        raise CeiRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    if not isinstance(value, kinds):
        raise CeiRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    return value


def _require_text(value: Any, where: str, code: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CeiRefusal(code, f"{where} must be a non-empty stripped string")
    return value


def _require_payload(value: Any, where: str, code: str) -> str:
    """Prose or source payload. May keep indent or a trailing newline."""

    if not isinstance(value, str) or not value.strip() or "\r" in value:
        raise CeiRefusal(code, f"{where} must be a non-empty LF string")
    return value


_LEFTOVER3_IDENTITY_KEYS = frozenset({"slug", "mod", "test", "url", "url2", "ticket"})
_SIDE_IDENTITY_KEYS = frozenset({"slug", "mod", "test_fn", "docs_url", "docs_url2", "ticket"})


def _check_side_keys(row: Any, keys: tuple[str, ...], where: str) -> None:
    """A side is an object carrying exactly ``keys``."""

    if not isinstance(row, dict):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    missing = [key for key in keys if key not in row]
    if missing:
        raise CeiRefusal(FINDING_PLANT_FIELD_MISSING, f"{where} missing {missing[0]}")
    extra = [key for key in row if key not in keys]
    if extra:
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} has extra {extra[0]}")


def _text_field(
    row: Mapping[str, Any], key: str, where: str, identity_keys: frozenset[str]
) -> str:
    """Identity keys are stripped one-liners; every other key is an LF payload."""

    checker = _require_text if key in identity_keys else _require_payload
    return checker(row[key], f"{where}.{key}", FINDING_PLANT_FIELD_INVALID)


def _leftover3_side_from_row(row: Any, keys: tuple[str, ...], where: str) -> Leftover3Side:
    _check_side_keys(row, keys, where)
    fields = {key: _text_field(row, key, where, _LEFTOVER3_IDENTITY_KEYS) for key in keys}
    slug = fields["slug"]
    if not SLUG_RE.fullmatch(slug):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.slug is not a plant slug")
    _refuse_leftover3_slug(slug, where)
    if fields["wrong"] != LEFTOVER3_WRONG:
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.wrong must be {LEFTOVER3_WRONG!r}")
    outcome = fields.pop("ok")
    ticket = fields.pop("ticket", None)
    return Leftover3Side(**fields, outcome=outcome, ticket=ticket)


def _side_field(row: Mapping[str, Any], key: str, where: str) -> Any:
    if key != "coverage":
        return _text_field(row, key, where, _SIDE_IDENTITY_KEYS)
    coverage = row[key]
    if not isinstance(coverage, int) or isinstance(coverage, bool) or coverage < 1:
        raise CeiRefusal(
            FINDING_PLANT_FIELD_INVALID, f"{where}.coverage must be a positive int"
        )
    return coverage


def _side_from_row(row: Any, keys: tuple[str, ...], where: str) -> Side:
    _check_side_keys(row, keys, where)
    fields = {key: _side_field(row, key, where) for key in keys}
    slug = fields["slug"]
    if not SLUG_RE.fullmatch(slug):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.slug is not a plant slug")
    _refuse_banned_slug(slug, fields["domain"], where)
    if fields["first_old"] not in fields["src_body"]:
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.first_old is not in src_body")
    ticket = fields.pop("ticket", None)
    ticket_why = fields.pop("ticket_why", None)
    return Side(**fields, ticket=ticket, ticket_why=ticket_why)


def _is_int_at_least(value: Any, minimum: int) -> TypeGuard[int]:
    """An int (never a bool) of at least ``minimum``."""

    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _plant_sides(
    row: Mapping[str, Any], where: str
) -> tuple[str, Side | Leftover3Side, Side | Leftover3Side]:
    shape = row.get("shape", SHAPE_OK_BAD)
    if shape == LEFTOVER3_SHAPE:
        return (
            shape,
            _leftover3_side_from_row(row.get("ok"), LEFTOVER3_OK_KEYS, f"{where}.ok"),
            _leftover3_side_from_row(row.get("bad"), LEFTOVER3_BAD_KEYS, f"{where}.bad"),
        )
    if shape == SHAPE_OK_BAD:
        return (
            shape,
            _side_from_row(row.get("ok"), OK_SIDE_KEYS, f"{where}.ok"),
            _side_from_row(row.get("bad"), BAD_SIDE_KEYS, f"{where}.bad"),
        )
    raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.shape {shape!r} is not a CEI shape")


def _plant_from_row(row: Any, where: str) -> Plant:
    if not isinstance(row, dict):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_PLANT_FIELD_INVALID)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.mill_id is not cei_rNNN")
    shape, ok, bad = _plant_sides(row, where)
    plant_id = _require_text(row.get("plant_id"), f"{where}.plant_id", FINDING_PLANT_FIELD_INVALID)
    expected = f"{mill_id}:{ok.slug}"
    if plant_id != expected:
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.plant_id must be {expected!r}")
    base_round = row.get("base_round")
    if not _is_int_at_least(base_round, 1):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.base_round must be a positive int")
    index = row.get("index")
    if not _is_int_at_least(index, 0):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.index must be a non-negative int")
    return Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=_require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING),
        base_round=base_round,
        index=index,
        shape=shape,
        ok=ok,
        bad=bad,
    )


def _mill_from_row(row: Any, where: str) -> Mill:
    mill_id = _require_text(
        _field(row, "mill_id", str, where), f"{where}.mill_id", FINDING_CATALOG_FIELD_INVALID
    )
    if not MILL_ID_RE.fullmatch(mill_id):
        raise CeiRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.mill_id is not cei_rNNN")
    base_round = _field(row, "base_round", int, where)
    if isinstance(base_round, bool) or base_round < 1:
        raise CeiRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{where}.base_round must be a positive int"
        )
    plant_count = _field(row, "plant_count", int, where)
    if isinstance(plant_count, bool) or plant_count < 1:
        raise CeiRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{where}.plant_count must be a positive int"
        )
    return Mill(
        mill_id=mill_id,
        base_round=base_round,
        source=_require_text(
            _field(row, "source", str, where), f"{where}.source", FINDING_CATALOG_FIELD_INVALID
        ),
        plant_count=plant_count,
    )


def _read_jsonl(path: Path) -> tuple[Any, ...]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CeiRefusal(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}") from exc
    if not text.endswith("\n") or "\r" in text:
        raise CeiRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name} must be LF-framed jsonl")
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise CeiRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError as exc:
            raise CeiRefusal(
                FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is not strict JSON"
            ) from exc
    return tuple(rows)


def _registry_factory_ids() -> set[str]:
    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        payload = load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CeiRefusal(
            FINDING_FACTORY_NOT_REGISTERED, f"factory registry is unreadable: {exc}"
        ) from exc
    factories = payload.get("factories") if isinstance(payload, dict) else None
    if not isinstance(factories, list):
        raise CeiRefusal(FINDING_FACTORY_NOT_REGISTERED, "factory registry factories is not a list")
    return {
        path_id
        for row in factories
        if isinstance(row, dict) and isinstance(path_id := row.get("path_id"), str)
    }


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    catalog_dir = Path(default_catalog_dir() if directory is None else directory)
    meta_path = catalog_dir / CATALOG_FILENAME
    plants_path = catalog_dir / PLANTS_FILENAME
    try:
        meta_text = meta_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CeiRefusal(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing") from exc
    try:
        meta = load_strict_json(meta_text)
    except ValueError as exc:
        raise CeiRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON"
        ) from exc
    return _catalog_from_meta(catalog_dir, plants_path, meta)


def _meta_pins(meta: Any) -> tuple[str, str, int, str]:
    """The header pins, then the plant count and plants digest the header declares."""

    catalog_id = _require_text(
        _field(meta, "catalog_id", str, CATALOG_FILENAME),
        f"{CATALOG_FILENAME}.catalog_id",
        FINDING_CATALOG_FIELD_INVALID,
    )
    fmt = _field(meta, "format", str, CATALOG_FILENAME)
    if fmt != CATALOG_FORMAT:
        raise CeiRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.format must be {CATALOG_FORMAT}",
        )
    factory = _field(meta, "factory", str, CATALOG_FILENAME)
    if factory != FACTORY:
        raise CeiRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME}.factory must be {FACTORY}"
        )
    prefix = _field(meta, "mill_prefix", str, CATALOG_FILENAME)
    if prefix != MILL_PREFIX:
        raise CeiRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.mill_prefix must be {MILL_PREFIX}",
        )
    kind = _field(meta, "record_kind", str, CATALOG_FILENAME)
    if kind != RECORD_KIND:
        raise CeiRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.record_kind must be {RECORD_KIND}",
        )
    quota = _field(meta, "quota_per_round", int, CATALOG_FILENAME)
    if isinstance(quota, bool) or quota != QUOTA_PER_ROUND:
        raise CeiRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.quota_per_round must be {QUOTA_PER_ROUND}",
        )
    plant_count = _field(meta, "plant_count", int, CATALOG_FILENAME)
    plants_sha256 = _field(meta, "plants_sha256", str, CATALOG_FILENAME)
    return catalog_id, factory, plant_count, plants_sha256


def _catalog_from_meta(catalog_dir: Path, plants_path: Path, meta: Any) -> Catalog:
    """Bind the plants file to the pins ``CATALOG.json`` declares."""

    catalog_id, factory, plant_count, plants_sha256 = _meta_pins(meta)
    mill_rows = _field(meta, "mills", list, CATALOG_FILENAME)
    mills = tuple(
        _mill_from_row(row, f"{CATALOG_FILENAME}.mills[{i}]") for i, row in enumerate(mill_rows)
    )
    digest = _pinned_plants_digest(plants_path, plants_sha256)
    if factory not in _registry_factory_ids():
        raise CeiRefusal(FINDING_FACTORY_NOT_REGISTERED, f"{factory} is not a registry path_id")
    rows = _read_jsonl(plants_path)
    if len(rows) != plant_count:
        raise CeiRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.plant_count is {plant_count}, file has {len(rows)}",
        )
    plants = tuple(
        _plant_from_row(row, f"{PLANTS_FILENAME}:{i}") for i, row in enumerate(rows, start=1)
    )
    _refuse_duplicate_identities(plants)
    _refuse_mill_pins(mills, plants)
    return Catalog(
        catalog_id=catalog_id,
        directory=catalog_dir,
        factory=factory,
        plants_sha256=digest,
        plants=plants,
        mills=mills,
        meta=meta,
    )


def _pinned_plants_digest(plants_path: Path, plants_sha256: str) -> str:
    try:
        plants_bytes = plants_path.read_bytes()
    except OSError as exc:
        raise CeiRefusal(FINDING_CATALOG_FILE_MISSING, f"{plants_path} is missing") from exc
    digest = sha256_bytes(plants_bytes)
    if digest != plants_sha256:
        raise CeiRefusal(
            FINDING_CATALOG_SHA256_MISMATCH,
            f"{PLANTS_FILENAME} digest {digest} != catalog pin {plants_sha256}",
        )
    return digest


def _refuse_duplicate_identities(plants: tuple[Plant, ...]) -> None:
    """No plant_id, and no slug on either side, appears twice in the catalog."""

    seen: set[str] = set()
    seen_slugs: set[str] = set()
    for plant in plants:
        if plant.plant_id in seen:
            raise CeiRefusal(FINDING_PLANT_DUPLICATE_ID, f"duplicate plant_id {plant.plant_id}")
        seen.add(plant.plant_id)
        for slug in (plant.ok.slug, plant.bad.slug):
            if slug in seen_slugs:
                raise CeiRefusal(FINDING_PLANT_DUPLICATE_ID, f"duplicate slug {slug}")
            seen_slugs.add(slug)


def _refuse_mill_pins(mills: tuple[Mill, ...], plants: tuple[Plant, ...]) -> None:
    """Catalog mills are exactly the plants' mills, with their counts and base rounds."""

    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    mill_ids = {mill.mill_id for mill in mills}
    if mill_ids != set(by_mill):
        raise CeiRefusal(
            FINDING_CATALOG_FIELD_INVALID, "catalog mills do not match plant mill_id values"
        )
    for mill in mills:
        if by_mill[mill.mill_id] != mill.plant_count:
            raise CeiRefusal(
                FINDING_CATALOG_FIELD_INVALID,
                f"{mill.mill_id} plant_count {mill.plant_count} != {by_mill[mill.mill_id]}",
            )
        _refuse_mill_base_round(mill, plants)


def _refuse_mill_base_round(mill: Mill, plants: tuple[Plant, ...]) -> None:
    for plant in plants:
        if plant.mill_id == mill.mill_id and plant.base_round != mill.base_round:
            raise CeiRefusal(
                FINDING_CATALOG_FIELD_INVALID,
                f"{plant.plant_id} base_round != mill base_round",
            )


def catalog_check(directory: Path | None = None) -> list[dict[str, str]]:
    """Load the catalog. An invalid catalog is a refusal, not a finding list."""

    loaded = load_catalog(directory)
    if loaded.plants:
        return []
    return [{"code": FINDING_CATALOG_FIELD_INVALID, "detail": "empty catalog"}]


bind_import_twin(__name__)
