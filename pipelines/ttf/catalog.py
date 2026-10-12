#!/usr/bin/env python3
"""TTF plant catalog: AST extract plus compact committed JSONL.

``plants_from_source`` walks a recovered generator as text (``ast.parse``
only, ``exec: false``). The committed catalog is ``plants.jsonl`` under
this package, covering every recover-grok mill catalog on
``origin/codex/recover-grok-01a06111``. Recovered ``*mill*.py`` /
``*loop*.py`` scripts are not vendored.
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_ID,
    CATALOG_SCHEMA,
    FACTORY,
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SLICE_STRIDE,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_SLICE_OUT_OF_DOMAIN,
    FAMILY_PREFIX,
    FULL_PLANT_COUNT,
    GENERATOR,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    SLICE_IDS,
    SOURCE_CATALOGS,
    TtfRefusal,
    bind_import_twin,
    default_catalog_dir,
    load_strict_json,
    refuse,
    refuse_first,
    refuse_when,
    shown,
)

ID_PREFIX = "ttf"
PLANT_FIELDS = (
    "record_id",
    "source_round",
    "index",
    "title",
    "domain",
    "sim_or_real",
    "goal",
    "proposed_action",
    "decision",
    "correctness",
    "rationale",
    "executed_action",
    "outcome",
    "reward_total",
    "reward_note",
    "source_name",
)
SIM_OR_REAL = frozenset({"designed", "hil", "simulated"})
DECISIONS = frozenset({"ACCEPT", "MODIFY", "REJECT"})
CORRECTNESS = frozenset({"correct", "incorrect"})
REC_NAME_RE = re.compile(r"^REC_(\d+)$")
BUILDER_NAME_RE = re.compile(r"^rec_(\d+)$")
RECORD_ID_RE = re.compile(
    r"^ttf-r(?P<round>[0-9]+)(?P<suffix>[a-z]*)-(?P<index>[0-9]+)$"
)
TOTAL_RE = re.compile(r"total ([+-]?\d+\.\d+)")
SOURCE_FILE_BY_SLICE = {item[0]: item[1] for item in SOURCE_CATALOGS}

__all__ = [
    "CATALOG_FILENAME",
    "CATALOG_ID",
    "FACTORY",
    "GENERATOR",
    "ID_PREFIX",
    "PLANT_FIELDS",
    "PLANTS_FILENAME",
    "QUOTA_PER_ROUND",
    "SLICE_IDS",
    "Catalog",
    "Plant",
    "catalog_check",
    "load_catalog",
    "plant_from_mapping",
    "plants_for_round",
    "plants_for_slice",
    "plants_from_source",
    "slice_from_record_id",
]


@dataclass(frozen=True)
class Plant:
    """One AST-extracted TTF identity. Full recovered rasters stay out."""

    record_id: str
    source_round: int
    index: int
    title: str
    domain: str
    sim_or_real: str
    goal: str
    proposed_action: str
    decision: str
    correctness: str
    rationale: str
    executed_action: str
    outcome: str
    reward_total: float
    reward_note: str
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
    except TtfRefusal:
        return None


_SKIPPED_KEYS = frozenset({"spike_events", "spikes", "raster", "excerpt"})
_BUILDER_KEYS = frozenset({"id", "domain", "sim_or_real", "decision", "goal"})


def _negated_number(node: ast.UnaryOp) -> Any:
    """``-<int or float literal>``; any other unary expression walks to None."""
    if not isinstance(node.op, ast.USub) or not isinstance(node.operand, ast.Constant):
        return None
    value = node.operand.value
    return -value if isinstance(value, (int, float)) else None


_Parts = tuple[Sequence[ast.AST], Callable[[list[Any]], Any]]


def _leaf(value: Any) -> _Parts:
    return (), lambda _values: value


def _call_parts(node: ast.Call) -> _Parts:
    """Positional args, then named keyword values (``**`` entries stay out)."""
    func = node.func.id if isinstance(node.func, ast.Name) else None
    named = [keyword for keyword in node.keywords if keyword.arg]
    count = len(node.args)

    def rebuild(values: list[Any]) -> dict[str, Any]:
        kwargs = {keyword.arg: value for keyword, value in zip(named, values[count:])}
        return {"_call": func, "args": values[:count], "kwargs": kwargs}

    return [*node.args, *(keyword.value for keyword in named)], rebuild


def _walk_parts(node: ast.AST, consts: Mapping[str, Any]) -> _Parts:
    """Any node but a tuple or dict as (child nodes, rebuild); unknown nodes walk to None.

    ``_walk_mapping`` walks the children itself, so a nesting level costs one frame.
    """
    if isinstance(node, ast.Name) and node.id in consts:
        return _leaf(consts[node.id])
    if isinstance(node, ast.Constant):
        return _leaf(node.value)
    if isinstance(node, ast.UnaryOp):
        return _leaf(_negated_number(node))
    if isinstance(node, ast.List):
        return node.elts, list
    return _call_parts(node) if isinstance(node, ast.Call) else _leaf(None)


def _kept_key(key: Any) -> bool:
    return isinstance(key, str) and key not in _SKIPPED_KEYS


def _keyed_entries(node: ast.Dict) -> list[tuple[ast.expr, ast.expr]]:
    """Dict entries with a key node; ``**`` entries are skipped."""
    return [(key, value) for key, value in zip(node.keys, node.values) if key is not None]


def _walk_mapping(node: ast.AST, consts: Mapping[str, Any]) -> Any:
    """Best-effort literal walk. Calls and names stay out (no exec)."""

    if isinstance(node, ast.Tuple):
        return tuple(_walk_mapping(elt, consts) for elt in node.elts)
    if isinstance(node, ast.Dict):
        mapping: dict[str, Any] = {}
        for key_node, value_node in _keyed_entries(node):
            key = _walk_mapping(key_node, consts)
            if _kept_key(key):
                mapping[key] = _walk_mapping(value_node, consts)
        return mapping
    children, rebuild = _walk_parts(node, consts)
    return rebuild([_walk_mapping(child, consts) for child in children])


def _reward_note(reward: Any) -> str:
    if isinstance(reward, dict):
        args = reward.get("args")
        if isinstance(args, list) and len(args) >= 4 and isinstance(args[3], str):
            return args[3]
        note = reward.get("notes")
        if isinstance(note, str):
            return note
    return _text(reward)


def _reward_total(note: str) -> float | None:
    match = TOTAL_RE.search(note)
    return float(match.group(1)) if match else None


def _round_from_id(record_id: str) -> int | None:
    match = RECORD_ID_RE.match(record_id)
    return int(match.group("round")) if match else None


def slice_from_record_id(record_id: str) -> str:
    match = RECORD_ID_RE.match(record_id)
    refuse_when(
        match is None,
        FINDING_FIELD_INVALID,
        f"record_id must be a ttf-r id, got {shown(record_id)}",
    )
    assert match is not None
    return f"r{match.group('round')}{match.group('suffix')}"


_DRAFT_TEXT_FIELDS = (
    "title",
    "domain",
    "sim_or_real",
    "goal",
    "proposed_action",
    "decision",
    "correctness",
    "rationale",
    "executed_action",
    "outcome",
    "reward_note",
)


def _plant_draft(source_name: str, extracted: Mapping[str, Any]) -> dict[str, Any]:
    """A plant row from the fields an extractor found; absent fields default to empty.

    No extractor finds a source round, so it always comes from the record id.
    """
    ident = _text(extracted.get("record_id"))
    text = {field: _text(extracted.get(field)) for field in _DRAFT_TEXT_FIELDS}
    reward_total = extracted.get("reward_total")
    return {
        "record_id": ident,
        "source_round": _round_from_id(ident),
        "index": extracted.get("index"),
        "title": text["title"],
        "domain": text["domain"],
        "sim_or_real": text["sim_or_real"] or "designed",
        "goal": text["goal"],
        "proposed_action": text["proposed_action"],
        "decision": text["decision"],
        "correctness": text["correctness"] or "correct",
        "rationale": text["rationale"],
        "executed_action": text["executed_action"],
        "outcome": text["outcome"],
        "reward_total": 0.0 if reward_total is None else reward_total,
        "reward_note": text["reward_note"],
        "source_name": source_name,
    }


def _dict_field(mapping: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = mapping.get(key)
    return value if isinstance(value, dict) else {}


def _from_rec_dict(
    rec: Mapping[str, Any],
    source_name: str,
    index: int,
) -> dict[str, Any]:
    state = _dict_field(rec, "state")
    proposed = _dict_field(rec, "proposed_action")
    safety = _dict_field(rec, "safety_decision")
    executed = _dict_field(rec, "executed_action")
    outcome = _dict_field(rec, "future_outcome")
    note = _reward_note(rec.get("reward_components"))
    return _plant_draft(source_name, {
        "record_id": rec.get("id"),
        "index": index,
        "title": rec.get("title"),
        "domain": state.get("domain") or rec.get("domain"),
        "sim_or_real": state.get("sim_or_real"),
        "goal": state.get("goal") or rec.get("goal"),
        "proposed_action": proposed.get("name") or rec.get("proposed_action"),
        "decision": safety.get("decision"),
        "correctness": safety.get("correctness"),
        "rationale": safety.get("rationale"),
        "executed_action": executed.get("name") or rec.get("executed_action"),
        "outcome": outcome.get("summary") or rec.get("outcome"),
        "reward_total": _reward_total(note),
        "reward_note": note,
    })


def _str_constant(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _builder_strings(fn: ast.FunctionDef) -> dict[str, str]:
    """The first string literal per identity key across every dict literal in ``fn``."""
    found: dict[str, str] = {}
    for node in ast.walk(fn):
        if not isinstance(node, ast.Dict):
            continue
        for key_node, value_node in zip(node.keys, node.values):
            key = _str_constant(key_node)
            value = _str_constant(value_node)
            if key in _BUILDER_KEYS and key not in found and value is not None:
                found[key] = value
    return found


def _from_builder_fn(fn: ast.FunctionDef, source_name: str, index: int) -> dict[str, Any] | None:
    found = _builder_strings(fn)
    if "id" not in found:
        return None
    return _plant_draft(source_name, {
        "record_id": found.get("id"),
        "index": index,
        "domain": found.get("domain"),
        "sim_or_real": found.get("sim_or_real"),
        "goal": found.get("goal"),
        "decision": found.get("decision"),
    })


def _rec_from_assignment(
    name: str, value: ast.AST, consts: Mapping[str, Any], source_name: str
) -> dict[str, Any] | None:
    """A ``REC_<n> = {...}`` dict literal walked into a plant row, else None."""
    match = REC_NAME_RE.match(name)
    if not match or not isinstance(value, ast.Dict):
        return None
    return _from_rec_dict(_walk_mapping(value, consts), source_name, int(match.group(1)))


def _builder_from_function(node: ast.FunctionDef, source_name: str) -> dict[str, Any] | None:
    match = BUILDER_NAME_RE.match(node.name)
    if match is None:
        return None
    return _from_builder_fn(node, source_name, int(match.group(1)))


def _remember_const(consts: dict[str, Any], name: str, value: ast.AST) -> None:
    """Bind ``name`` when ``value`` is a known name or a literal, so later rows can use it."""
    resolved = _optional_const(value, consts)
    if resolved is not None:
        consts[name] = resolved


def _module_rows(
    tree: ast.Module, source_name: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """``REC_<n>`` dict rows and ``rec_<n>()`` builder rows, in source order."""
    consts: dict[str, Any] = {}
    recs: list[dict[str, Any]] = []
    builders: list[dict[str, Any]] = []
    for node in tree.body:
        item = _assigned(node)
        if item is not None:
            name, value = item
            _remember_const(consts, name, value)
            row = _rec_from_assignment(name, value, consts, source_name)
            found = recs
        elif isinstance(node, ast.FunctionDef):
            row = _builder_from_function(node, source_name)
            found = builders
        else:
            continue
        if row is not None:
            found.append(row)
    return recs, builders


def plants_from_source(text: str, source_name: str = "snippet") -> tuple[Plant, ...]:
    """AST-extract one TTF identity catalog. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_AST_NOT_A_PLANT, f"mill source is not parseable: {exc}")
    recs, builders = _module_rows(tree, source_name)
    rows = recs or builders
    refuse_when(
        len(rows) != QUOTA_PER_ROUND,
        FINDING_CATALOG_SLICE_STRIDE,
        f"{source_name} did not yield a {QUOTA_PER_ROUND}-record catalog",
    )
    rows.sort(key=lambda row: (row.get("source_round") or 0, row.get("index") or 0))
    for offset, row in enumerate(rows, start=1):
        row["index"] = offset
    return tuple(
        plant_from_mapping(row, f"{source_name}[{index}]")
        for index, row in enumerate(rows)
    )


def _require_identity(values: Mapping[str, Any], where: str) -> None:
    record_id = values["record_id"]
    refuse_when(
        not isinstance(record_id, str) or RECORD_ID_RE.match(record_id) is None,
        FINDING_FIELD_INVALID,
        f"{where}.record_id must be a ttf-r id, got {shown(record_id)}",
    )
    source_round = values["source_round"]
    refuse_when(
        type(source_round) is not int or source_round < 1,
        FINDING_FIELD_INVALID,
        f"{where}.source_round must be a positive int, got {shown(source_round)}",
    )
    index = values["index"]
    refuse_when(
        type(index) is not int or not 1 <= index <= QUOTA_PER_ROUND,
        FINDING_FIELD_INVALID,
        f"{where}.index must be 1..{QUOTA_PER_ROUND}, got {shown(index)}",
    )


def _require_vocabulary(values: Mapping[str, Any], where: str) -> None:
    sim = values["sim_or_real"]
    refuse_when(
        sim not in SIM_OR_REAL,
        FINDING_FIELD_INVALID,
        f"{where}.sim_or_real must be designed/hil/simulated, got {shown(sim)}",
    )
    decision = values["decision"]
    refuse_when(
        decision not in DECISIONS,
        FINDING_FIELD_INVALID,
        f"{where}.decision must be ACCEPT/MODIFY/REJECT, got {shown(decision)}",
    )
    correctness = values["correctness"]
    refuse_when(
        correctness not in CORRECTNESS,
        FINDING_FIELD_INVALID,
        f"{where}.correctness must be correct/incorrect, got {shown(correctness)}",
    )
    total = values["reward_total"]
    refuse_when(
        type(total) is not float and type(total) is not int,
        FINDING_FIELD_INVALID,
        f"{where}.reward_total must be a number, got {shown(total)}",
    )


def _checked_fields(values: Mapping[str, Any], where: str) -> dict[str, Any]:
    """Every field in ``PLANT_FIELDS`` order: ints kept, the total as float, the rest strings."""
    checked: dict[str, Any] = {}
    for field in PLANT_FIELDS:
        value = values[field]
        if field in {"source_round", "index"}:
            checked[field] = value
        elif field == "reward_total":
            checked[field] = float(value)
        else:
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
    _require_vocabulary(values, where)
    checked = _checked_fields(values, where)
    refuse_when(
        not checked["domain"] or not checked["decision"],
        FINDING_FIELD_MISSING,
        f"{where} needs domain and decision",
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
    """Fail closed unless every recover-grok catalog is a five-plant slice."""

    loaded = load_catalog() if plants is None else Catalog(CATALOG_ID, plants)
    items = loaded.plants
    refuse_when(not items, FINDING_CATALOG_EMPTY, "catalog has no plants")
    refuse_when(
        len(items) != FULL_PLANT_COUNT,
        FINDING_CATALOG_SLICE_STRIDE,
        f"catalog length {len(items)} is not {FULL_PLANT_COUNT}",
    )
    _check_unique(items)
    by_slice: dict[str, tuple[Plant, ...]] = {}
    for plant in items:
        slice_id = slice_from_record_id(plant.record_id)
        by_slice.setdefault(slice_id, ())
        by_slice[slice_id] = by_slice[slice_id] + (plant,)
    refuse_when(
        tuple(by_slice) != SLICE_IDS,
        FINDING_CATALOG_SLICE_STRIDE,
        f"catalog slices {tuple(by_slice)} are not {SLICE_IDS}",
    )
    for slice_id, chunk in by_slice.items():
        refuse_when(
            len(chunk) != QUOTA_PER_ROUND,
            FINDING_CATALOG_SLICE_STRIDE,
            f"slice {slice_id} has {len(chunk)} plants, want {QUOTA_PER_ROUND}",
        )
        expected_source = SOURCE_FILE_BY_SLICE[slice_id]
        refuse_when(
            {plant.source_name for plant in chunk} != {expected_source},
            FINDING_FIELD_INVALID,
            f"slice {slice_id} source_name must be {expected_source}",
        )
    rounds = tuple(sorted({plant.source_round for plant in items}))
    return {
        "status": "ok",
        "catalog_id": CATALOG_ID,
        "coverage": "full",
        "source_catalogs": len(SOURCE_CATALOGS),
        "slices": list(SLICE_IDS),
        "plants": len(items),
        "rounds": list(rounds),
        "first_round": rounds[0],
        "last_round": rounds[-1],
        "factory": FACTORY,
        "generator": GENERATOR,
    }


def plants_for_slice(slice_id: str, plants: tuple[Plant, ...] | None = None) -> tuple[Plant, ...]:
    items = load_catalog().plants if plants is None else plants
    refuse_when(
        slice_id not in SLICE_IDS,
        FINDING_SLICE_OUT_OF_DOMAIN,
        f"slice must be one of {list(SLICE_IDS)}, got {shown(slice_id)}",
    )
    chunk = tuple(
        plant for plant in items if slice_from_record_id(plant.record_id) == slice_id
    )
    refuse_when(
        len(chunk) != QUOTA_PER_ROUND,
        FINDING_SLICE_OUT_OF_DOMAIN,
        f"no plant slice for {slice_id}",
    )
    return chunk


def plants_for_round(round_n: int, plants: tuple[Plant, ...] | None = None) -> tuple[Plant, ...]:
    """Return the five plants for ``round_n`` when that round names one slice only."""

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
    slices = {slice_from_record_id(plant.record_id) for plant in chunk}
    refuse_when(
        len(slices) != 1,
        FINDING_SLICE_OUT_OF_DOMAIN,
        f"round {round_n} spans slices {sorted(slices)}; use plants_for_slice",
    )
    refuse_when(
        len(chunk) != QUOTA_PER_ROUND,
        FINDING_SLICE_OUT_OF_DOMAIN,
        f"no plant slice for r{round_n}",
    )
    return chunk


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load ``CATALOG.json`` and ``plants.jsonl``. Never exec a mill script."""

    catalog_dir = default_catalog_dir() if directory is None else Path(directory)
    catalog_path = catalog_dir / CATALOG_FILENAME
    plants_path = catalog_dir / PLANTS_FILENAME
    refuse_first(
        (
            (not catalog_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {catalog_path}"),
            (not plants_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {plants_path}"),
        )
    )
    meta = load_strict_json(catalog_path.read_text(encoding="utf-8"))
    refuse_when(not isinstance(meta, dict), FINDING_FIELD_INVALID, "CATALOG.json must be an object")
    refuse_when(
        meta.get("catalog_id") != CATALOG_ID
        or meta.get("family") != FAMILY_PREFIX
        or meta.get("schema") != CATALOG_SCHEMA
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
        plant_from_mapping(load_strict_json(line), f"line {lineno}")
        for lineno, line in enumerate(plants_bytes.decode("utf-8").splitlines(), start=1)
        if line
    ]
    refuse_when(not rows, FINDING_CATALOG_EMPTY, "plants.jsonl has no rows")
    refuse_when(
        len(rows) != meta["plants"],
        FINDING_FIELD_INVALID,
        f"plants.jsonl has {len(rows)} rows; CATALOG.json says {meta['plants']}",
    )
    return Catalog(CATALOG_ID, tuple(rows))


bind_import_twin(__name__)
