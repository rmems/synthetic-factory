"""Constant-source checks shared by the plant catalogs.

The generate-shape catalogs used to copy these blocks. One copy keeps the
refusal text and the returned set identical.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from oracle_grounded.import_twins import bind_import_twin

_LoadJson = Callable[[str], Any]


def registry_factory_ids(
    repo_root: Callable[[], Path],
    load_strict_json: _LoadJson,
    refuse: Callable[[str], BaseException],
) -> set[str]:
    """Path ids from ``config/FACTORY-REGISTRY.json``.

    A row that is not a dict, or a ``path_id`` that is not a str, is skipped.
    ``refuse(message)`` must return the refusal exception for an unreadable
    registry or a ``factories`` value that is not a list.
    """

    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        payload = load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise refuse(f"factory registry is unreadable: {exc}") from exc
    factories = payload.get("factories") if isinstance(payload, dict) else None
    if not isinstance(factories, list):
        raise refuse("factory registry factories is not a list")
    ids: set[str] = set()
    for row in factories:
        if not isinstance(row, dict):
            continue
        path_id = row.get("path_id")
        if isinstance(path_id, str):
            ids.add(path_id)
    return ids


def const_dict(
    node: ast.Dict,
    evaluate: Callable[[ast.AST], Any],
    refuse: Callable[[], BaseException],
) -> dict[Any, Any]:
    """Evaluate a dict literal. A ``None`` key is unpacking and raises first."""

    keys: list[ast.expr] = []
    for key in node.keys:
        if key is None:
            raise refuse()
        keys.append(key)
    return {
        evaluate(key): evaluate(value) for key, value in zip(keys, node.values, strict=True)
    }


def plant_const_eval(node: ast.AST, refusal: Callable[..., BaseException], finding: str) -> Any:
    """Literal values only. Refuses calls, names, and starred dicts."""

    def evaluate(item: ast.AST) -> Any:
        return plant_const_eval(item, refusal, finding)

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [evaluate(item) for item in node.elts]
        return values if isinstance(node, ast.List) else tuple(values)
    if isinstance(node, ast.Dict):
        return const_dict(
            node,
            evaluate,
            lambda: refusal(finding, "plant source uses dict unpacking"),
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -evaluate(node.operand)
    raise refusal(
        finding,
        f"plant source is not a constant ({type(node).__name__})",
    )


def require_positive_base(
    base: Any,
    mill_id: str,
    prefix: str,
    refuse: Callable[[], BaseException],
) -> int:
    """Use ``base``, or the numeric tail of ``mill_id``. ``refuse()`` has the message."""

    resolved = base
    if resolved is None:
        resolved = int(mill_id[len(prefix) :])
    if isinstance(resolved, bool) or not isinstance(resolved, int):
        raise refuse()
    if resolved < 1:
        raise refuse()
    return resolved


def keyed_plant_rows(
    raw_plants: list[Any],
    keys: tuple[str, ...],
    identity: Mapping[str, Any],
    refusals: tuple[Callable[[str], BaseException], Callable[[str], BaseException]],
) -> tuple[dict[str, Any], ...]:
    """One row per dict. ``refusals`` is ``(parse, missing)`` and each returns an exception."""

    refuse_parse, refuse_missing = refusals
    mill_id = identity["mill_id"]
    source = identity["source"]
    base = identity["base_round"]
    label = identity["label"]
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_plants):
        if not isinstance(raw, dict):
            raise refuse_parse(f"{source} {label}[{index}] is not an object")
        missing = [key for key in keys if key not in raw]
        if missing:
            raise refuse_missing(f"{source} {label}[{index}] missing {missing[0]}")
        row = {
            "plant_id": f"{mill_id}:{raw['slug']}",
            "mill_id": mill_id,
            "source": source,
            "base_round": base,
        }
        row.update({key: raw[key] for key in keys})
        rows.append(row)
    return tuple(rows)


def _refuse_mismatched_pins(
    contract: Any,
    refusal: Callable[..., BaseException],
    actual: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> None:
    filename = contract.CATALOG_FILENAME
    for key, want in expected.items():
        got = actual[key]
        bad = got != want
        if key == "quota_per_round":
            bad = isinstance(got, bool) or got != want
        if bad:
            raise refusal(
                contract.FINDING_CATALOG_FIELD_INVALID,
                f"{filename}.{key} must be {want}",
            )


def _refuse_mill_count_mismatch(
    contract: Any,
    refusal: Callable[..., BaseException],
    plants: tuple[Any, ...],
    mills: tuple[Any, ...],
) -> None:
    seen: set[str] = set()
    for plant in plants:
        if plant.plant_id in seen:
            raise refusal(
                contract.FINDING_PLANT_DUPLICATE_ID,
                f"duplicate plant_id {plant.plant_id}",
            )
        seen.add(plant.plant_id)
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    mill_ids = {mill.mill_id for mill in mills}
    if mill_ids != set(by_mill):
        raise refusal(
            contract.FINDING_CATALOG_FIELD_INVALID,
            "catalog mills do not match plant mill_id values",
        )
    for mill in mills:
        if by_mill[mill.mill_id] != mill.plant_count:
            raise refusal(
                contract.FINDING_CATALOG_FIELD_INVALID,
                f"{mill.mill_id} plant_count {mill.plant_count} != {by_mill[mill.mill_id]}",
            )


def _read_catalog_meta(
    catalog_dir: Path,
    module: Any,
    contract: Any,
    refusal: Callable[..., BaseException],
) -> dict[str, Any]:
    meta_path = catalog_dir / contract.CATALOG_FILENAME
    try:
        meta_text = meta_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise refusal(contract.FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing") from exc
    try:
        meta = module.load_strict_json(meta_text)
    except ValueError as exc:
        raise refusal(
            contract.FINDING_CATALOG_FIELD_INVALID,
            f"{contract.CATALOG_FILENAME} is not strict JSON",
        ) from exc
    catalog_id = module._require_text(
        module._field(meta, "catalog_id", str, contract.CATALOG_FILENAME),
        f"{contract.CATALOG_FILENAME}.catalog_id",
        contract.FINDING_CATALOG_FIELD_INVALID,
    )
    fmt = module._field(meta, "format", str, contract.CATALOG_FILENAME)
    factory = module._field(meta, "factory", str, contract.CATALOG_FILENAME)
    prefix = module._field(meta, "mill_prefix", str, contract.CATALOG_FILENAME)
    kind = module._field(meta, "record_kind", str, contract.CATALOG_FILENAME)
    quota = module._field(meta, "quota_per_round", int, contract.CATALOG_FILENAME)
    _refuse_mismatched_pins(
        contract,
        refusal,
        {
            "format": fmt,
            "factory": factory,
            "mill_prefix": prefix,
            "record_kind": kind,
            "quota_per_round": quota,
        },
        {
            "format": contract.CATALOG_FORMAT,
            "factory": contract.FACTORY,
            "mill_prefix": contract.MILL_PREFIX,
            "record_kind": contract.RECORD_KIND,
            "quota_per_round": contract.QUOTA_PER_ROUND,
        },
    )
    mill_rows = module._field(meta, "mills", list, contract.CATALOG_FILENAME)
    return {
        "meta": meta,
        "catalog_id": catalog_id,
        "factory": factory,
        "plant_count": module._field(meta, "plant_count", int, contract.CATALOG_FILENAME),
        "plants_sha256": module._field(meta, "plants_sha256", str, contract.CATALOG_FILENAME),
        "mills": tuple(
            module._mill_from_row(row, f"{contract.CATALOG_FILENAME}.mills[{index}]")
            for index, row in enumerate(mill_rows)
        ),
        "contract": contract,
        "refusal": refusal,
    }


def _read_catalog_plants(
    catalog_dir: Path,
    module: Any,
    pins: Mapping[str, Any],
) -> tuple[tuple[Any, ...], str]:
    contract = pins["contract"]
    refusal = pins["refusal"]
    plants_path = catalog_dir / contract.PLANTS_FILENAME
    try:
        plants_bytes = plants_path.read_bytes()
    except OSError as exc:
        raise refusal(contract.FINDING_CATALOG_FILE_MISSING, f"{plants_path} is missing") from exc
    digest = module.sha256_bytes(plants_bytes)
    plants_sha256 = pins["plants_sha256"]
    if digest != plants_sha256:
        raise refusal(
            contract.FINDING_CATALOG_SHA256_MISMATCH,
            f"{contract.PLANTS_FILENAME} digest {digest} != catalog pin {plants_sha256}",
        )
    factory = pins["factory"]
    if factory not in module._registry_factory_ids():
        raise refusal(
            contract.FINDING_FACTORY_NOT_REGISTERED,
            f"{factory} is not a registry path_id",
        )
    rows = module._read_jsonl(plants_path)
    plant_count = pins["plant_count"]
    if len(rows) != plant_count:
        raise refusal(
            contract.FINDING_CATALOG_FIELD_INVALID,
            f"{contract.CATALOG_FILENAME}.plant_count is {plant_count}, file has {len(rows)}",
        )
    plants = tuple(
        module._plant_from_row(row, f"{contract.PLANTS_FILENAME}:{index}")
        for index, row in enumerate(rows, start=1)
    )
    return plants, digest


def load_pinned_catalog(
    directory: Path | None,
    module: Any,
    contract: Any,
    refusal: Callable[..., BaseException],
) -> Any:
    """Load one mill catalog. ``module`` reads rows; ``contract`` holds the pins."""

    catalog_dir = Path(module.default_catalog_dir() if directory is None else directory)
    pins = _read_catalog_meta(catalog_dir, module, contract, refusal)
    plants, digest = _read_catalog_plants(catalog_dir, module, pins)
    mills = pins["mills"]
    _refuse_mill_count_mismatch(contract, refusal, plants, mills)
    return module.Catalog(
        catalog_id=pins["catalog_id"],
        directory=catalog_dir,
        factory=pins["factory"],
        plants_sha256=digest,
        plants=plants,
        mills=mills,
        meta=pins["meta"],
    )


bind_import_twin(__name__)
