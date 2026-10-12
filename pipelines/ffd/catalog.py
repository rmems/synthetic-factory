#!/usr/bin/env python3
"""Pinned FFD mill catalog: AST extract, load, and check.

The three leftover-execution mills on ``origin/legacy-mill-lane`` stay on
that branch. This module parses their source with :mod:`ast`, evaluates only
the catalog constructors (never the reserve/publish loop), and loads the
committed JSON under ``config/ffd/``. No ``ffd-mill*.py`` file is vendored.
"""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    CATALOG_FORMAT,
    CATALOG_ID,
    FACTORY,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_INPUT_NOT_AN_OBJECT,
    FINDING_SLUG_COLLISION,
    FINDING_SOURCE_UNPARSEABLE,
    GENERATOR,
    PREFIX,
    SOURCES,
    bind_import_twin,
    default_catalog_dir,
    dumps_exact_json,
    finding_row,
    load_strict_json,
    refuse,
    refuse_when,
    shown,
)

CATALOG_FILENAME = "CATALOG.json"
LEFTOVER3_FILENAME = "leftover3-pairs.jsonl"
LLL_FILENAME = "lll-pairs.jsonl"
HOP_PLANTS_FILENAME = "hop-plants.jsonl"
HOP_PAIRS_FILENAME = "hop-pairs.jsonl"
# CATALOG.json ``files`` key -> committed file name, in load and write order.
_CATALOG_FILES = {
    "leftover3_pairs": LEFTOVER3_FILENAME,
    "lll_pairs": LLL_FILENAME,
    "hop_plants": HOP_PLANTS_FILENAME,
    "hop_pairs": HOP_PAIRS_FILENAME,
}
_META_IDENTITY = (
    ("format", CATALOG_FORMAT),
    ("catalog_id", CATALOG_ID),
    ("factory", FACTORY),
    ("generator", GENERATOR),
)
LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
LEGACY_REF = "origin/legacy-mill-lane"

SOURCE_PATHS = {
    "leftover3": "experiments/ffd-mill-leftover3-r41.py",
    "lll": "experiments/ffd-mill-lll-r61.py",
    "hop": "experiments/ffd-mill-hop-r102.py",
}
CATALOG_FIRST = {"leftover3": 41, "lll": 61, "hop": 102}

__all__ = [
    "CATALOG_FILENAME",
    "Catalog",
    "SOURCE_PATHS",
    "catalog_check",
    "extract_hop",
    "extract_leftover3",
    "extract_lll",
    "extract_source",
    "load_catalog",
    "sha256_bytes",
    "sha256_text",
    "write_extracted",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError) as exc:
        raise SyntaxError(f"catalog node is not a literal: {ast.dump(node)[:80]}") from exc


def _target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return None


def _assign_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Assign):
        return [name for name in (_target_name(t) for t in node.targets) if name]
    if isinstance(node, ast.AnnAssign):
        name = _target_name(node.target)
        return [name] if name else []
    return []


def _is_extend(node: ast.AST, name: str) -> bool:
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return False
    func = node.value.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "extend"
        and isinstance(func.value, ast.Name)
        and func.value.id == name
    )


def _is_catalog_node(node: ast.stmt, keep_names: set[str], keep_fns: set[str]) -> bool:
    if isinstance(node, ast.FunctionDef) and node.name in keep_fns:
        return True
    if any(name in keep_names for name in _assign_names(node)):
        return True
    return any(_is_extend(node, name) for name in keep_names)


def _exec_catalog_nodes(source: str, keep_names: set[str], keep_fns: set[str]) -> dict[str, Any]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_UNPARSEABLE, f"legacy mill source is unparseable: {exc}")
    keep = [node for node in tree.body if _is_catalog_node(node, keep_names, keep_fns)]
    module = ast.Module(body=keep, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict[str, Any] = {}
    try:
        exec(compile(module, "<ffd-ast-extract>", "exec"), namespace, namespace)  # noqa: S102
    except Exception as exc:
        refuse(FINDING_SOURCE_UNPARSEABLE, f"catalog constructors failed: {exc}")
    return namespace


def _constant_tuple(source: str, name: str) -> tuple[Any, ...]:
    tree = ast.parse(source)
    for node in tree.body:
        if name in _assign_names(node) and isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if value is None:
                break
            literal = _literal(value)
            return tuple(literal)
    return ()


def _extract_pairs(source: str, label: str, keep_fns: set[str]) -> list[dict[str, Any]]:
    """Evaluate ``PAIRS`` through ``keep_fns`` and copy each ``(ok, bad)`` tuple."""

    namespace = _exec_catalog_nodes(source, {"PAIRS"}, keep_fns)
    pairs = namespace.get("PAIRS")
    refuse_when(not isinstance(pairs, list) or not pairs, FINDING_SOURCE_UNPARSEABLE,
                f"{label} PAIRS is missing or empty")
    out: list[dict[str, Any]] = []
    for item in pairs:
        refuse_when(not isinstance(item, tuple) or len(item) != 2, FINDING_SOURCE_UNPARSEABLE,
                    f"{label} pair is not an (ok, bad) tuple")
        ok, bad = item
        refuse_when(not isinstance(ok, dict) or not isinstance(bad, dict),
                    FINDING_SOURCE_UNPARSEABLE, f"{label} pair members must be objects")
        out.append({"ok": dict(ok), "bad": dict(bad)})
    return out


def extract_leftover3(source: str) -> list[dict[str, Any]]:
    """AST-extract leftover3 ``PAIRS`` via ``_ok`` / ``_bad`` / ``_pair`` only."""

    return _extract_pairs(source, "leftover3", {"_p", "_ok", "_bad", "_pair"})


def extract_lll(source: str) -> list[dict[str, Any]]:
    """AST-extract leftover-leftover-leftover ``PAIRS`` via ``pair`` only."""

    return _extract_pairs(source, "lll", {"pair"})


def _is_fn_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return False
    return node.func.id == "fn" and len(node.args) == 1


def _fn_key(node: ast.AST) -> str:
    refuse_when(
        not _is_fn_call(node),
        FINDING_SOURCE_UNPARSEABLE,
        "hop LHC_PAIRS entry is not fn(<plant-key>)",
    )
    return str(_literal(node.args[0]))


def _hop_pair_row(elt: ast.AST, plant_rows: Mapping[str, Any]) -> dict[str, Any]:
    refuse_when(not isinstance(elt, ast.Tuple) or len(elt.elts) < 6,
                FINDING_SOURCE_UNPARSEABLE, "hop LHC_PAIRS row is short")
    title = _literal(elt.elts[0])
    ok_key = _fn_key(elt.elts[1])
    bad_key = _fn_key(elt.elts[2])
    densify = _literal(elt.elts[3])
    loops = _literal(elt.elts[4])
    nxt = _literal(elt.elts[5])
    refuse_when(ok_key not in plant_rows or bad_key not in plant_rows,
                FINDING_SOURCE_UNPARSEABLE, f"hop pair names unknown plants {ok_key!r}/{bad_key!r}")
    return {
        "title": title,
        "ok": ok_key,
        "bad": bad_key,
        "densify": densify,
        "loops": loops,
        "next": nxt,
    }


def _hop_pairs(source: str, plant_rows: Mapping[str, Any]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for node in ast.parse(source).body:
        if "LHC_PAIRS" not in _assign_names(node):
            continue
        value = node.value
        refuse_when(not isinstance(value, ast.List), FINDING_SOURCE_UNPARSEABLE,
                    "hop LHC_PAIRS is not a list")
        pairs.extend(_hop_pair_row(elt, plant_rows) for elt in value.elts)
    return pairs


def extract_hop(source: str) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], tuple[str, ...]]:
    """AST-extract hop ``PLANTS`` via ``mk`` / ``P`` and ``LHC_PAIRS`` keys."""

    namespace = _exec_catalog_nodes(source, {"PLANTS"}, {"P", "mk"})
    plants = namespace.get("PLANTS")
    refuse_when(not isinstance(plants, dict) or not plants, FINDING_SOURCE_UNPARSEABLE,
                "hop PLANTS is missing or empty")
    plant_rows = {str(key): dict(value) for key, value in plants.items()}
    pairs = _hop_pairs(source, plant_rows)
    banned = _constant_tuple(source, "BANNED_SUB")
    return plant_rows, pairs, tuple(str(item) for item in banned)


def extract_source(source_id: str, source: str) -> dict[str, Any]:
    """Dispatch one mill source text to the matching AST extract."""

    if source_id == "leftover3":
        return {"pairs": extract_leftover3(source)}
    if source_id == "lll":
        return {"pairs": extract_lll(source)}
    if source_id == "hop":
        plants, pairs, banned = extract_hop(source)
        return {"plants": plants, "pairs": pairs, "banned_sub": list(banned)}
    refuse(FINDING_SOURCE_UNPARSEABLE, f"unknown extract source {shown(source_id)}")


def _field(mapping: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
    refuse_when(not isinstance(mapping, dict), FINDING_INPUT_NOT_AN_OBJECT, f"{where} must be an object")
    refuse_when(key not in mapping, FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    value = mapping[key]
    refuse_when(
        (not isinstance(value, kinds)) or (isinstance(value, bool) and kinds is not bool),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where}.{key} has the wrong type",
    )
    return value


def _load_jsonl(path: Path, digest: str, where: str) -> list[Any]:
    refuse_when(not path.is_file(), FINDING_CATALOG_FILE_MISSING, f"{path} is missing")
    payload = path.read_bytes()
    refuse_when(sha256_bytes(payload) != digest, FINDING_CATALOG_SHA256_MISMATCH,
                f"{where} sha256 does not match CATALOG.json")
    rows: list[Any] = []
    text = payload.decode("utf-8")
    refuse_when(not text.endswith("\n") or "\r" in text, FINDING_CATALOG_FIELD_INVALID,
                f"{where} must be LF-framed with a final newline")
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line:
            refuse(FINDING_CATALOG_FIELD_INVALID, f"{where}:{lineno} is empty")
        rows.append(load_strict_json(line))
    return rows


def _jsonl_bytes(rows: list[Any]) -> bytes:
    lines = [dumps_exact_json(row, ensure_ascii=True, sort_keys=True) for row in rows]
    return ("\n".join(lines) + "\n").encode("utf-8")


@dataclass(frozen=True)
class Catalog:
    """The committed FFD mill catalog: three leftover-execution sources."""

    catalog_dir: Path
    meta: Mapping[str, Any]
    leftover3: tuple[Mapping[str, Any], ...]
    lll: tuple[Mapping[str, Any], ...]
    hop_plants: Mapping[str, Mapping[str, Any]]
    hop_pairs: tuple[Mapping[str, Any], ...]
    banned_sub: tuple[str, ...]

    @property
    def catalog_id(self) -> str:
        return str(self.meta["catalog_id"])

    def pairs_of(self, source_id: str) -> tuple[Mapping[str, Any], ...]:
        if source_id == "leftover3":
            return self.leftover3
        if source_id == "lll":
            return self.lll
        if source_id == "hop":
            return self.hop_pairs
        refuse(FINDING_CATALOG_FIELD_INVALID, f"unknown source {shown(source_id)}")

    def catalog_first(self, source_id: str) -> int:
        sources = _field(self.meta, "sources", dict, "CATALOG.json")
        row = _field(sources, source_id, dict, f"CATALOG.json.sources.{source_id}")
        return int(_field(row, "catalog_first", int, f"CATALOG.json.sources.{source_id}"))


def _check_meta_identity(meta: Any) -> None:
    refuse_when(not isinstance(meta, dict), FINDING_INPUT_NOT_AN_OBJECT, "CATALOG.json must be an object")
    for key, expected in _META_IDENTITY:
        refuse_when(meta.get(key) != expected, FINDING_CATALOG_FIELD_INVALID,
                    f"CATALOG.json.{key} must be {expected}")


def _pinned_rows(directory: Path, files: Any, digests: Any, file_key: str) -> list[Any]:
    """Load one catalog JSONL file named by ``files`` and pinned by ``digests``."""

    return _load_jsonl(
        directory / _field(files, file_key, str, "CATALOG.json.files"),
        _field(digests, f"{file_key}_sha256", str, "CATALOG.json.digests"),
        _CATALOG_FILES[file_key],
    )


def _hop_plants_by_id(rows: list[Any]) -> dict[str, dict[str, Any]]:
    hop_plants = {}
    for row in rows:
        refuse_when(not isinstance(row, dict) or "id" not in row, FINDING_CATALOG_FIELD_INVALID,
                    "hop plant row must carry id")
        plant_id = row["id"]
        hop_plants[str(plant_id)] = {key: value for key, value in row.items() if key != "id"}
    return hop_plants


def load_catalog(catalog_dir: Path | None = None) -> Catalog:
    """Load the committed catalog and bind each JSONL file to its pin."""

    directory = Path(catalog_dir) if catalog_dir is not None else default_catalog_dir()
    meta_path = directory / CATALOG_FILENAME
    refuse_when(not meta_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing")
    meta = load_strict_json(meta_path.read_text(encoding="utf-8"))
    _check_meta_identity(meta)
    files = _field(meta, "files", dict, "CATALOG.json")
    digests = _field(meta, "digests", dict, "CATALOG.json")
    rows = {key: _pinned_rows(directory, files, digests, key) for key in _CATALOG_FILES}
    hop_plants = _hop_plants_by_id(rows["hop_plants"])
    banned = tuple(_field(meta, "banned_sub", list, "CATALOG.json"))
    return Catalog(
        catalog_dir=directory,
        meta=meta,
        leftover3=tuple(rows["leftover3_pairs"]),
        lll=tuple(rows["lll_pairs"]),
        hop_plants=hop_plants,
        hop_pairs=tuple(rows["hop_pairs"]),
        banned_sub=tuple(str(item) for item in banned),
    )


def _require_keys(row: Mapping[str, Any], keys: tuple[str, ...], where: str) -> None:
    missing = [key for key in keys if key not in row]
    refuse_when(bool(missing), FINDING_CATALOG_FIELD_MISSING, f"{where} missing {missing}")


_LEFTOVER3_OK_KEYS = (
    "slug", "goal", "plan", "mod", "test_fn", "src_body", "first_old", "first_new",
    "seed", "domain", "stack", "residual", "coverage", "plan_change",
)
_LEFTOVER3_BAD_KEYS = _LEFTOVER3_OK_KEYS + ("ticket", "ticket_why")
_LLL_KEYS = ("slug", "domain", "stack", "seed", "leftover", "token", "ticket", "wrong", "right")
_HOP_PAIR_KEYS = ("title", "ok", "bad", "densify", "loops", "next")
_HOP_PLANT_KEYS = ("slug", "ok", "leftover", "what", "impl", "goal", "plan")


class _CatalogAudit:
    """Accumulates findings and slugs while one ``catalog_check`` walks the sources."""

    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self.findings: list[dict[str, str]] = []
        self.slugs: list[str] = []

    def flag(self, source_id: str, detail: str) -> None:
        self.findings.append(finding_row(FINDING_CATALOG_FIELD_INVALID, source_id, detail))

    def check_source(self, source_id: str) -> None:
        pairs = self.catalog.pairs_of(source_id)
        refuse_when(not pairs, FINDING_CATALOG_FIELD_INVALID, f"{source_id} has no pairs")
        for index, pair in enumerate(pairs):
            where = f"{source_id}[{index}]"
            refuse_when(not isinstance(pair, Mapping), FINDING_INPUT_NOT_AN_OBJECT,
                        f"{where} must be an object")
            if source_id == "hop":
                self.check_hop_pair(where, pair)
            else:
                self.check_mill_pair(source_id, where, pair)

    def check_hop_plant(self, where: str, pair: Mapping[str, Any], side: str) -> None:
        plant_id = str(pair[side])
        refuse_when(plant_id not in self.catalog.hop_plants, FINDING_CATALOG_FIELD_INVALID,
                    f"{where}.{side} names unknown plant {plant_id!r}")
        plant = self.catalog.hop_plants[plant_id]
        _require_keys(plant, _HOP_PLANT_KEYS, f"{where}.{side}")
        self.slugs.append(str(plant["slug"]))
        low = str(plant["slug"]).lower()
        for ban in self.catalog.banned_sub:
            if ban in low:
                self.flag("hop", f"banned token {ban} in {plant['slug']}")

    def check_hop_pair(self, where: str, pair: Mapping[str, Any]) -> None:
        _require_keys(pair, _HOP_PAIR_KEYS, where)
        for side in ("ok", "bad"):
            self.check_hop_plant(where, pair, side)
        ok_flag = self.catalog.hop_plants[str(pair["ok"])]["ok"]
        bad_flag = self.catalog.hop_plants[str(pair["bad"])]["ok"]
        if ok_flag == bad_flag:
            self.flag("hop", f"{where} success flags are not opposite")

    def check_mill_pair(self, source_id: str, where: str, pair: Mapping[str, Any]) -> None:
        _require_keys(pair, ("ok", "bad"), where)
        ok, bad = pair["ok"], pair["bad"]
        keys = _LEFTOVER3_OK_KEYS if source_id == "leftover3" else _LLL_KEYS
        bad_keys = _LEFTOVER3_BAD_KEYS if source_id == "leftover3" else _LLL_KEYS
        _require_keys(ok, keys, f"{where}.ok")
        _require_keys(bad, bad_keys, f"{where}.bad")
        self.slugs.append(str(ok["slug"]))
        self.slugs.append(str(bad["slug"]))
        if source_id == "leftover3":
            for row in (ok, bad):
                if row["first_old"] not in row["src_body"]:
                    self.flag(source_id, f"{row['slug']} first_old not in src_body")


def catalog_check(catalog: Catalog) -> list[dict[str, str]]:
    """Structural uniqueness and required-field check; empty when the catalog is clean."""

    audit = _CatalogAudit(catalog)
    try:
        for source_id in SOURCES:
            audit.check_source(source_id)
        if len(audit.slugs) != len(set(audit.slugs)):
            audit.findings.append(finding_row(FINDING_SLUG_COLLISION, "catalog", "catalog slugs collide"))
    except Exception as exc:
        audit.findings.append(finding_row(
            getattr(exc, "code", FINDING_CATALOG_FIELD_INVALID), "catalog", str(exc),
        ))
    return audit.findings


def _catalog_meta(sources_meta: dict[str, Any], pair_counts: dict[str, int],
                  payloads: dict[str, bytes], banned_sub: tuple[str, ...]) -> dict[str, Any]:
    return {
        "catalog_id": CATALOG_ID,
        "format": CATALOG_FORMAT,
        "family": "ffd",
        "factory": FACTORY,
        "prefix": PREFIX,
        "generator": GENERATOR,
        "legacy": {"ref": LEGACY_REF, "commit": LEGACY_COMMIT},
        "sources": sources_meta,
        "pair_counts": pair_counts,
        "files": dict(_CATALOG_FILES),
        "digests": {f"{key}_sha256": sha256_bytes(payloads[key]) for key in _CATALOG_FILES},
        "banned_sub": list(banned_sub),
    }


def write_extracted(catalog_dir: Path, leftover3: list[dict[str, Any]], lll: list[dict[str, Any]],
                    hop_plants: dict[str, dict[str, Any]], hop_pairs: list[dict[str, Any]],
                    banned_sub: tuple[str, ...], sources_meta: dict[str, Any]) -> None:
    """Write a brand-new catalog directory from AST-extracted rows."""

    refuse_when(catalog_dir.exists(), FINDING_CATALOG_FIELD_INVALID,
                f"{catalog_dir} already exists")
    catalog_dir.mkdir(parents=True)
    payloads = {
        "leftover3_pairs": _jsonl_bytes(leftover3),
        "lll_pairs": _jsonl_bytes(lll),
        "hop_plants": _jsonl_bytes([{"id": key, **value} for key, value in hop_plants.items()]),
        "hop_pairs": _jsonl_bytes(hop_pairs),
    }
    for key, filename in _CATALOG_FILES.items():
        (catalog_dir / filename).write_bytes(payloads[key])
    pair_counts = {"leftover3": len(leftover3), "lll": len(lll), "hop": len(hop_pairs)}
    meta = _catalog_meta(sources_meta, pair_counts, payloads, banned_sub)
    (catalog_dir / CATALOG_FILENAME).write_text(
        dumps_exact_json(meta, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


bind_import_twin(__name__)
