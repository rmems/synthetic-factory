#!/usr/bin/env python3
"""Pinned MAOS first-slice catalog: AST extract plus committed JSONL.

``plants_from_source`` walks a recovered builder with ``ast.parse`` only
(``exec: false``). The committed slice lives in ``config/maos/`` as a
header plus one compact identity row per recovered round. Full rasters,
notes, and mill scripts stay off this branch.
"""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    CATALOG_ID,
    FACTORY,
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_ROUND_OUT_OF_DOMAIN,
    GENERATOR,
    MaosRefusal,
    bind_import_twin,
    load_strict_json,
    refuse,
    refuse_first,
    refuse_when,
    require_round,
    shown,
)

CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
DEFAULT_CATALOG_DIR = Path(__file__).resolve().parents[2] / "config" / "maos"
REQUIRED_META_FIELDS = (
    "catalog_id",
    "family",
    "schema",
    "factory",
    "generator",
    "plants",
    "rounds",
    "plants_filename",
    "plants_sha256",
)
PLANT_FIELDS = (
    "record_id",
    "title",
    "source_round",
    "factory",
    "generator",
    "run_label",
    "domain",
    "scenario",
    "sim_or_real",
    "decision",
    "decision_correctness",
    "generated_at",
    "spike_events",
    "raster_spikes",
    "source_path",
    "source_key",
    "source_blob",
    "source_sha256",
    "source_lines",
    "source_name",
)
ROW_KEYS = (
    "id",
    "title",
    "round",
    "factory",
    "generator",
    "run_label",
    "domain",
    "scenario",
    "sim_or_real",
    "decision",
    "decision_correctness",
    "generated_at",
    "spike_events",
    "raster_spikes",
    "source_path",
    "source_key",
    "source_blob",
    "source_sha256",
    "source_lines",
)

__all__ = [
    "CATALOG_FILENAME",
    "DEFAULT_CATALOG_DIR",
    "PLANTS_FILENAME",
    "Catalog",
    "Plant",
    "catalog_check",
    "load_catalog",
    "plants_for_round",
    "plants_from_source",
]


@dataclass(frozen=True)
class Plant:
    """One compact MAOS identity. Full recovered payloads stay out."""

    record_id: str
    title: str
    source_round: int
    factory: str
    generator: str
    run_label: str
    domain: str
    scenario: str
    sim_or_real: str
    decision: str
    decision_correctness: str
    generated_at: str
    spike_events: int
    raster_spikes: int
    source_path: str
    source_key: str
    source_blob: str
    source_sha256: str
    source_lines: int
    source_name: str

    def as_mapping(self) -> dict[str, Any]:
        return {field: getattr(self, field) for field in PLANT_FIELDS}


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    plants: tuple[Plant, ...]
    plants_sha256: str

    def plant(self, record_id: str) -> Plant:
        for item in self.plants:
            if item.record_id == record_id:
                return item
        refuse(FINDING_FIELD_INVALID, f"no plant {shown(record_id)} in the catalog")


def _assigned(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    return None


def _resolve(node: ast.AST, env: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in env:
        return env[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _resolve(node.operand, env)
        if isinstance(value, (int, float)):
            return -value
        refuse(FINDING_AST_NOT_A_PLANT, "unary minus is not numeric")
    if isinstance(node, ast.BinOp):
        left, right = _resolve(node.left, env), _resolve(node.right, env)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        refuse(FINDING_AST_NOT_A_PLANT, "unsupported binary operator")
    if isinstance(node, ast.List):
        return [_resolve(elt, env) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_resolve(elt, env) for elt in node.elts)
    if isinstance(node, ast.Dict):
        out: dict[Any, Any] = {}
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:
                refuse(FINDING_AST_NOT_A_PLANT, "starred dict is not a plant")
            out[_resolve(key_node, env)] = _resolve(value_node, env)
        return out
    refuse(FINDING_AST_NOT_A_PLANT, f"catalog argument is not a literal: {type(node).__name__}")


def _optional_resolve(node: ast.AST, env: Mapping[str, Any]) -> Any:
    try:
        return _resolve(node, env)
    except (MaosRefusal, TypeError, KeyError):
        return None


def _collect_env(nodes: list[ast.stmt], env: Mapping[str, Any] | None = None) -> dict[str, Any]:
    bound: dict[str, Any] = dict(env or {})
    for node in nodes:
        item = _assigned(node)
        if item is None:
            continue
        name, value = item
        resolved = _optional_resolve(value, bound)
        if resolved is not None:
            bound[name] = resolved
    return bound


def _build_record_fn(tree: ast.Module) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "build_record":
            return node
    refuse(FINDING_AST_NOT_A_PLANT, "source has no build_record function")


def _text(value: Any) -> str:
    return value if isinstance(value, str) and value.strip() else ""


def _count(value: Any) -> int:
    if type(value) is int:
        return value
    if isinstance(value, (list, tuple)):
        return len(value)
    if isinstance(value, dict) and type(value.get("spikes")) is int:
        return value["spikes"]
    return 0


def _plant_from_rec(rec: Mapping[str, Any], env: Mapping[str, Any], source_name: str) -> Plant:
    state = rec.get("state") if isinstance(rec.get("state"), dict) else {}
    meta = rec.get("meta") if isinstance(rec.get("meta"), dict) else {}
    decision = rec.get("safety_decision") if isinstance(rec.get("safety_decision"), dict) else {}
    record_id = _text(rec.get("id"))
    round_n = meta.get("round")
    refuse_when(not record_id, FINDING_FIELD_MISSING, f"{source_name} rec.id is missing")
    refuse_when(
        type(round_n) is not int or round_n < 1,
        FINDING_FIELD_INVALID,
        f"{source_name} meta.round is not a positive int",
    )
    factory = _text(meta.get("factory")) or FACTORY
    generator = _text(meta.get("generator")) or GENERATOR
    refuse_when(
        factory != FACTORY,
        FINDING_FIELD_INVALID,
        f"{source_name} factory {shown(factory)}",
    )
    refuse_when(
        generator != GENERATOR,
        FINDING_FIELD_INVALID,
        f"{source_name} generator {shown(generator)}",
    )
    return Plant(
        record_id=record_id,
        title=_text(rec.get("title")),
        source_round=round_n,
        factory=factory,
        generator=generator,
        run_label=_text(meta.get("run_label")),
        domain=_text(meta.get("domain") or state.get("domain")),
        scenario=_text(state.get("scenario_name") or meta.get("scenario")),
        sim_or_real=_text(state.get("sim_or_real")) or "designed",
        decision=_text(decision.get("decision")),
        decision_correctness=_text(decision.get("correctness")),
        generated_at=_text(env.get("GEN_AT")),
        spike_events=_count(rec.get("spike_events")),
        raster_spikes=_count(rec.get("raster")),
        source_path="",
        source_key="",
        source_blob="",
        source_sha256="",
        source_lines=0,
        source_name=source_name,
    )


def plants_from_source(text: str, source_name: str = "snippet") -> tuple[Plant, ...]:
    """AST-extract the ``rec`` identity from one recovered builder. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_AST_NOT_A_PLANT, f"mill source is not parseable: {exc}")
    env = _collect_env(list(tree.body))
    fn = _build_record_fn(tree)
    local = _collect_env(list(fn.body), env)
    rec = local.get("rec")
    refuse_when(
        not isinstance(rec, dict),
        FINDING_AST_NOT_A_PLANT,
        f"{source_name} has no rec dict",
    )
    return (_plant_from_rec(rec, local, source_name),)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _as_str(value: Any, label: str) -> str:
    refuse_when(
        not isinstance(value, str) or not value,
        FINDING_FIELD_INVALID,
        f"{label} must be a string",
    )
    return value


def _as_int(value: Any, label: str, *, minimum: int = 0) -> int:
    refuse_when(
        type(value) is not int or value < minimum,
        FINDING_FIELD_INVALID,
        f"{label} is not an int",
    )
    return value


def _require_keys(row: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    missing = [key for key in keys if key not in row]
    refuse_when(bool(missing), FINDING_FIELD_MISSING, f"{label} missing {missing}")


def _plant_from_row(row: Mapping[str, Any], lineno: int) -> Plant:
    _require_keys(row, ROW_KEYS, f"line {lineno}")
    record_id = _as_str(row["id"], f"line {lineno} id")
    refuse_when(
        not record_id.startswith("maos-r"),
        FINDING_FIELD_INVALID,
        f"line {lineno} id {shown(record_id)} is not a maos plant",
    )
    factory = _as_str(row["factory"], f"line {lineno} factory")
    generator = _as_str(row["generator"], f"line {lineno} generator")
    refuse_when(
        factory != FACTORY,
        FINDING_FIELD_INVALID,
        f"line {lineno} factory {shown(factory)}",
    )
    refuse_when(
        generator != GENERATOR,
        FINDING_FIELD_INVALID,
        f"line {lineno} generator {shown(generator)}",
    )
    return Plant(
        record_id=record_id,
        title=_as_str(row["title"], f"line {lineno} title"),
        source_round=_as_int(row["round"], f"line {lineno} round", minimum=1),
        factory=factory,
        generator=generator,
        run_label=_as_str(row["run_label"], f"line {lineno} run_label"),
        domain=_as_str(row["domain"], f"line {lineno} domain"),
        scenario=_as_str(row["scenario"], f"line {lineno} scenario"),
        sim_or_real=_as_str(row["sim_or_real"], f"line {lineno} sim_or_real"),
        decision=_as_str(row["decision"], f"line {lineno} decision"),
        decision_correctness=_as_str(
            row["decision_correctness"],
            f"line {lineno} decision_correctness",
        ),
        generated_at=_as_str(row["generated_at"], f"line {lineno} generated_at"),
        spike_events=_as_int(row["spike_events"], f"line {lineno} spike_events"),
        raster_spikes=_as_int(row["raster_spikes"], f"line {lineno} raster_spikes"),
        source_path=_as_str(row["source_path"], f"line {lineno} source_path"),
        source_key=_as_str(row["source_key"], f"line {lineno} source_key"),
        source_blob=_as_str(row["source_blob"], f"line {lineno} source_blob"),
        source_sha256=_as_str(row["source_sha256"], f"line {lineno} source_sha256"),
        source_lines=_as_int(row["source_lines"], f"line {lineno} source_lines", minimum=1),
        source_name=f"line {lineno}",
    )


def load_catalog(directory: Path | None = None) -> Catalog:
    catalog_dir = Path(directory) if directory is not None else DEFAULT_CATALOG_DIR
    catalog_path = catalog_dir / CATALOG_FILENAME
    plants_path = catalog_dir / PLANTS_FILENAME
    refuse_first((
        (not catalog_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {catalog_path}"),
        (not plants_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {plants_path}"),
    ))
    meta = load_strict_json(catalog_path.read_text(encoding="utf-8"))
    refuse_when(not isinstance(meta, dict), FINDING_FIELD_INVALID, "CATALOG.json must be an object")
    missing = [key for key in REQUIRED_META_FIELDS if key not in meta]
    refuse_when(bool(missing), FINDING_FIELD_MISSING, f"CATALOG.json missing {missing}")
    refuse_when(
        meta.get("catalog_id") != CATALOG_ID
        or meta.get("family") != "maos"
        or meta.get("schema") != "maos-plants-v1"
        or meta.get("factory") != FACTORY,
        FINDING_FIELD_INVALID,
        "unexpected catalog identity",
    )
    plants_bytes = plants_path.read_bytes()
    digest = _sha256_bytes(plants_bytes)
    refuse_when(
        meta.get("plants_sha256") != digest,
        FINDING_PLANTS_SHA_MISMATCH,
        f"plants.jsonl sha256 {digest} != pinned {meta.get('plants_sha256')}",
    )
    rows = [
        _plant_from_row(load_strict_json(line), lineno)
        for lineno, line in enumerate(plants_bytes.decode("utf-8").splitlines(), start=1)
        if line
    ]
    refuse_when(not rows, FINDING_CATALOG_EMPTY, "plants.jsonl has no rows")
    refuse_when(
        len(rows) != meta["plants"],
        FINDING_FIELD_INVALID,
        f"plants.jsonl has {len(rows)} rows; CATALOG.json says {meta['plants']}",
    )
    ids = [plant.record_id for plant in rows]
    refuse_when(len(set(ids)) != len(ids), FINDING_DUPLICATE_ID, "duplicate plant ids")
    return Catalog(CATALOG_ID, tuple(rows), digest)


def _check_unique(plants: tuple[Plant, ...]) -> None:
    ids = [plant.record_id for plant in plants]
    refuse_when(len(set(ids)) != len(ids), FINDING_DUPLICATE_ID, "duplicate plant ids")


def catalog_check(plants: tuple[Plant, ...] | None = None) -> dict[str, Any]:
    loaded = _CATALOG if plants is None else Catalog(CATALOG_ID, plants, "")
    _check_unique(loaded.plants)
    refuse_when(not loaded.plants, FINDING_CATALOG_EMPTY, "catalog has no plants")
    rounds = tuple(sorted({plant.source_round for plant in loaded.plants}))
    return {
        "status": "ok",
        "catalog_id": loaded.catalog_id,
        "plants": len(loaded.plants),
        "rounds": list(rounds),
        "first_round": rounds[0],
        "last_round": rounds[-1],
        "quota": 1,
    }


def plants_for_round(round_n: int, plants: tuple[Plant, ...] | None = None) -> tuple[Plant, ...]:
    require_round(round_n)
    loaded = plants if plants is not None else _CATALOG.plants
    matched = tuple(plant for plant in loaded if plant.source_round == round_n)
    refuse_when(
        not matched,
        FINDING_ROUND_OUT_OF_DOMAIN,
        f"round {round_n} is outside the recovered first slice",
    )
    return matched


_CATALOG = load_catalog()


bind_import_twin(__name__)
