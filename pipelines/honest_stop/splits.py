"""Load the family registration and the held-out exclusion list."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json
from .scenarios import Scenario, catalog

__all__ = ["FamilyConfig", "config_digest", "load_family"]

REPO_ROOT = Path(__file__).resolve().parents[2]
FAMILY_PATH = REPO_ROOT / "config" / "agent-honest-stop" / "family.json"
EXCLUSION_PATH = REPO_ROOT / "config" / "agent-honest-stop" / "eval-exclusion.json"
_FAMILY_KEYS = (
    "dataset",
    "dedup_model",
    "eval_exclusion",
    "family",
    "ollama_url",
    "schema",
    "schema_version",
    "splits",
    "world",
    "writer_model",
)
_EXCLUSION_KEYS = ("list", "note", "schema_version", "task_ids")
_EXCLUSION_CODE = "config.exclusion"
_SPLITS_CODE = "config.splits"
_PIN_CODE = "config.pin"
_JSON_CODE = "config.json"


@dataclass(frozen=True)
class FamilyConfig:
    """The reviewed registration: models, splits, and the held-out task ids."""

    dataset: str
    writer_model: str
    dedup_model: str
    ollama_url: str
    splits: dict[str, str]
    excluded_task_ids: frozenset[str]
    config_sha256: str
    exclusion_sha256: str


def _sha(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise cv.FamilyError("config.unreadable", f"{path}: {exc}") from exc


def _decode(path: Path, payload: bytes) -> object:
    try:
        return load_strict_json(payload.decode("utf-8"))
    except (ValueError, RecursionError) as exc:
        raise cv.FamilyError(_JSON_CODE, f"{path}: {exc}") from exc


def _as_object(path: Path, document: object) -> dict:
    if isinstance(document, dict):
        return document
    raise cv.FamilyError(_JSON_CODE, f"{path}: expected an object")


def _read(path: Path) -> tuple[dict, str]:
    payload = _read_bytes(path)
    return _as_object(path, _decode(path, payload)), _sha(payload)


def _same_keys(document: dict, keys: tuple[str, ...]) -> bool:
    return set(document) == set(keys)


def _require_keys(document: dict, keys: tuple[str, ...], code: str) -> None:
    if _same_keys(document, keys):
        return
    raise cv.FamilyError(code, "unexpected keys")


def _expected_pins() -> dict[str, str]:
    return {
        "schema_version": cv.FAMILY_SCHEMA,
        "family": cv.FAMILY,
        "dataset": cv.DATASET,
        "world": cv.WORLD,
        "writer_model": cv.WRITER_MODEL,
        "dedup_model": cv.DEDUP_MODEL,
        "ollama_url": cv.OLLAMA_URL,
        "schema": cv.SCHEMA_RELATIVE,
        "eval_exclusion": "config/agent-honest-stop/eval-exclusion.json",
    }


def _pin_matches(document: dict, key: str, value: str) -> None:
    if document.get(key) == value:
        return
    raise cv.FamilyError(_PIN_CODE, f"{key} does not match the family pin")


def _pins(document: dict) -> None:
    for key, value in _expected_pins().items():
        _pin_matches(document, key, value)


def _require_schema_file() -> None:
    if (REPO_ROOT / cv.SCHEMA_RELATIVE).is_file():
        return
    raise cv.FamilyError("config.schema", "schema file is missing")


def _require_mapping(raw: object) -> dict:
    if isinstance(raw, dict):
        return raw
    raise cv.FamilyError(_SPLITS_CODE, "splits must be an object")


def _scenario_ids() -> set[str]:
    return {item.scenario_id for item in catalog()}


def _require_scenario_keys(raw: dict, scenario_ids: set[str]) -> None:
    if set(raw) == scenario_ids:
        return
    raise cv.FamilyError(_SPLITS_CODE, "splits must name each scenario once")


def _known_split(split: object) -> bool:
    if not isinstance(split, str):
        return False
    return split in cv.SPLITS


def _require_known_split(scenario_id: str, split: object) -> str:
    if _known_split(split):
        return str(split)
    raise cv.FamilyError(_SPLITS_CODE, f"unknown split for {scenario_id}")


def _collect_splits(raw: dict) -> dict[str, str]:
    splits: dict[str, str] = {}
    for scenario_id, split in raw.items():
        splits[scenario_id] = _require_known_split(scenario_id, split)
    return splits


def _splits(document: dict) -> dict[str, str]:
    raw = _require_mapping(document["splits"])
    _require_scenario_keys(raw, _scenario_ids())
    return _collect_splits(raw)


def _as_list(value: object) -> list:
    if isinstance(value, list):
        return value
    raise cv.FamilyError(_EXCLUSION_CODE, "task_ids must be a non-empty list")


def _nonempty(value: list) -> None:
    if value:
        return
    raise cv.FamilyError(_EXCLUSION_CODE, "task_ids must be a non-empty list")


def _text_item(item: object) -> bool:
    if not isinstance(item, str):
        return False
    return bool(item.strip())


def _all_text(value: list) -> None:
    if all(_text_item(item) for item in value):
        return
    raise cv.FamilyError(_EXCLUSION_CODE, "task ids must be text")


def _unique(value: list) -> bool:
    return len(value) == len(set(value))


def _sorted_rows(value: list) -> bool:
    return value == sorted(value)


def _unique_sorted(value: list) -> bool:
    if not _unique(value):
        return False
    return _sorted_rows(value)


def _require_unique_sorted(value: list) -> None:
    if _unique_sorted(value):
        return
    raise cv.FamilyError(_EXCLUSION_CODE, "task_ids must be sorted unique text")


def _task_ids(value: object) -> frozenset[str]:
    rows = _as_list(value)
    _nonempty(rows)
    _all_text(rows)
    _require_unique_sorted(rows)
    return frozenset(rows)


def _version_ok(document: dict) -> bool:
    if document["schema_version"] != cv.EXCLUSION_SCHEMA:
        return False
    return document["list"] == cv.EXCLUSION_LIST


def _require_version(document: dict) -> None:
    if _version_ok(document):
        return
    raise cv.FamilyError(_EXCLUSION_CODE, "exclusion list is not the held-out list")


def _note_ok(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return bool(value.strip())


def _require_note(document: dict) -> None:
    if _note_ok(document["note"]):
        return
    raise cv.FamilyError(_EXCLUSION_CODE, "note must be text")


def _exclusion(document: dict) -> frozenset[str]:
    _require_keys(document, _EXCLUSION_KEYS, _EXCLUSION_CODE)
    _require_version(document)
    _require_note(document)
    return _task_ids(document["task_ids"])


def _is_held_out(scenario: Scenario, splits: dict[str, str]) -> bool:
    return splits[scenario.scenario_id] == cv.HELD_OUT


def _held_ids(splits: dict[str, str]) -> set[str]:
    return {item.task_id for item in catalog() if _is_held_out(item, splits)}


def _held_out_agrees(splits: dict[str, str], excluded: frozenset[str]) -> None:
    if _held_ids(splits) == excluded:
        return
    raise cv.FamilyError(_EXCLUSION_CODE, "held-out splits and task ids disagree")


def config_digest() -> str:
    """SHA-256 of the family registration bytes."""

    return _sha(_read_bytes(FAMILY_PATH))


def load_family() -> FamilyConfig:
    """Read and cross-check the registration. A drift raises :class:`FamilyError`."""

    document, digest = _read(FAMILY_PATH)
    _require_keys(document, _FAMILY_KEYS, "config.keys")
    _pins(document)
    _require_schema_file()
    splits = _splits(document)
    exclusion, exclusion_digest = _read(EXCLUSION_PATH)
    excluded = _exclusion(exclusion)
    _held_out_agrees(splits, excluded)
    return FamilyConfig(
        dataset=document["dataset"],
        writer_model=document["writer_model"],
        dedup_model=document["dedup_model"],
        ollama_url=document["ollama_url"],
        splits=splits,
        excluded_task_ids=excluded,
        config_sha256=digest,
        exclusion_sha256=exclusion_digest,
    )


bind_import_twin(__name__)
