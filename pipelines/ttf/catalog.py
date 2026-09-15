#!/usr/bin/env python3
"""TTF plant catalog: AST extract of the first recovered ``ttf*`` slice.

``plants_from_source`` walks a recovered generator as text (``ast.parse``
only, ``exec: false``). The committed catalog is the five-record r02c
identity extract from ``origin/codex/recover-grok-01a06111``. Recovered
``*mill*.py`` / ``*loop*.py`` scripts are not vendored.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ._contract import (
    CATALOG_ID,
    FACTORY,
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_SLICE_STRIDE,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_SLICE_OUT_OF_DOMAIN,
    GENERATOR,
    QUOTA_PER_ROUND,
    SLICE_ID,
    TtfRefusal,
    bind_import_twin,
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
WAVE_ROUNDS = (2,)

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


def _walk_mapping(node: ast.AST, consts: Mapping[str, Any]) -> Any:
    """Best-effort literal walk. Calls and names stay out (no exec)."""

    if isinstance(node, ast.Name) and node.id in consts:
        return consts[node.id]
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        if isinstance(node.operand, ast.Constant) and isinstance(node.operand.value, (int, float)):
            return -node.operand.value
    if isinstance(node, ast.List):
        return [_walk_mapping(elt, consts) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_walk_mapping(elt, consts) for elt in node.elts)
    if isinstance(node, ast.Dict):
        mapping: dict[str, Any] = {}
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:
                continue
            key = _walk_mapping(key_node, consts)
            if not isinstance(key, str):
                continue
            if key in {"spike_events", "spikes", "raster", "excerpt"}:
                continue
            mapping[key] = _walk_mapping(value_node, consts)
        return mapping
    if isinstance(node, ast.Call):
        func = node.func.id if isinstance(node.func, ast.Name) else None
        return {
            "_call": func,
            "args": [_walk_mapping(arg, consts) for arg in node.args],
            "kwargs": {
                keyword.arg: _walk_mapping(keyword.value, consts)
                for keyword in node.keywords
                if keyword.arg
            },
        }
    return None


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


def _plant_draft(
    source_name: str,
    *,
    record_id: Any = None,
    source_round: Any = None,
    index: Any = None,
    title: Any = "",
    domain: Any = "",
    sim_or_real: Any = "",
    goal: Any = "",
    proposed_action: Any = "",
    decision: Any = "",
    correctness: Any = "",
    rationale: Any = "",
    executed_action: Any = "",
    outcome: Any = "",
    reward_total: Any = None,
    reward_note: Any = "",
) -> dict[str, Any]:
    ident = _text(record_id)
    parsed_round = _round_from_id(ident)
    return {
        "record_id": ident,
        "source_round": source_round if type(source_round) is int else parsed_round,
        "index": index,
        "title": _text(title),
        "domain": _text(domain),
        "sim_or_real": _text(sim_or_real) or "designed",
        "goal": _text(goal),
        "proposed_action": _text(proposed_action),
        "decision": _text(decision),
        "correctness": _text(correctness) or "correct",
        "rationale": _text(rationale),
        "executed_action": _text(executed_action),
        "outcome": _text(outcome),
        "reward_total": 0.0 if reward_total is None else reward_total,
        "reward_note": _text(reward_note),
        "source_name": source_name,
    }


def _from_rec_dict(
    rec: Mapping[str, Any],
    source_name: str,
    index: int,
) -> dict[str, Any]:
    state = rec.get("state") if isinstance(rec.get("state"), dict) else {}
    proposed = rec.get("proposed_action") if isinstance(rec.get("proposed_action"), dict) else {}
    safety = rec.get("safety_decision") if isinstance(rec.get("safety_decision"), dict) else {}
    executed = rec.get("executed_action") if isinstance(rec.get("executed_action"), dict) else {}
    outcome = rec.get("future_outcome") if isinstance(rec.get("future_outcome"), dict) else {}
    note = _reward_note(rec.get("reward_components"))
    return _plant_draft(
        source_name,
        record_id=rec.get("id"),
        index=index,
        title=rec.get("title"),
        domain=state.get("domain") or rec.get("domain"),
        sim_or_real=state.get("sim_or_real"),
        goal=state.get("goal") or rec.get("goal"),
        proposed_action=proposed.get("name") or rec.get("proposed_action"),
        decision=safety.get("decision"),
        correctness=safety.get("correctness"),
        rationale=safety.get("rationale"),
        executed_action=executed.get("name") or rec.get("executed_action"),
        outcome=outcome.get("summary") or rec.get("outcome"),
        reward_total=_reward_total(note),
        reward_note=note,
    )


def _from_builder_fn(fn: ast.FunctionDef, source_name: str, index: int) -> dict[str, Any] | None:
    found: dict[str, Any] = {}
    for node in ast.walk(fn):
        if not isinstance(node, ast.Dict):
            continue
        for key_node, value_node in zip(node.keys, node.values):
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                continue
            if key_node.value not in {"id", "domain", "sim_or_real", "decision", "goal"}:
                continue
            if key_node.value in found:
                continue
            if isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
                found[key_node.value] = value_node.value
    if "id" not in found:
        return None
    return _plant_draft(
        source_name,
        record_id=found.get("id"),
        index=index,
        domain=found.get("domain"),
        sim_or_real=found.get("sim_or_real"),
        goal=found.get("goal"),
        decision=found.get("decision"),
    )


def plants_from_source(text: str, source_name: str = "snippet") -> tuple[Plant, ...]:
    """AST-extract one TTF identity catalog. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_AST_NOT_A_PLANT, f"mill source is not parseable: {exc}")
    consts: dict[str, Any] = {}
    recs: list[dict[str, Any]] = []
    builders: list[dict[str, Any]] = []
    for node in tree.body:
        item = _assigned(node)
        if item is not None:
            name, value = item
            resolved = _optional_const(value, consts)
            if resolved is not None:
                consts[name] = resolved
            match = REC_NAME_RE.match(name)
            if match and isinstance(value, ast.Dict):
                walked = _walk_mapping(value, consts)
                if isinstance(walked, dict):
                    recs.append(_from_rec_dict(walked, source_name, int(match.group(1))))
            continue
        if isinstance(node, ast.FunctionDef) and BUILDER_NAME_RE.match(node.name):
            index = int(BUILDER_NAME_RE.match(node.name).group(1))
            draft = _from_builder_fn(node, source_name, index)
            if draft is not None:
                builders.append(draft)
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


def _require_plant_fields(values: Mapping[str, Any], where: str) -> dict[str, Any]:
    missing = [field for field in PLANT_FIELDS if field not in values]
    refuse_when(bool(missing), FINDING_FIELD_MISSING, f"{where} missing {missing}")
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
    checked: dict[str, Any] = {}
    for field in PLANT_FIELDS:
        value = values[field]
        if field in {"source_round", "index"}:
            checked[field] = value
            continue
        if field == "reward_total":
            checked[field] = float(value)
            continue
        refuse_when(
            not isinstance(value, str),
            FINDING_FIELD_INVALID,
            f"{where}.{field} must be a string, got {shown(value)}",
        )
        checked[field] = value
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
    """Fail closed unless every row has identity and a 5-stride slice."""

    items = load_catalog().plants if plants is None else plants
    refuse_when(not items, FINDING_CATALOG_EMPTY, "catalog has no plants")
    refuse_when(
        len(items) != QUOTA_PER_ROUND,
        FINDING_CATALOG_SLICE_STRIDE,
        f"catalog length {len(items)} is not {QUOTA_PER_ROUND}",
    )
    _check_unique(items)
    rounds = tuple(sorted({plant.source_round for plant in items}))
    refuse_when(
        rounds != WAVE_ROUNDS,
        FINDING_CATALOG_SLICE_STRIDE,
        f"catalog rounds {list(rounds)} are not {list(WAVE_ROUNDS)}",
    )
    return {
        "status": "ok",
        "catalog_id": CATALOG_ID,
        "slice": SLICE_ID,
        "plants": len(items),
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
        FINDING_SLICE_OUT_OF_DOMAIN,
        f"no plant slice for r{round_n}",
    )
    return chunk


_EXTRACTED_ROWS: tuple[tuple[Any, ...], ...] = (
    (
        "ttf-r02c-011",
        2,
        1,
        "Heptox-Rehn HR-HIL / Ampoule A-7: Re2O7 vapor 18.4 kPa beats N2 4.2 slm "
        "by 208 us; correct MODIFY still eats an in-window quartz crack "
        "(partnered negative total -0.48)",
        "rhenium-heptoxide-sublimer",
        "hil",
        "Keep Ampoule A-7 vapor <= 12.0 kPa and finish the Re2O7 HIL pass "
        "without dumping heptoxide condensate onto the cold finger.",
        "cruise_n2_sweep",
        "MODIFY",
        "correct",
        "Vapor 18.4 kPa won by 208 us, so Ampoule A-7 is over the 12.0 kPa "
        "Re2O7 sublimer cap, not still a cold-ampoule story. Holding 4.2 slm "
        "predicts next-sample 19.6 kPa > 12.0. MODIFY: N2 4.2 -> 1.8 slm. "
        "Observed after clamp 11.2 kPa <= 12.0. A full REJECT is not "
        "indicated: a clean HIL pass accepts 1.8 slm.",
        "clamped_n2_sweep",
        "Process-correct MODIFY held vapor at 11.2 kPa on the HR-HIL dummy "
        "pad. At 24.200 ms a quartz neck crack already seated in Ampoule A-7 "
        "dumped heptoxide onto the cold finger. Clamp reduced dump energy; it "
        "did not prevent the dump. Partnered negative: process heads stay "
        "honest; world loss is named, not netted.",
        -0.48,
        "Partnered negative. Process-correct MODIFY on HIL dummy pad; world "
        "still charges inside the 42 ms raster. total -0.48 = 0.30 + -0.62 + "
        "-0.16 + 0.05 + -0.05. Named cold-finger isolate (abort_s=780) is not "
        "netted into task_progress.",
        "ttf_r02c_gen.py",
    ),
    (
        "ttf-r02c-012",
        2,
        2,
        "Samaco-Fell SF-3 / Press P-8: off-gas O2 84 ppm beats H2 2.4 Nm3/h "
        "by 168 us; correct MODIFY clamps hydrogen 2.4 -> 1.1",
        "samarium-cobalt-sinter",
        "designed",
        "Keep Press P-8 off-gas O2 <= 40 ppm and finish the SmCo binder-burn "
        "without oxidizing the compact.",
        "cruise_h2_binder_burn",
        "MODIFY",
        "correct",
        "Off-gas O2 84 ppm won by 168 us, so Press P-8 is over the 40 ppm "
        "SmCo sinter cap, not still a wet-binder story. Holding 2.4 Nm3/h "
        "predicts next-sample 96 ppm > 40. MODIFY: H2 2.4 -> 1.1 Nm3/h. "
        "Observed after clamp 28 ppm <= 40. A full REJECT is not indicated: "
        "a clean burn accepts 1.1 Nm3/h.",
        "clamped_h2_binder_burn",
        "Correct MODIFY held off-gas O2 at 28 ppm. Compact finished the "
        "binder-burn without oxidation. No in-window world charge.",
        1.01,
        "Correct MODIFY. O2 84 ppm > 40 cap; H2 2.4 -> 1.1 Nm3/h. "
        "total +1.01 = 0.38 + 0.30 + 0.16 + 0.10 + 0.07.",
        "ttf_r02c_gen.py",
    ),
    (
        "ttf-r02c-013",
        2,
        3,
        "Tetrach-Germ TG-2 / Kettle K-9: AE 52 pps beats kettle 86 C by 176 us; "
        "correct REJECT holds GeCl4 1.6 -> 0 kg/h",
        "germanium-tetrachloride-rectifier",
        "designed",
        "Keep Kettle K-9 crack AE <= 10 pps and finish the GeCl4 hearts-cut "
        "without dumping liquor through a quartz split.",
        "cruise_gecl4_hearts",
        "REJECT",
        "correct",
        "AE 52 pps won by 176 us and is over the 10 pps quartz crack cap. "
        "Kettle 86 C is under the 110 C boil-look and is not a license to "
        "keep boiling. REJECT: GeCl4 1.6 -> 0 kg/h hold. A MODIFY that only "
        "trims reflux would still load a cracking kettle.",
        "hold_for_crack",
        "Correct REJECT held GeCl4 at 0 kg/h. Quartz crack did not dump the "
        "kettle. Kettle 86 C remaining under the 110 C boil-look was the "
        "losing channel and did not justify a cruise.",
        0.8,
        "Correct REJECT. AE 52 pps > 10 cap; GeCl4 1.6 -> 0 kg/h. "
        "total +0.80 = 0.12 + 0.40 + 0.12 + 0.10 + 0.06.",
        "ttf_r02c_gen.py",
    ),
    (
        "ttf-r02c-014",
        2,
        4,
        "Tantala-Lith TL-2 sim / Puller X-4: seed 1488 C beats furnace glint "
        "1610 C by 178 us; correct ACCEPT leaves 0.22 mm/h",
        "lithium-tantalate-czochralski",
        "simulated",
        "Keep Puller X-4 seed <= 1540 C and finish the LiTaO3 pass at the "
        "filed 0.22 mm/h without an extra freeze-lid clamp.",
        "hold_lto_pull",
        "ACCEPT",
        "correct",
        "Seed 1488 C won by 178 us and is under the 1540 C freeze-lid cap. "
        "Furnace 1610 C is a lighting glint, not a seed reading. ACCEPT the "
        "filed 0.22 mm/h pull. Executed identical to proposed. An extra "
        "clamp is not indicated.",
        "hold_lto_pull",
        "Correct ACCEPT kept the filed 0.22 mm/h LiTaO3 pull. Seed stayed "
        "1489 C under 1540. Furnace remaining a lighting glint was the "
        "losing channel and did not justify an extra clamp.",
        1.08,
        "Correct ACCEPT. Seed 1488 C < 1540 C cap; glint unused. "
        "total +1.08 = 0.42 + 0.28 + 0.18 + 0.12 + 0.08.",
        "ttf_r02c_gen.py",
    ),
    (
        "ttf-r02c-015",
        2,
        5,
        "Oxychlor-Van OV-6 / Reactor R-11: live Cl2 0.42 vol% beats lagged "
        "XS-12 by 178 us; WRONG REJECT holds VOCl3 18 -> 0 (lagged interlock "
        "as trip)",
        "vanadium-oxytrichloride-oxychlor",
        "designed",
        "Keep Reactor R-11 live Cl2 <= 1.20 vol% and finish the VOCl3 pass "
        "at 18.0 kg/h without treating a lagged CIP interlock as a motion trip.",
        "cruise_vocl3_oxychlor",
        "REJECT",
        "incorrect",
        "XS-12 still reads closed, so the supervisor treats Reactor R-11 as "
        "already tripped and REJECT-holds VOCl3 18.0 -> 0 kg/h. Live Cl2 "
        "0.42 vol% is cited only as context. The closed contact is treated "
        "as a live motion trip.",
        "hold_for_lagged_interlock",
        "Incorrect REJECT held a legal 0.42 vol% Cl2 oxychlorinator because "
        "lagged XS-12 was bound as a live trip. Cost is a 16 min missed "
        "window. Live gas never reached 1.20 vol%.",
        -0.62,
        "Wrong-reject / lagged-interlock-as-trip. Live 0.42 < 1.20; XS-12 "
        "stale closed. total -0.62 = -0.26 + -0.10 + -0.22 + -0.10 + 0.06. "
        "Named missed window (missed_window_s=960) is not netted into a "
        "fake safety credit.",
        "ttf_r02c_gen.py",
    ),
)


def load_catalog() -> Catalog:
    """The committed r02c slice. Never reads a recovered mill script."""

    plants = tuple(
        plant_from_mapping(dict(zip(PLANT_FIELDS, row, strict=True)), f"row[{index}]")
        for index, row in enumerate(_EXTRACTED_ROWS)
    )
    return Catalog(CATALOG_ID, plants)


bind_import_twin(__name__)
