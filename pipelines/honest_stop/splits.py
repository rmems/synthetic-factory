"""Load the family registration and the held-out exclusion list."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json
from .scenarios import catalog

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


def _read(path: Path) -> tuple[dict, str]:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise cv.FamilyError("config.unreadable", f"{path}: {exc}") from exc
    try:
        document = load_strict_json(payload.decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise cv.FamilyError("config.json", f"{path}: {exc}") from exc
    if not isinstance(document, dict):
        raise cv.FamilyError("config.json", f"{path}: expected an object")
    return document, _sha(payload)


def _require_keys(document: dict, keys: tuple[str, ...], code: str) -> None:
    if set(document) != set(keys):
        raise cv.FamilyError(code, "unexpected keys")


def _pins(document: dict) -> None:
    expected = {
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
    for key, value in expected.items():
        if document.get(key) != value:
            raise cv.FamilyError("config.pin", f"{key} does not match the family pin")
    if not (REPO_ROOT / cv.SCHEMA_RELATIVE).is_file():
        raise cv.FamilyError("config.schema", "schema file is missing")


def _splits(document: dict) -> dict[str, str]:
    raw = document["splits"]
    if not isinstance(raw, dict):
        raise cv.FamilyError("config.splits", "splits must be an object")
    scenario_ids = {item.scenario_id for item in catalog()}
    if set(raw) != scenario_ids:
        raise cv.FamilyError("config.splits", "splits must name each scenario once")
    splits = {}
    for scenario_id, split in raw.items():
        if split not in cv.SPLITS:
            raise cv.FamilyError("config.splits", f"unknown split for {scenario_id}")
        splits[scenario_id] = split
    return splits


def _task_ids(value: object) -> frozenset[str]:
    if not isinstance(value, list) or not value:
        raise cv.FamilyError("config.exclusion", "task_ids must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise cv.FamilyError("config.exclusion", "task ids must be text")
    if len(value) != len(set(value)) or value != sorted(value):
        raise cv.FamilyError("config.exclusion", "task_ids must be sorted unique text")
    return frozenset(value)


def _exclusion(document: dict) -> frozenset[str]:
    _require_keys(document, _EXCLUSION_KEYS, "config.exclusion")
    version_ok = document["schema_version"] == cv.EXCLUSION_SCHEMA
    if not version_ok or document["list"] != cv.EXCLUSION_LIST:
        raise cv.FamilyError("config.exclusion", "exclusion list is not the held-out list")
    if not isinstance(document["note"], str) or not document["note"].strip():
        raise cv.FamilyError("config.exclusion", "note must be text")
    return _task_ids(document["task_ids"])


def _held_out_agrees(splits: dict[str, str], excluded: frozenset[str]) -> None:
    held = {item.task_id for item in catalog() if splits[item.scenario_id] == cv.HELD_OUT}
    if held != excluded:
        raise cv.FamilyError("config.exclusion", "held-out splits and task ids disagree")


def config_digest() -> str:
    """SHA-256 of the family registration bytes."""

    try:
        payload = FAMILY_PATH.read_bytes()
    except OSError as exc:
        raise cv.FamilyError("config.unreadable", str(exc)) from exc
    return _sha(payload)


def load_family() -> FamilyConfig:
    """Read and cross-check the registration. A drift raises :class:`FamilyError`."""

    document, digest = _read(FAMILY_PATH)
    _require_keys(document, _FAMILY_KEYS, "config.keys")
    _pins(document)
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
