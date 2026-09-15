#!/usr/bin/env python3
"""Pinned CEI pair catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` (identity, factory, mill pins)
and ``plants.jsonl`` (one ``_ok``/``_bad`` pair per line). Load verifies
the plants digest and every required field before a pair is trusted.
Historical hop-mill scripts are read only as text through
:func:`plants_from_source`.
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    BAD_ARG_NAMES,
    BAD_CALL,
    BAD_SIDE_KEYS,
    BANNED_SLUG_BITS,
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    FACTORY,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_DUPLICATE_ID,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    MILL_PREFIX,
    NOVEL_COVERAGE_BAD,
    NOVEL_COVERAGE_OK,
    OK_ARG_NAMES,
    OK_CALL,
    OK_SIDE_KEYS,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    SOURCE_ROUND,
    CeiRefusal,
    bind_import_twin,
    load_strict_json,
    repo_root,
)

MILL_ID_RE = re.compile(r"^cei_r[0-9]+$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

__all__ = [
    "Catalog",
    "Mill",
    "Plant",
    "Side",
    "catalog_check",
    "default_catalog_dir",
    "expand_bad",
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
class Plant:
    """One AST-extracted CEI pair (success side + handoff side)."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    index: int
    ok: Side
    bad: Side


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


def expand_ok(args: Mapping[str, Any]) -> dict[str, Any]:
    """Faithful ``_ok`` expansion from ``cei-mill-r81``. Never exec."""

    missing = [name for name in OK_ARG_NAMES if name not in args]
    if missing:
        raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"_ok missing {missing[0]}")
    slug = args["slug"]
    goal = args["goal"]
    mod = args["mod"]
    stack = args["stack"]
    docs = args["docs"]
    first_old = args["first_old"]
    first_new = args["first_new"]
    fix_new = args["fix_new"]
    extra = {key: args[key] for key in args if key not in OK_ARG_NAMES}
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

    missing = [name for name in BAD_ARG_NAMES if name not in args]
    if missing:
        raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"_bad missing {missing[0]}")
    slug = args["slug"]
    goal = args["goal"]
    mod = args["mod"]
    stack = args["stack"]
    docs = args["docs"]
    first_old = args["first_old"]
    first_new = args["first_new"]
    ticket = args["ticket"]
    extra = {key: args[key] for key in args if key not in BAD_ARG_NAMES}
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
        "docs_ok2": (
            f"Do not unlink. Handoff {ticket}. Not leftover leftover leftover clones."
        ),
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


def _const_eval(node: ast.AST) -> Any:
    """Literal values only. Never exec, compile, or eval."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        if any(key is None for key in node.keys):
            raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, "pair source uses dict unpacking")
        return {_const_eval(key): _const_eval(value) for key, value in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand)
    raise CeiRefusal(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"pair source is not a constant ({type(node).__name__})",
    )


def _assigned_name(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        if node.value is not None:
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


def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract ``PAIRS`` of ``_ok``/``_bad`` calls. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise CeiRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}"
        ) from exc
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
    if not isinstance(raw_pairs, ast.List) or not raw_pairs.elts:
        raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no PAIRS list")
    if not MILL_ID_RE.fullmatch(mill_id):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not cei_rNNN")
    base = inferred_base if base_round is None else base_round
    if base is None:
        base = SOURCE_ROUND
    if not isinstance(base, int) or isinstance(base, bool) or base < 1:
        raise CeiRefusal(
            FINDING_PLANT_FIELD_INVALID, f"{source} CATALOG_FIRST must be a positive int"
        )
    rows = []
    seen_slugs: set[str] = set()
    seen_mods: set[str] = set()
    seen_tickets: set[str] = set()
    for index, raw in enumerate(raw_pairs.elts):
        if not isinstance(raw, ast.Tuple) or len(raw.elts) != 2:
            raise CeiRefusal(
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{source} PAIRS[{index}] is not an (_ok, _bad) tuple",
            )
        ok_node, bad_node = raw.elts
        if not isinstance(ok_node, ast.Call) or not isinstance(ok_node.func, ast.Name):
            raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} PAIRS[{index}][0]")
        if not isinstance(bad_node, ast.Call) or not isinstance(bad_node.func, ast.Name):
            raise CeiRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} PAIRS[{index}][1]")
        if ok_node.func.id != OK_CALL or bad_node.func.id != BAD_CALL:
            raise CeiRefusal(
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{source} PAIRS[{index}] must be {_ok_label()}",
            )
        ok = expand_ok(_call_args(ok_node, OK_ARG_NAMES, f"{source} PAIRS[{index}].ok"))
        bad = expand_bad(_call_args(bad_node, BAD_ARG_NAMES, f"{source} PAIRS[{index}].bad"))
        if ok["first_old"] not in ok["src_body"] or bad["first_old"] not in bad["src_body"]:
            raise CeiRefusal(
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{source} PAIRS[{index}] first_old is not in src_body",
            )
        _refuse_banned_slug(ok["slug"], ok["domain"], f"{source} PAIRS[{index}].ok")
        _refuse_banned_slug(bad["slug"], bad["domain"], f"{source} PAIRS[{index}].bad")
        for slug in (ok["slug"], bad["slug"]):
            if slug in seen_slugs:
                raise CeiRefusal(FINDING_PLANT_DUPLICATE_ID, f"duplicate slug {slug}")
            seen_slugs.add(slug)
        for mod in (ok["mod"], bad["mod"]):
            if mod in seen_mods:
                raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"duplicate mod {mod}")
            seen_mods.add(mod)
        ticket = bad["ticket"]
        if ticket in seen_tickets:
            raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"duplicate ticket {ticket}")
        seen_tickets.add(ticket)
        rows.append(
            {
                "plant_id": f"{mill_id}:{ok['slug']}",
                "mill_id": mill_id,
                "source": source,
                "base_round": base,
                "index": index,
                "ok": ok,
                "bad": bad,
            }
        )
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


def _side_from_row(row: Any, keys: tuple[str, ...], where: str) -> Side:
    if not isinstance(row, dict):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    missing = [key for key in keys if key not in row]
    if missing:
        raise CeiRefusal(FINDING_PLANT_FIELD_MISSING, f"{where} missing {missing[0]}")
    extra = [key for key in row if key not in keys]
    if extra:
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} has extra {extra[0]}")
    identity_keys = frozenset({"slug", "mod", "test_fn", "docs_url", "docs_url2", "ticket"})
    fields: dict[str, Any] = {}
    for key in keys:
        if key == "coverage":
            coverage = row[key]
            if not isinstance(coverage, int) or isinstance(coverage, bool) or coverage < 1:
                raise CeiRefusal(
                    FINDING_PLANT_FIELD_INVALID, f"{where}.coverage must be a positive int"
                )
            fields[key] = coverage
            continue
        checker = _require_text if key in identity_keys else _require_payload
        fields[key] = checker(row[key], f"{where}.{key}", FINDING_PLANT_FIELD_INVALID)
    slug = fields["slug"]
    if not SLUG_RE.fullmatch(slug):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.slug is not a plant slug")
    _refuse_banned_slug(slug, fields["domain"], where)
    if fields["first_old"] not in fields["src_body"]:
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.first_old is not in src_body")
    ticket = fields.pop("ticket", None)
    ticket_why = fields.pop("ticket_why", None)
    return Side(**fields, ticket=ticket, ticket_why=ticket_why)


def _plant_from_row(row: Any, where: str) -> Plant:
    if not isinstance(row, dict):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_PLANT_FIELD_INVALID)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.mill_id is not cei_rNNN")
    ok = _side_from_row(row.get("ok"), OK_SIDE_KEYS, f"{where}.ok")
    bad = _side_from_row(row.get("bad"), BAD_SIDE_KEYS, f"{where}.bad")
    plant_id = _require_text(row.get("plant_id"), f"{where}.plant_id", FINDING_PLANT_FIELD_INVALID)
    expected = f"{mill_id}:{ok.slug}"
    if plant_id != expected:
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.plant_id must be {expected!r}")
    base_round = row.get("base_round")
    if not isinstance(base_round, int) or isinstance(base_round, bool) or base_round < 1:
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.base_round must be a positive int")
    index = row.get("index")
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        raise CeiRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.index must be a non-negative int")
    return Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=_require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING),
        base_round=base_round,
        index=index,
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
        row.get("path_id")
        for row in factories
        if isinstance(row, dict) and isinstance(row.get("path_id"), str)
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
    mill_rows = _field(meta, "mills", list, CATALOG_FILENAME)
    mills = tuple(
        _mill_from_row(row, f"{CATALOG_FILENAME}.mills[{i}]") for i, row in enumerate(mill_rows)
    )
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
        for plant in plants:
            if plant.mill_id == mill.mill_id and plant.base_round != mill.base_round:
                raise CeiRefusal(
                    FINDING_CATALOG_FIELD_INVALID,
                    f"{plant.plant_id} base_round != mill base_round",
                )
    return Catalog(
        catalog_id=catalog_id,
        directory=catalog_dir,
        factory=factory,
        plants_sha256=digest,
        plants=plants,
        mills=mills,
        meta=meta,
    )


def catalog_check(directory: Path | None = None) -> list[dict[str, str]]:
    """Load the catalog. An invalid catalog is a refusal, not a finding list."""

    loaded = load_catalog(directory)
    if loaded.plants:
        return []
    return [{"code": FINDING_CATALOG_FIELD_INVALID, "detail": "empty catalog"}]


bind_import_twin(__name__)
