#!/usr/bin/env python3
"""FFPC plant catalog: AST extract of recovered Session-A builders.

``plants_from_source`` walks a recovered mill as text (``ast.parse`` only,
``exec: false``). The committed catalog is a compact JSONL slice under
``pipelines/ffpc/`` pinned by ``CATALOG.json``. Recovered ``*mill*.py`` scripts
are not vendored.
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
    CATALOG_ID,
    FACTORY,
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_TRIPLE_STRIDE,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_TRIPLE_OUT_OF_DOMAIN,
    GENERATOR,
    QUOTA_PER_ROUND,
    SOURCE_COMMIT,
    SOURCE_REF,
    SOURCE_TREE,
    FfpcRefusal,
    bind_import_twin,
    load_strict_json,
    refuse,
    refuse_first,
    refuse_when,
    shown,
)

CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
DEFAULT_CATALOG_DIR = Path(__file__).resolve().parent
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
    "quota_per_round",
    "source_ref",
    "source_commit",
)

ID_PREFIX = "ffpc"
PLANT_FIELDS = (
    "record_id",
    "source_round",
    "index",
    "site",
    "domain",
    "sim_or_real",
    "failure_mode",
    "root_cause",
    "goal",
    "source_name",
)
SIM_OR_REAL = frozenset({"designed", "hil", "simulated"})

__all__ = [
    "CATALOG_FILENAME",
    "CATALOG_ID",
    "DEFAULT_CATALOG_DIR",
    "FACTORY",
    "GENERATOR",
    "ID_PREFIX",
    "PLANT_FIELDS",
    "PLANTS_FILENAME",
    "QUOTA_PER_ROUND",
    "WAVE_ROUNDS",
    "Catalog",
    "Plant",
    "catalog_check",
    "load_catalog",
    "plant_from_mapping",
    "plants_for_round",
    "plants_from_source",
]


@dataclass(frozen=True)
class Plant:
    """One AST-extracted FFPC pair identity. Full recovered payloads stay out."""

    record_id: str
    source_round: int
    index: int
    site: str
    domain: str
    sim_or_real: str
    failure_mode: str
    root_cause: str
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


def _site_from_env(env: Any) -> str:
    if not isinstance(env, dict):
        return ""
    for key in ("site", "plant", "unit", "asset", "hall", "facility"):
        value = env.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


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
    except FfpcRefusal:
        return None


def _resolve_expr(node: ast.AST, consts: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return consts.get(node.id)
    if isinstance(node, ast.Dict):
        out: dict[str, Any] = {}
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None or value_node is None:
                continue
            key = _resolve_expr(key_node, consts)
            if not isinstance(key, str):
                continue
            out[key] = _resolve_expr(value_node, consts)
        return out
    if isinstance(node, ast.List):
        return [_resolve_expr(elt, consts) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_resolve_expr(elt, consts) for elt in node.elts)
    try:
        return _literal(node)
    except FfpcRefusal:
        return None


def _collect_consts(tree: ast.Module) -> tuple[dict[str, Any], dict[str, ast.AST]]:
    raw: dict[str, ast.AST] = {}
    for node in tree.body:
        item = _assigned(node)
        if item is None:
            continue
        name, value = item
        raw[name] = value
    consts: dict[str, Any] = {}
    for _ in range(len(raw) + 1):
        changed = False
        for name, value in raw.items():
            if name in consts:
                continue
            resolved = _resolve_expr(value, consts)
            if resolved is not None:
                consts[name] = resolved
                changed = True
        if not changed:
            break
    return consts, raw


def _infer_round(consts: Mapping[str, Any], source_name: str) -> int:
    match = re.search(r"ffpc[-_]r(\d+)", source_name, re.IGNORECASE)
    if match is not None:
        return int(match.group(1))
    rnd = consts.get("ROUND")
    refuse_when(
        type(rnd) is not int,
        FINDING_AST_NOT_A_PLANT,
        f"{source_name} has no ffpc-r slug and ROUND is {shown(rnd)}",
    )
    return rnd


def _plant_from_arm(
    arm: Mapping[str, Any],
    round_n: int,
    index: int,
    source_name: str,
) -> dict[str, Any]:
    state = arm.get("state") if isinstance(arm.get("state"), dict) else {}
    env = state.get("environment") if isinstance(state.get("environment"), dict) else {}
    diagnosis = arm.get("diagnosis") if isinstance(arm.get("diagnosis"), dict) else {}
    meta = arm.get("meta") if isinstance(arm.get("meta"), dict) else {}
    proposed = arm.get("proposed_action") if isinstance(arm.get("proposed_action"), dict) else {}
    return _plant_draft(
        round_n,
        index,
        source_name,
        record_id=arm.get("id"),
        site=_site_from_env(env),
        domain=state.get("domain") or meta.get("domain"),
        sim_or_real=state.get("sim_or_real"),
        failure_mode=arm.get("failure_archetype")
        or meta.get("failure_archetype")
        or arm.get("gate_flaw_class"),
        root_cause=diagnosis.get("root_cause") or diagnosis.get("root"),
        goal=arm.get("goal") or proposed.get("summary") or proposed.get("type"),
    )


def _plant_draft(
    round_n: int,
    index: int,
    source_name: str,
    *,
    record_id: Any = None,
    site: Any = "",
    domain: Any = "",
    sim_or_real: Any = "",
    failure_mode: Any = "",
    root_cause: Any = "",
    goal: Any = "",
) -> dict[str, Any]:
    return {
        "record_id": record_id or f"ffpc-r{round_n:02d}-{index:03d}",
        "source_round": round_n,
        "index": index,
        "site": _text(site),
        "domain": _text(domain),
        "sim_or_real": _text(sim_or_real) or "designed",
        "failure_mode": _text(failure_mode),
        "root_cause": _text(root_cause),
        "goal": _text(goal),
        "source_name": source_name,
    }


def _from_pairs_dicts(
    pairs: ast.List,
    consts: dict[str, Any],
    round_n: int,
    source_name: str,
) -> list[dict[str, Any]]:
    plants: list[dict[str, Any]] = []
    for offset, elt in enumerate(pairs.elts, start=1):
        if not isinstance(elt, ast.Dict) or any(key is None for key in elt.keys):
            continue
        row: dict[str, Any] = {}
        for key_node, value_node in zip(elt.keys, elt.values):
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                continue
            resolved = _optional_const(value_node, consts)
            if resolved is not None:
                row[key_node.value] = resolved
        state = row.get("state") if isinstance(row.get("state"), dict) else {}
        shared = row.get("shared") if isinstance(row.get("shared"), dict) else {}
        ctx = row.get("ctx") if isinstance(row.get("ctx"), dict) else {}
        diagnosis = row.get("diagnosis") if isinstance(row.get("diagnosis"), dict) else {}
        env_host = state or shared or ctx
        env = env_host.get("environment") if isinstance(env_host.get("environment"), dict) else {}
        index = row.get("index") if type(row.get("index")) is int else offset
        plants.append(
            _plant_draft(
                round_n,
                index,
                source_name,
                record_id=row.get("id"),
                site=row.get("site") or _site_from_env(env),
                domain=env_host.get("domain") or row.get("domain"),
                sim_or_real=env_host.get("sim_or_real"),
                failure_mode=row.get("failure_archetype")
                or row.get("failure_mode")
                or row.get("gate_flaw_class"),
                root_cause=diagnosis.get("root_cause") or diagnosis.get("root") or row.get("root"),
                goal=row.get("goal"),
            )
        )
    return plants


def _from_pair_record_calls(
    pairs: ast.List,
    consts: dict[str, Any],
    round_n: int,
    source_name: str,
) -> list[dict[str, Any]]:
    plants: list[dict[str, Any]] = []
    for offset, elt in enumerate(pairs.elts, start=1):
        if not isinstance(elt, ast.Call):
            continue
        if not isinstance(elt.func, ast.Name) or elt.func.id != "pair_record":
            continue
        if len(elt.args) < 3:
            continue
        record_id = _optional_const(elt.args[0], consts)
        goal = _optional_const(elt.args[1], consts)
        failure_mode = _optional_const(elt.args[2], consts)
        state = consts.get(f"STATE_0{offset}")
        state = state if isinstance(state, dict) else {}
        env = state.get("environment") if isinstance(state.get("environment"), dict) else {}
        plants.append(
            _plant_draft(
                round_n,
                offset,
                source_name,
                record_id=record_id,
                site=_site_from_env(env),
                domain=state.get("domain"),
                sim_or_real=state.get("sim_or_real"),
                failure_mode=failure_mode,
                goal=goal,
            )
        )
    return plants


def _from_state_slots(
    consts: dict[str, Any],
    round_n: int,
    source_name: str,
) -> list[dict[str, Any]]:
    plants: list[dict[str, Any]] = []
    for index in (1, 2, 3):
        state = consts.get(f"STATE_0{index}") or consts.get(f"PAIR_0{index}_STATE")
        if not isinstance(state, dict):
            continue
        diag = consts.get(f"DIAG_0{index}") or consts.get(f"PAIR_0{index}_DIAGNOSIS") or {}
        env = state.get("environment") if isinstance(state.get("environment"), dict) else {}
        plants.append(
            _plant_draft(
                round_n,
                index,
                source_name,
                site=_site_from_env(env),
                domain=state.get("domain"),
                sim_or_real=state.get("sim_or_real"),
                failure_mode=consts.get(f"FAIL_0{index}") or consts.get(f"P{index}_FM") or "",
                root_cause=diag.get("root_cause") or diag.get("root") if isinstance(diag, dict) else "",
                goal=consts.get(f"GOAL_0{index}") or consts.get(f"P{index}_GOAL") or "",
            )
        )
    return plants


def _from_pairs_int_dict(
    pairs: ast.Dict,
    consts: Mapping[str, Any],
    round_n: int,
    source_name: str,
) -> list[dict[str, Any]]:
    plants: list[dict[str, Any]] = []
    for key_node, value_node in zip(pairs.keys, pairs.values):
        index = _resolve_expr(key_node, consts)
        row = _resolve_expr(value_node, consts)
        if type(index) is not int or not isinstance(row, dict):
            continue
        plants.append(
            _plant_draft(
                round_n,
                index,
                source_name,
                record_id=row.get("id"),
                goal=row.get("goal"),
                failure_mode=row.get("failure_archetype") or row.get("gate_flaw_class"),
            )
        )
    return plants


def _from_arm_or_rej(
    consts: Mapping[str, Any],
    round_n: int,
    source_name: str,
) -> list[dict[str, Any]]:
    plants: list[dict[str, Any]] = []
    for index in (1, 2, 3):
        arm: Mapping[str, Any] | None = None
        for key in (
            f"ARM{index}",
            f"ARM_{index:03d}",
            f"REJ_{index:02d}",
            f"REJECTED_{index:02d}",
        ):
            value = consts.get(key)
            if isinstance(value, dict) and value.get("id"):
                arm = value
                break
        if arm is None:
            continue
        plants.append(_plant_from_arm(arm, round_n, index, source_name))
    return plants


def _kwargs_from_dict_call(call: ast.Call, consts: Mapping[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for kw in call.keywords:
        if kw.arg is None:
            continue
        resolved = _optional_const(kw.value, consts)
        if resolved is None and isinstance(kw.value, ast.Name):
            resolved = consts.get(kw.value.id)
        if resolved is not None:
            row[kw.arg] = resolved
    return row


def _failure_archetype_from_meta_call(node: ast.AST) -> str:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return ""
    if node.func.id == "meta_block" and len(node.args) >= 2:
        value = _optional_const(node.args[1], {})
        return _text(value)
    if node.func.id == "meta_for" and len(node.args) >= 3:
        value = _optional_const(node.args[2], {})
        return _text(value)
    return ""


def _failure_archetype_from_record_ast(record: ast.AST) -> str:
    if not isinstance(record, ast.Dict):
        return ""
    for key_node, value_node in zip(record.keys, record.values):
        if not isinstance(key_node, ast.Constant) or key_node.value != "meta":
            continue
        return _failure_archetype_from_meta_call(value_node)
    return ""


def _from_pairs_dict_calls(
    pairs: ast.List,
    consts: Mapping[str, Any],
    round_n: int,
    source_name: str,
) -> list[dict[str, Any]]:
    plants: list[dict[str, Any]] = []
    for offset, elt in enumerate(pairs.elts, start=1):
        if not isinstance(elt, ast.Call) or not isinstance(elt.func, ast.Name) or elt.func.id != "dict":
            continue
        row = _kwargs_from_dict_call(elt, consts)
        state = row.get("state") if isinstance(row.get("state"), dict) else {}
        env = state.get("environment") if isinstance(state.get("environment"), dict) else {}
        index = row.get("index") if type(row.get("index")) is int else offset
        root = row.get("root")
        root_cause = root if isinstance(root, str) else _text(root)
        plants.append(
            _plant_draft(
                round_n,
                index,
                source_name,
                record_id=row.get("pair_id") or row.get("id"),
                site=_site_from_env(env),
                domain=state.get("domain"),
                sim_or_real=state.get("sim_or_real"),
                failure_mode=row.get("failure_mode") or row.get("archetype") or row.get("flaw"),
                root_cause=root_cause,
                goal=row.get("goal"),
            )
        )
    return plants


def _from_rec_records(
    consts: Mapping[str, Any],
    raw: Mapping[str, ast.AST],
    round_n: int,
    source_name: str,
) -> list[dict[str, Any]]:
    rec_keys = sorted(
        (name for name in consts if re.fullmatch(r"REC_\d+", name)),
        key=lambda name: int(name.split("_", 1)[1]),
    )
    plants: list[dict[str, Any]] = []
    for offset, name in enumerate(rec_keys, start=1):
        record = consts.get(name)
        if not isinstance(record, dict) or not record.get("id"):
            continue
        meta = record.get("meta") if isinstance(record.get("meta"), dict) else {}
        failure_mode = meta.get("failure_archetype") or meta.get("gate_flaw_class")
        if not failure_mode:
            failure_mode = _failure_archetype_from_record_ast(raw.get(name, ast.Constant(None)))
        arm = dict(record)
        if failure_mode and not isinstance(arm.get("meta"), dict):
            arm["meta"] = {"failure_archetype": failure_mode}
        elif failure_mode and isinstance(arm.get("meta"), dict):
            arm = dict(record)
            arm["meta"] = {**meta, "failure_archetype": failure_mode}
        diag_key = f"DIAG_{name.split('_', 1)[1]}"
        diag = consts.get(diag_key)
        if isinstance(diag, dict) and not arm.get("diagnosis"):
            arm = dict(arm)
            arm["diagnosis"] = diag
        plants.append(_plant_from_arm(arm, round_n, offset, source_name))
    return plants


def _from_rejected_pair_list(
    pairs: ast.List,
    consts: Mapping[str, Any],
    round_n: int,
    source_name: str,
) -> list[dict[str, Any]]:
    plants: list[dict[str, Any]] = []
    for offset, elt in enumerate(pairs.elts, start=1):
        row = _resolve_expr(elt, consts)
        if not isinstance(row, dict):
            continue
        arm = row.get("rejected")
        if not isinstance(arm, dict):
            continue
        plants.append(_plant_from_arm(arm, round_n, offset, source_name))
    return plants


def plants_from_source(text: str, source_name: str = "snippet") -> tuple[Plant, ...]:
    """AST-extract one 3-pair FFPC identity catalog. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_AST_NOT_A_PLANT, f"mill source is not parseable: {exc}")
    consts, raw = _collect_consts(tree)
    factory = consts.get("FACTORY")
    refuse_when(
        factory not in (None, FACTORY),
        FINDING_AST_NOT_A_PLANT,
        f"{source_name} FACTORY is {shown(factory)}",
    )
    round_n = _infer_round(consts, source_name)
    pairs = raw.get("PAIRS")
    plants: list[dict[str, Any]] = []
    if isinstance(pairs, ast.List) and pairs.elts and isinstance(pairs.elts[0], ast.Dict):
        first_row = _resolve_expr(pairs.elts[0], consts)
        if isinstance(first_row, dict) and "rejected" in first_row:
            plants = _from_rejected_pair_list(pairs, consts, round_n, source_name)
        else:
            plants = _from_pairs_dicts(pairs, consts, round_n, source_name)
    elif (
        isinstance(pairs, ast.List)
        and pairs.elts
        and isinstance(pairs.elts[0], ast.Call)
        and isinstance(pairs.elts[0].func, ast.Name)
        and pairs.elts[0].func.id == "dict"
    ):
        plants = _from_pairs_dict_calls(pairs, consts, round_n, source_name)
    elif isinstance(pairs, ast.List) and pairs.elts and isinstance(pairs.elts[0], ast.Call):
        plants = _from_pair_record_calls(pairs, consts, round_n, source_name)
    elif isinstance(pairs, ast.List) and pairs.elts:
        plants = _from_rejected_pair_list(pairs, consts, round_n, source_name)
    elif isinstance(pairs, ast.Dict):
        plants = _from_pairs_int_dict(pairs, consts, round_n, source_name)
    if len(plants) != 3:
        plants = _from_arm_or_rej(consts, round_n, source_name)
    if len(plants) != 3:
        plants = _from_state_slots(consts, round_n, source_name)
    if len(plants) != 3:
        plants = _from_rec_records(consts, raw, round_n, source_name)
    refuse_when(
        len(plants) != 3,
        FINDING_CATALOG_TRIPLE_STRIDE,
        f"{source_name} did not yield a 3-pair catalog",
    )
    for row in plants:
        record_id = row.get("record_id")
        if isinstance(record_id, str):
            id_round = re.search(r"ffpc-r(\d+)", record_id)
            if id_round is not None and int(id_round.group(1)) != round_n:
                refuse(
                    FINDING_AST_NOT_A_PLANT,
                    f"{source_name} id {shown(record_id)} disagrees with round r{round_n}",
                )
    return tuple(plant_from_mapping(row, f"{source_name}[{index}]") for index, row in enumerate(plants))


def _require_plant_fields(values: Mapping[str, Any], where: str) -> dict[str, Any]:
    missing = [field for field in PLANT_FIELDS if field not in values]
    refuse_when(bool(missing), FINDING_FIELD_MISSING, f"{where} missing {missing}")
    record_id = values["record_id"]
    refuse_when(
        not isinstance(record_id, str) or not record_id.startswith("ffpc-r"),
        FINDING_FIELD_INVALID,
        f"{where}.record_id must be an ffpc-r id, got {shown(record_id)}",
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
    sim = values["sim_or_real"]
    refuse_when(
        sim not in SIM_OR_REAL,
        FINDING_FIELD_INVALID,
        f"{where}.sim_or_real must be designed/hil/simulated, got {shown(sim)}",
    )
    checked = {}
    for field in PLANT_FIELDS:
        value = values[field]
        if field in {"source_round", "index"}:
            checked[field] = value
            continue
        refuse_when(
            not isinstance(value, str),
            FINDING_FIELD_INVALID,
            f"{where}.{field} must be a string, got {shown(value)}",
        )
        checked[field] = value
    refuse_when(
        not checked["domain"] and not checked["failure_mode"] and not checked["goal"],
        FINDING_FIELD_MISSING,
        f"{where} needs domain, failure_mode, or goal",
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


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _plant_from_row(row: Mapping[str, Any], where: str) -> Plant:
    return plant_from_mapping(row, where)


_CATALOG: Catalog | None = None
WAVE_ROUNDS: tuple[int, ...] = ()


def load_catalog(directory: Path | None = None) -> Catalog:
    global _CATALOG, WAVE_ROUNDS
    if directory is None and _CATALOG is not None:
        return _CATALOG
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
        or meta.get("family") != "ffpc"
        or meta.get("schema") != "ffpc-plants-v1"
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
        _plant_from_row(load_strict_json(line), f"line {lineno}")
        for lineno, line in enumerate(plants_bytes.decode("utf-8").splitlines(), start=1)
        if line
    ]
    refuse_when(not rows, FINDING_CATALOG_EMPTY, "plants.jsonl has no rows")
    refuse_when(
        len(rows) != meta["plants"],
        FINDING_FIELD_INVALID,
        f"plants.jsonl has {len(rows)} rows; CATALOG.json says {meta['plants']}",
    )
    _check_unique(tuple(rows))
    catalog = Catalog(CATALOG_ID, tuple(rows))
    if directory is None:
        _CATALOG = catalog
        WAVE_ROUNDS = tuple(sorted({plant.source_round for plant in catalog.plants}))
    return catalog


bind_import_twin(__name__)
