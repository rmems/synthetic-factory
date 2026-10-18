#!/usr/bin/env python3
"""NELB plant catalog: AST extract of recovered builders (never exec).

``plants_from_source`` walks a recovered mill as text (``ast.parse`` only,
``exec: false``). The committed catalog is compact JSONL beside
``CATALOG.json`` under ``pipelines/nelb/``. Recovered ``*mill*.py`` /
``gen_r*.py`` scripts are not vendored.
"""

from __future__ import annotations

import ast
import functools
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_ID,
    FACTORY,
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_CATALOG_TRIPLE_STRIDE,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_TRIPLE_OUT_OF_DOMAIN,
    GENERATOR,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    NelbRefusal,
    bind_import_twin,
    default_catalog_dir,
    load_strict_json,
    refuse,
    refuse_first,
    refuse_when,
    sha256_bytes,
    shown,
)

ID_PREFIX = "nelb"
LEAD_DECISIONS = frozenset({"ACCEPT", "MODIFY", "REJECT"})
SIM_OR_REAL = frozenset({"designed", "hil", "simulated"})
PLANT_FIELDS = (
    "record_id",
    "source_round",
    "index",
    "site",
    "domain",
    "sim_or_real",
    "reconstruction",
    "formula",
    "lead_decision",
    "companion_decision",
    "companion_key",
    "goal",
    "source_name",
)

__all__ = [
    "CATALOG_ID",
    "FACTORY",
    "GENERATOR",
    "ID_PREFIX",
    "PLANT_FIELDS",
    "QUOTA_PER_ROUND",
    "WAVE_ROUNDS",
    "Catalog",
    "Plant",
    "catalog_check",
    "default_catalog_dir",
    "load_catalog",
    "plant_from_mapping",
    "plants_for_round",
    "plants_from_source",
    "sha256_bytes",
]


@dataclass(frozen=True)
class Plant:
    """One AST-extracted NELB pair identity. Full recovered payloads stay out."""

    record_id: str
    source_round: int
    index: int
    site: str
    domain: str
    sim_or_real: str
    reconstruction: str
    formula: str
    lead_decision: str
    companion_decision: str
    companion_key: str
    goal: str
    source_name: str

    def as_mapping(self) -> dict[str, Any]:
        return {field: getattr(self, field) for field in PLANT_FIELDS}


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    plants: tuple[Plant, ...]

    def plant(self, record_id: str) -> Plant:
        for item in self.plants:
            if item.record_id == record_id:
                return item
        refuse(FINDING_FIELD_INVALID, f"no plant {shown(record_id)} in the catalog")


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError) as exc:
        refuse(FINDING_AST_NOT_A_PLANT, f"catalog argument is not a literal: {exc}")


def _text(value: Any) -> str:
    return value if isinstance(value, str) and value.strip() else ""


def _assigned(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    return None


def _optional_const(value: ast.AST, consts: Mapping[str, Any]) -> Any:
    if isinstance(value, ast.Name) and value.id in consts:
        return consts[value.id]
    try:
        return _literal(value)
    except NelbRefusal:
        return None


def _str_key(node: ast.AST | None) -> str | None:
    """The text of a string-constant dict key; None for any other key node."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _constant_is(node: ast.AST | None, value: Any) -> bool:
    return isinstance(node, ast.Constant) and node.value == value


def _names(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _str_keyed_entries(node: ast.Dict) -> list[tuple[str, ast.expr]]:
    """The entries of a dict literal whose keys are string constants, in source order."""

    entries: list[tuple[str, ast.expr]] = []
    for key_node, value_node in zip(node.keys, node.values):
        key = _str_key(key_node)
        if key is not None:
            entries.append((key, value_node))
    return entries


def _dict_literal(node: ast.AST, consts: Mapping[str, Any]) -> dict[str, Any] | None:
    """String-keyed entries that resolve to a constant or (recursively) a nested dict literal."""

    if not isinstance(node, ast.Dict) or any(key is None for key in node.keys):
        return None
    row: dict[str, Any] = {}
    for key, value_node in _str_keyed_entries(node):
        value = _optional_const(value_node, consts)
        if value is None and isinstance(value_node, ast.Dict):
            value = _dict_literal(value_node, consts)
        if value is not None:
            row[key] = value
    return row


def _dict_field(mapping: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = mapping.get(key)
    return value if isinstance(value, dict) else {}


def _site_from_setting(setting: str) -> str:
    head = setting.split(".", 1)[0].strip()
    if "(" in head:
        head = head.split("(", 1)[0].strip().rstrip(",")
    elif "," in head:
        head = head.split(",", 1)[0].strip()
    return head


def _index_from_name(name: str) -> int | None:
    digits = "".join(ch for ch in name.split("_", 1)[-1] if ch.isdigit())
    return int(digits) if digits else None


def _round_from_id(record_id: str) -> int | None:
    if not record_id.startswith("nelb-r"):
        return None
    token = record_id[6:].split("-", 1)[0]
    digits = "".join(ch for ch in token if ch.isdigit())
    return int(digits) if digits else None


_DRAFT_TEXT_FIELDS = (
    "site",
    "domain",
    "sim_or_real",
    "reconstruction",
    "formula",
    "lead_decision",
    "companion_decision",
    "companion_key",
    "goal",
)


def _plant_draft(
    round_n: int,
    index: int,
    source_name: str,
    extracted: Mapping[str, Any],
) -> dict[str, Any]:
    """A plant row from the fields an extractor found; absent fields default to empty."""

    text = {field: _text(extracted.get(field)) for field in _DRAFT_TEXT_FIELDS}
    return {
        "record_id": extracted.get("record_id") or f"nelb-r{round_n:02d}-{index:03d}",
        "source_round": round_n,
        "index": index,
        "site": text["site"],
        "domain": text["domain"],
        "sim_or_real": text["sim_or_real"] or "designed",
        "reconstruction": text["reconstruction"],
        "formula": text["formula"],
        "lead_decision": text["lead_decision"],
        "companion_decision": text["companion_decision"],
        "companion_key": text["companion_key"] or "trajectory_companion",
        "goal": text["goal"],
        "source_name": source_name,
    }


def _decision_of(traj: Mapping[str, Any]) -> str:
    return _text(_dict_field(traj, "safety_decision").get("decision"))


def _has_decision(value: Any) -> bool:
    return isinstance(value, dict) and "safety_decision" in value


def _view_companion(view: Mapping[str, Any]) -> tuple[str, dict[str, Any]] | None:
    """The first non-lead language-view entry that carries a safety decision."""

    for key, value in view.items():
        if key != "trajectory" and _has_decision(value):
            return key, value
    return None


def _language_view_dicts(returned: ast.Dict) -> Iterator[ast.Dict]:
    for key_node, value_node in zip(returned.keys, returned.values):
        if _constant_is(key_node, "language_view") and isinstance(value_node, ast.Dict):
            yield value_node


def _trajectory_key(view_node: ast.Dict) -> str | None:
    for nested_key, nested_value in zip(view_node.keys, view_node.values):
        key = _str_key(nested_key)
        if key is None or key in {"description", "trajectory"}:
            continue
        if key.startswith("trajectory_") or _names(nested_value, "traj2"):
            return key
    return None


def _companion_key(returned: ast.Dict, view: Mapping[str, Any]) -> str:
    """Name the companion trajectory key without executing the mill."""

    for view_node in _language_view_dicts(returned):
        key = _trajectory_key(view_node)
        if key is not None:
            return key
    found = _view_companion(view)
    return "" if found is None else found[0]


def _return_dict(node: ast.AST, assigns: Mapping[str, ast.AST]) -> ast.Dict | None:
    if not isinstance(node, ast.Return):
        return None
    if isinstance(node.value, ast.Name):
        bound = assigns.get(node.value.id)
        return bound if isinstance(bound, ast.Dict) else None
    return node.value if isinstance(node.value, ast.Dict) else None


def _returned_dict(fn: ast.FunctionDef, assigns: Mapping[str, ast.AST]) -> ast.Dict | None:
    """The last ``return`` of a dict literal, directly or through a local name."""

    for node in reversed(fn.body):
        returned = _return_dict(node, assigns)
        if returned is not None:
            return returned
    return None


def _assigned_dict(
    assigns: Mapping[str, ast.AST], name: str, consts: Mapping[str, Any]
) -> Mapping[str, Any]:
    """The resolvable entries of the dict literal a builder binds to ``name``; else empty."""
    node = assigns.get(name)
    if node is None:
        return {}
    return _dict_literal(node, consts) or {}


def _rec_trajectories(
    returned: ast.Dict,
    view: Mapping[str, Any],
    assigns: Mapping[str, ast.AST],
    consts: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any], str]:
    """The lead and companion trajectories and the companion key of one builder."""

    traj = _assigned_dict(assigns, "traj", consts)
    traj2 = _assigned_dict(assigns, "traj2", consts)
    if not traj and isinstance(view.get("trajectory"), dict):
        traj = view["trajectory"]
    companion_key = _companion_key(returned, view)
    if not traj2:
        found = _view_companion(view)
        if found is not None:
            companion_key = companion_key or found[0]
            traj2 = found[1]
    return traj, traj2, companion_key


def _rec_round(record_id: Any, round_n: int) -> int:
    """The round a builder's own ``nelb-rNN`` id names, else the module's round."""

    inferred = _round_from_id(record_id) if isinstance(record_id, str) else None
    return inferred or round_n


def _from_rec_func(
    fn: ast.FunctionDef,
    consts: Mapping[str, Any],
    round_n: int,
    source_name: str,
) -> dict[str, Any] | None:
    assigns = dict(
        item for node in fn.body if (item := _assigned(node)) is not None
    )
    returned = _returned_dict(fn, assigns)
    if returned is None:
        return None
    rec = _dict_literal(returned, consts) or {}
    view = _dict_field(rec, "language_view")
    traj, traj2, companion_key = _rec_trajectories(returned, view, assigns, consts)
    state = _dict_field(traj, "state")
    recon = _dict_field(rec, "reconstruction_model")
    notes = _dict_field(rec, "bridge_notes")
    record_id = rec.get("id")
    return _plant_draft(
        _rec_round(record_id, round_n),
        _index_from_name(fn.name) or 1,
        source_name,
        {
            "record_id": record_id,
            "site": _site_from_setting(_text(state.get("setting"))),
            "domain": state.get("domain"),
            "sim_or_real": state.get("sim_or_real"),
            "reconstruction": recon.get("name"),
            "formula": recon.get("formula"),
            "lead_decision": _decision_of(traj),
            "companion_decision": _decision_of(traj2),
            "companion_key": companion_key,
            "goal": notes.get("why_high_value") or view.get("description"),
        },
    )


def _pairs_row_draft(
    row: Mapping[str, Any], offset: int, round_n: int, source_name: str
) -> dict[str, Any]:
    state = _dict_field(row, "state")
    return _plant_draft(
        round_n,
        row["index"] if type(row.get("index")) is int else offset,
        source_name,
        {
            "record_id": row.get("id") or row.get("record_id"),
            "site": row.get("site") or _site_from_setting(_text(state.get("setting"))),
            "domain": row.get("domain") or state.get("domain"),
            "sim_or_real": row.get("sim_or_real") or state.get("sim_or_real"),
            "reconstruction": row.get("reconstruction"),
            "formula": row.get("formula"),
            "lead_decision": row.get("lead_decision"),
            "companion_decision": row.get("companion_decision"),
            "companion_key": row.get("companion_key"),
            "goal": row.get("goal"),
        },
    )


def _from_pairs_dicts(
    pairs: ast.List,
    consts: Mapping[str, Any],
    round_n: int,
    source_name: str,
) -> list[dict[str, Any]]:
    plants: list[dict[str, Any]] = []
    for offset, elt in enumerate(pairs.elts, start=1):
        row = _dict_literal(elt, consts)
        if row is not None:
            plants.append(_pairs_row_draft(row, offset, round_n, source_name))
    return plants


def _module_bindings(
    tree: ast.Module,
) -> tuple[dict[str, Any], dict[str, ast.AST], list[ast.FunctionDef]]:
    """Top-level constants, raw assigned nodes, and ``rec_*`` builders, in source order."""

    consts: dict[str, Any] = {}
    raw: dict[str, ast.AST] = {}
    rec_funcs: list[ast.FunctionDef] = []
    for node in tree.body:
        item = _assigned(node)
        if item is not None:
            name, value = item
            raw[name] = value
            resolved = _optional_const(value, consts)
            if resolved is not None:
                consts[name] = resolved
        elif isinstance(node, ast.FunctionDef) and node.name.startswith("rec_"):
            rec_funcs.append(node)
    return consts, raw, rec_funcs


def _rec_func_drafts(
    rec_funcs: list[ast.FunctionDef],
    consts: Mapping[str, Any],
    round_n: int,
    source_name: str,
) -> list[dict[str, Any]]:
    plants: list[dict[str, Any]] = []
    for index, fn in enumerate(rec_funcs, start=1):
        row = _from_rec_func(fn, consts, round_n, source_name)
        if row is not None:
            row["index"] = index
            plants.append(row)
    return plants


def plants_from_source(text: str, source_name: str = "snippet") -> tuple[Plant, ...]:
    """AST-extract one 3-pair NELB identity catalog. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_AST_NOT_A_PLANT, f"mill source is not parseable: {exc}")
    consts, raw, rec_funcs = _module_bindings(tree)
    factory = consts.get("FACTORY")
    refuse_when(
        factory not in (None, FACTORY),
        FINDING_AST_NOT_A_PLANT,
        f"{source_name} FACTORY is {shown(factory)}",
    )
    round_n = consts.get("ROUND")
    if type(round_n) is not int:
        round_n = 1
    plants = _rec_func_drafts(rec_funcs, consts, round_n, source_name)
    pairs = raw.get("PAIRS")
    if len(plants) != QUOTA_PER_ROUND and isinstance(pairs, ast.List):
        plants = _from_pairs_dicts(pairs, consts, round_n, source_name)
    refuse_when(
        len(plants) != QUOTA_PER_ROUND,
        FINDING_CATALOG_TRIPLE_STRIDE,
        f"{source_name} did not yield a 3-pair catalog",
    )
    return tuple(
        plant_from_mapping(row, f"{source_name}[{index}]")
        for index, row in enumerate(plants)
    )


def _require_identity(values: Mapping[str, Any], where: str) -> None:
    record_id = values["record_id"]
    refuse_when(
        not isinstance(record_id, str) or not record_id.startswith("nelb-r"),
        FINDING_FIELD_INVALID,
        f"{where}.record_id must be a nelb-r id, got {shown(record_id)}",
    )
    source_round = values["source_round"]
    refuse_when(
        type(source_round) is not int or source_round < 1,
        FINDING_FIELD_INVALID,
        f"{where}.source_round must be a positive int, got {shown(source_round)}",
    )
    index = values["index"]
    refuse_when(
        type(index) is not int or not 1 <= index <= 3,
        FINDING_FIELD_INVALID,
        f"{where}.index must be 1..3, got {shown(index)}",
    )


def _require_decisions(values: Mapping[str, Any], where: str) -> None:
    sim = values["sim_or_real"]
    refuse_when(
        sim not in SIM_OR_REAL,
        FINDING_FIELD_INVALID,
        f"{where}.sim_or_real must be designed/hil/simulated, got {shown(sim)}",
    )
    lead = values["lead_decision"]
    refuse_when(
        lead not in LEAD_DECISIONS,
        FINDING_FIELD_INVALID,
        f"{where}.lead_decision must be ACCEPT/MODIFY/REJECT, got {shown(lead)}",
    )
    companion = values["companion_decision"]
    refuse_when(
        companion not in LEAD_DECISIONS,
        FINDING_FIELD_INVALID,
        f"{where}.companion_decision must be ACCEPT/MODIFY/REJECT, got {shown(companion)}",
    )


def _require_strings(values: Mapping[str, Any], where: str) -> dict[str, Any]:
    """Every field in ``PLANT_FIELDS`` order; all but the two ints must be strings."""

    checked = {}
    for field in PLANT_FIELDS:
        value = values[field]
        if field not in {"source_round", "index"}:
            refuse_when(
                not isinstance(value, str),
                FINDING_FIELD_INVALID,
                f"{where}.{field} must be a string, got {shown(value)}",
            )
        checked[field] = value
    return checked


def _require_plant_fields(values: Mapping[str, Any], where: str) -> dict[str, Any]:
    missing = [field for field in PLANT_FIELDS if field not in values]
    refuse_when(bool(missing), FINDING_FIELD_MISSING, f"{where} missing {missing}")
    _require_identity(values, where)
    _require_decisions(values, where)
    checked = _require_strings(values, where)
    refuse_when(
        not checked["domain"] and not checked["reconstruction"],
        FINDING_FIELD_MISSING,
        f"{where} needs domain or reconstruction",
    )
    return checked


def plant_from_mapping(values: Mapping[str, Any], where: str = "plant") -> Plant:
    """Validate one mapping (AST row or committed row) into a frozen plant."""

    return Plant(**_require_plant_fields(values, where))


def _check_unique(plants: tuple[Plant, ...]) -> None:
    seen: dict[str, int] = {}
    for plant in plants:
        if plant.record_id in seen:
            refuse(
                FINDING_DUPLICATE_ID,
                f"record_id {shown(plant.record_id)} repeats "
                f"(r{seen[plant.record_id]} and r{plant.source_round})",
            )
        seen[plant.record_id] = plant.source_round


def catalog_check(plants: tuple[Plant, ...] | None = None) -> dict[str, Any]:
    """Fail closed unless every row has identity and a 3-stride."""

    items = load_catalog().plants if plants is None else plants
    refuse_when(not items, FINDING_CATALOG_EMPTY, "catalog has no plants")
    refuse_when(
        len(items) % QUOTA_PER_ROUND != 0,
        FINDING_CATALOG_TRIPLE_STRIDE,
        f"catalog length {len(items)} is not a multiple of {QUOTA_PER_ROUND}",
    )
    _check_unique(items)
    rounds = tuple(sorted({plant.source_round for plant in items}))
    for rnd in rounds:
        chunk = tuple(plant for plant in items if plant.source_round == rnd)
        refuse_when(
            len(chunk) != QUOTA_PER_ROUND,
            FINDING_CATALOG_TRIPLE_STRIDE,
            f"r{rnd} has {len(chunk)} plants, not {QUOTA_PER_ROUND}",
        )
    return {
        "status": "ok",
        "catalog_id": CATALOG_ID,
        "plants": len(items),
        "triples": len(items) // QUOTA_PER_ROUND,
        "rounds": list(rounds),
        "first_round": rounds[0],
        "last_round": rounds[-1],
        "factory": FACTORY,
        "generator": GENERATOR,
    }


def plants_for_round(round_n: int, plants: tuple[Plant, ...] | None = None) -> tuple[Plant, ...]:
    items = load_catalog().plants if plants is None else plants
    rounds = tuple(sorted({plant.source_round for plant in items}))
    refuse_first(
        (
            (
                type(round_n) is not int,
                FINDING_ROUND_OUT_OF_DOMAIN,
                f"round must be an int, got {shown(round_n)}",
            ),
            (
                type(round_n) is int and round_n not in rounds,
                FINDING_ROUND_OUT_OF_DOMAIN,
                f"round must be one of {list(rounds)}, got {shown(round_n)}",
            ),
        )
    )
    chunk = tuple(plant for plant in items if plant.source_round == round_n)
    refuse_when(
        len(chunk) != QUOTA_PER_ROUND,
        FINDING_TRIPLE_OUT_OF_DOMAIN,
        f"no plant triple for r{round_n}",
    )
    return chunk


def _read_plants_jsonl(path: Path) -> tuple[Plant, ...]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}")
    refuse_when(
        not text.endswith("\n") or "\r" in text,
        FINDING_FIELD_INVALID,
        f"{path.name} must be LF-framed jsonl",
    )
    plants: list[Plant] = []
    for index, line in enumerate(text.splitlines(), start=1):
        refuse_when(not line, FINDING_FIELD_INVALID, f"{path.name}:{index} is empty")
        try:
            row = load_strict_json(line)
        except ValueError as exc:
            refuse(FINDING_FIELD_INVALID, f"{path.name}:{index} is not strict JSON: {exc}")
        refuse_when(
            not isinstance(row, dict),
            FINDING_FIELD_INVALID,
            f"{path.name}:{index} is not an object",
        )
        plants.append(plant_from_mapping(row, f"{path.name}:{index}"))
    _check_unique(tuple(plants))
    return tuple(plants)


def _load_committed_catalog(catalog_dir: Path | None = None) -> Catalog:
    root = default_catalog_dir() if catalog_dir is None else catalog_dir
    meta_path = root / CATALOG_FILENAME
    plants_path = root / PLANTS_FILENAME
    try:
        meta = load_strict_json(meta_path.read_text(encoding="utf-8"))
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is unreadable: {exc}")
    except ValueError as exc:
        refuse(FINDING_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON: {exc}")
    refuse_when(
        not isinstance(meta, dict),
        FINDING_FIELD_INVALID,
        f"{CATALOG_FILENAME} must be an object",
    )
    catalog_id = meta.get("catalog_id")
    refuse_when(
        catalog_id != CATALOG_ID,
        FINDING_FIELD_INVALID,
        f"{CATALOG_FILENAME} catalog_id is {shown(catalog_id)}",
    )
    pinned = meta.get("plants_sha256")
    refuse_when(
        not isinstance(pinned, str) or len(pinned) != 64,
        FINDING_FIELD_MISSING,
        f"{CATALOG_FILENAME} missing plants_sha256",
    )
    try:
        plants_raw = plants_path.read_bytes()
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{plants_path} is unreadable: {exc}")
    digest = sha256_bytes(plants_raw)
    refuse_when(
        digest != pinned,
        FINDING_CATALOG_SHA256_MISMATCH,
        f"{PLANTS_FILENAME} digest {digest} != pinned {pinned}",
    )
    plants = _read_plants_jsonl(plants_path)
    expected = meta.get("plant_count")
    refuse_when(
        type(expected) is int and expected != len(plants),
        FINDING_FIELD_INVALID,
        f"{CATALOG_FILENAME} plant_count {expected} != {len(plants)} rows",
    )
    return Catalog(CATALOG_ID, plants)


# Declared (never bound) so the export in ``__all__`` is visible to static
# analysis; ``__getattr__`` below computes it from the catalog on first access.
WAVE_ROUNDS: tuple[int, ...]


@functools.cache
def load_catalog() -> Catalog:
    """The committed catalog, loaded and pin-checked once per process."""
    return _load_committed_catalog()


def __getattr__(name: str) -> Any:
    if name == "WAVE_ROUNDS":
        return tuple(sorted({plant.source_round for plant in load_catalog().plants}))
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


bind_import_twin(__name__)
