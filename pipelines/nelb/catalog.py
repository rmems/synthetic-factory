#!/usr/bin/env python3
"""NELB plant catalog: AST extract of the recovered r01 builder.

``plants_from_source`` walks a recovered mill as text (``ast.parse`` only,
``exec: false``). The committed catalog is the first three-pair slice from
``origin/codex/recover-grok-01a06111``. Recovered ``*mill*.py`` / ``gen_r*.py``
scripts are not vendored.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ._contract import (
    CATALOG_ID,
    FACTORY,
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_TRIPLE_STRIDE,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_TRIPLE_OUT_OF_DOMAIN,
    GENERATOR,
    QUOTA_PER_ROUND,
    NelbRefusal,
    bind_import_twin,
    refuse,
    refuse_first,
    refuse_when,
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
    "load_catalog",
    "plant_from_mapping",
    "plants_for_round",
    "plants_from_source",
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


def _dict_literal(node: ast.AST, consts: Mapping[str, Any]) -> dict[str, Any] | None:
    if not isinstance(node, ast.Dict) or any(key is None for key in node.keys):
        return None
    row: dict[str, Any] = {}
    for key_node, value_node in zip(node.keys, node.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            continue
        resolved = _optional_const(value_node, consts)
        if resolved is not None:
            row[key_node.value] = resolved
        elif isinstance(value_node, ast.Dict):
            nested = _dict_literal(value_node, consts)
            if nested is not None:
                row[key_node.value] = nested
    return row


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


def _plant_draft(
    round_n: int,
    index: int,
    source_name: str,
    *,
    record_id: Any = None,
    site: Any = "",
    domain: Any = "",
    sim_or_real: Any = "",
    reconstruction: Any = "",
    formula: Any = "",
    lead_decision: Any = "",
    companion_decision: Any = "",
    companion_key: Any = "",
    goal: Any = "",
) -> dict[str, Any]:
    return {
        "record_id": record_id or f"nelb-r{round_n:02d}-{index:03d}",
        "source_round": round_n,
        "index": index,
        "site": _text(site),
        "domain": _text(domain),
        "sim_or_real": _text(sim_or_real) or "designed",
        "reconstruction": _text(reconstruction),
        "formula": _text(formula),
        "lead_decision": _text(lead_decision),
        "companion_decision": _text(companion_decision),
        "companion_key": _text(companion_key) or "trajectory_companion",
        "goal": _text(goal),
        "source_name": source_name,
    }


def _decision_of(traj: Mapping[str, Any]) -> str:
    safety = traj.get("safety_decision") if isinstance(traj.get("safety_decision"), dict) else {}
    return _text(safety.get("decision"))


def _companion_key(returned: ast.Dict, view: Mapping[str, Any]) -> str:
    """Name the companion trajectory key without executing the mill."""

    for key_node, value_node in zip(returned.keys, returned.values):
        if not isinstance(key_node, ast.Constant) or key_node.value != "language_view":
            continue
        if not isinstance(value_node, ast.Dict):
            continue
        for nested_key, nested_value in zip(value_node.keys, value_node.values):
            if not isinstance(nested_key, ast.Constant) or not isinstance(nested_key.value, str):
                continue
            key = nested_key.value
            if key in {"description", "trajectory"}:
                continue
            if key.startswith("trajectory_") or (
                isinstance(nested_value, ast.Name) and nested_value.id == "traj2"
            ):
                return key
    for key, value in view.items():
        if key != "trajectory" and isinstance(value, dict) and "safety_decision" in value:
            return key
    return ""


def _from_rec_func(
    fn: ast.FunctionDef,
    consts: Mapping[str, Any],
    round_n: int,
    source_name: str,
) -> dict[str, Any] | None:
    assigns = dict(
        item for node in fn.body if (item := _assigned(node)) is not None
    )
    returned = None
    for node in reversed(fn.body):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            returned = node.value
            break
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Name):
            bound = assigns.get(node.value.id)
            if isinstance(bound, ast.Dict):
                returned = bound
                break
    if returned is None:
        return None
    rec = _dict_literal(returned, consts) or {}
    traj = _dict_literal(assigns.get("traj"), consts) or {}
    traj2 = _dict_literal(assigns.get("traj2"), consts) or {}
    view = rec.get("language_view") if isinstance(rec.get("language_view"), dict) else {}
    if not traj and isinstance(view.get("trajectory"), dict):
        traj = view["trajectory"]
    companion_key = _companion_key(returned, view)
    if not traj2:
        for key, value in view.items():
            if key != "trajectory" and isinstance(value, dict) and "safety_decision" in value:
                traj2 = value
                companion_key = companion_key or key
                break
    state = traj.get("state") if isinstance(traj.get("state"), dict) else {}
    recon = rec.get("reconstruction_model") if isinstance(rec.get("reconstruction_model"), dict) else {}
    notes = rec.get("bridge_notes") if isinstance(rec.get("bridge_notes"), dict) else {}
    index = _index_from_name(fn.name) or 1
    record_id = rec.get("id")
    inferred = _round_from_id(record_id) if isinstance(record_id, str) else None
    return _plant_draft(
        inferred or round_n,
        index,
        source_name,
        record_id=record_id,
        site=_site_from_setting(_text(state.get("setting"))),
        domain=state.get("domain"),
        sim_or_real=state.get("sim_or_real"),
        reconstruction=recon.get("name"),
        formula=recon.get("formula"),
        lead_decision=_decision_of(traj),
        companion_decision=_decision_of(traj2),
        companion_key=companion_key,
        goal=notes.get("why_high_value") or view.get("description"),
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
        if row is None:
            continue
        state = row.get("state") if isinstance(row.get("state"), dict) else {}
        plants.append(
            _plant_draft(
                round_n,
                row["index"] if type(row.get("index")) is int else offset,
                source_name,
                record_id=row.get("id") or row.get("record_id"),
                site=row.get("site") or _site_from_setting(_text(state.get("setting"))),
                domain=row.get("domain") or state.get("domain"),
                sim_or_real=row.get("sim_or_real") or state.get("sim_or_real"),
                reconstruction=row.get("reconstruction"),
                formula=row.get("formula"),
                lead_decision=row.get("lead_decision"),
                companion_decision=row.get("companion_decision"),
                companion_key=row.get("companion_key"),
                goal=row.get("goal"),
            )
        )
    return plants


def plants_from_source(text: str, source_name: str = "snippet") -> tuple[Plant, ...]:
    """AST-extract one 3-pair NELB identity catalog. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_AST_NOT_A_PLANT, f"mill source is not parseable: {exc}")
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
            continue
        if isinstance(node, ast.FunctionDef) and node.name.startswith("rec_"):
            rec_funcs.append(node)
    factory = consts.get("FACTORY")
    refuse_when(
        factory not in (None, FACTORY),
        FINDING_AST_NOT_A_PLANT,
        f"{source_name} FACTORY is {shown(factory)}",
    )
    round_n = consts.get("ROUND")
    if type(round_n) is not int:
        round_n = 1
    plants: list[dict[str, Any]] = []
    if rec_funcs:
        for fn in rec_funcs:
            row = _from_rec_func(fn, consts, round_n, source_name)
            if row is not None:
                plants.append(row)
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


def _require_plant_fields(values: Mapping[str, Any], where: str) -> dict[str, Any]:
    missing = [field for field in PLANT_FIELDS if field not in values]
    refuse_when(bool(missing), FINDING_FIELD_MISSING, f"{where} missing {missing}")
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


_EXTRACTED_ROWS: tuple[tuple[Any, ...], ...] = (
    (
        "nelb-r01-001",
        1,
        1,
        "Brackfen Pool BF-3",
        "johnson_noise_spent_fuel_pool_t",
        "designed",
        "johnson_noise_pool_temperature",
        "T_K = k_j * V_rms_uV^2; k_j = T_K / V_rms_uV^2",
        "REJECT",
        "MODIFY",
        "trajectory_recirc_hold",
        "Gate continue-recirc at BF-3 when Johnson-noise T_K = k_j*V^2 is 320 K "
        "over the 315 K isolate floor; Noiseveil 298 K is not SoT.",
        "gen_r01.py",
    ),
    (
        "nelb-r01-002",
        1,
        2,
        "Flintshaw CMP FS-6",
        "coulter_cmp_slurry_particles",
        "hil",
        "coulter_cmp_particle_concentration",
        "C_ppm = k_c * (Vp_mV / Vref_mV); R = Vp_mV / Vref_mV",
        "MODIFY",
        "ACCEPT",
        "trajectory_new_aperture",
        "Gate keep-polish at FS-6 when Coulter C_ppm = k_c*(Vp/Vref) is 120 ppm "
        "over the 80 ppm isolate floor; Slurryveil 18.20 ppm is not SoT.",
        "gen_r01.py",
    ),
    (
        "nelb-r01-003",
        1,
        3,
        "Yewholt COPV YH-9",
        "photoelastic_copv_hoop_stress",
        "simulated",
        "photoelastic_copv_hoop_stress",
        "sigma_MPa = k_p * N; N = sigma_MPa / k_p",
        "ACCEPT",
        "REJECT",
        "trajectory_skip_vessel_refusal",
        "Gate V-4 isolate at YH-9 when photoelastic sigma = k_p*N is 32 MPa "
        "over the 24 MPa isolate floor; Fringeveil 6.40 MPa cannot skip V-1..V-3.",
        "gen_r01.py",
    ),
)


def _plants_from_extracted() -> tuple[Plant, ...]:
    plants = tuple(
        plant_from_mapping(dict(zip(PLANT_FIELDS, row, strict=True)), f"extracted[{index}]")
        for index, row in enumerate(_EXTRACTED_ROWS)
    )
    _check_unique(plants)
    return plants


_CATALOG = Catalog(CATALOG_ID, _plants_from_extracted())
WAVE_ROUNDS = tuple(sorted({plant.source_round for plant in _CATALOG.plants}))


def load_catalog() -> Catalog:
    return _CATALOG


bind_import_twin(__name__)
