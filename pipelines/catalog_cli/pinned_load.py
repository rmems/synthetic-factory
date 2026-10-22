"""Pinned catalog load and the shared keyed-plant source reader.

Refusal text matches the loaders these helpers replaced: each pin is
checked before the next field is read, and a missing later field does not
hide an earlier mismatch.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Any

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
    from .source_const import keyed_plant_rows, require_positive_base
else:
    from catalog_cli.source_const import keyed_plant_rows, require_positive_base
    from oracle_grounded.import_twins import bind_import_twin

_SKIP = object()


def _readers(module: Any) -> SimpleNamespace:
    field, require_text, mill_from_row, plant_from_row, read_jsonl, registry_ids = (
        module.CATALOG_HOOKS
    )
    return SimpleNamespace(
        field=field,
        require_text=require_text,
        mill_from_row=mill_from_row,
        plant_from_row=plant_from_row,
        read_jsonl=read_jsonl,
        registry_ids=registry_ids,
        load_strict_json=module.load_strict_json,
        sha256_bytes=module.sha256_bytes,
        default_catalog_dir=module.default_catalog_dir,
        catalog=module.Catalog,
    )


def _read_text(path: Path, refusal: Callable[..., BaseException], code: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise refusal(code, f"{path} is missing") from exc


def _strict_meta(
    text: str,
    load_json: Callable[[str], Any],
    contract: Any,
    refusal: Callable[..., BaseException],
) -> Any:
    try:
        return load_json(text)
    except ValueError as exc:
        raise refusal(
            contract.FINDING_CATALOG_FIELD_INVALID,
            f"{contract.CATALOG_FILENAME} is not strict JSON",
        ) from exc


def _text_pin(meta: Any, hooks: SimpleNamespace, contract: Any, packed: tuple[Any, ...]) -> Any:
    refusal, key, want = packed
    got = hooks.field(meta, key, str, contract.CATALOG_FILENAME)
    if got != want:
        raise refusal(
            contract.FINDING_CATALOG_FIELD_INVALID,
            f"{contract.CATALOG_FILENAME}.{key} must be {want}",
        )
    return got


def _refuse_bad_quota(got: Any, contract: Any, refusal: Callable[..., BaseException]) -> None:
    bad = isinstance(got, bool)
    if not bad:
        bad = got != contract.QUOTA_PER_ROUND
    if bad:
        raise refusal(
            contract.FINDING_CATALOG_FIELD_INVALID,
            f"{contract.CATALOG_FILENAME}.quota_per_round must be {contract.QUOTA_PER_ROUND}",
        )


def _checked_identity(
    meta: Any,
    hooks: SimpleNamespace,
    contract: Any,
    refusal: Callable[..., BaseException],
) -> tuple[Any, Any]:
    filename = contract.CATALOG_FILENAME
    catalog_id = hooks.require_text(
        hooks.field(meta, "catalog_id", str, filename),
        f"{filename}.catalog_id",
        contract.FINDING_CATALOG_FIELD_INVALID,
    )
    _text_pin(meta, hooks, contract, (refusal, "format", contract.CATALOG_FORMAT))
    factory = _text_pin(meta, hooks, contract, (refusal, "factory", contract.FACTORY))
    _text_pin(meta, hooks, contract, (refusal, "mill_prefix", contract.MILL_PREFIX))
    _text_pin(meta, hooks, contract, (refusal, "record_kind", contract.RECORD_KIND))
    got = hooks.field(meta, "quota_per_round", int, filename)
    _refuse_bad_quota(got, contract, refusal)
    return catalog_id, factory


def _mills(
    mill_rows: list[Any],
    mill_from_row: Callable[..., Any],
    filename: str,
) -> tuple[Any, ...]:
    return tuple(
        mill_from_row(row, f"{filename}.mills[{index}]") for index, row in enumerate(mill_rows)
    )


def _read_catalog_meta(
    catalog_dir: Path,
    hooks: SimpleNamespace,
    contract: Any,
    refusal: Callable[..., BaseException],
) -> dict[str, Any]:
    filename = contract.CATALOG_FILENAME
    meta_path = catalog_dir / filename
    meta = _strict_meta(
        _read_text(meta_path, refusal, contract.FINDING_CATALOG_FILE_MISSING),
        hooks.load_strict_json,
        contract,
        refusal,
    )
    catalog_id, factory = _checked_identity(meta, hooks, contract, refusal)
    return {
        "meta": meta,
        "catalog_id": catalog_id,
        "factory": factory,
        "plant_count": hooks.field(meta, "plant_count", int, filename),
        "plants_sha256": hooks.field(meta, "plants_sha256", str, filename),
        "mills": _mills(hooks.field(meta, "mills", list, filename), hooks.mill_from_row, filename),
        "contract": contract,
        "refusal": refusal,
    }


def _read_bytes(path: Path, refusal: Callable[..., BaseException], code: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise refusal(code, f"{path} is missing") from exc


def _refuse_digest(
    digest: str,
    pinned: str,
    contract: Any,
    refusal: Callable[..., BaseException],
) -> None:
    if digest != pinned:
        name = contract.PLANTS_FILENAME
        raise refusal(
            contract.FINDING_CATALOG_SHA256_MISMATCH,
            f"{name} digest {digest} != catalog pin {pinned}",
        )


def _refuse_unregistered(
    factory: str,
    registry: set[str],
    contract: Any,
    refusal: Callable[..., BaseException],
) -> None:
    if factory not in registry:
        raise refusal(
            contract.FINDING_FACTORY_NOT_REGISTERED,
            f"{factory} is not a registry path_id",
        )


def _refuse_row_count(
    rows: tuple[Any, ...],
    plant_count: int,
    contract: Any,
    refusal: Callable[..., BaseException],
) -> None:
    if len(rows) != plant_count:
        raise refusal(
            contract.FINDING_CATALOG_FIELD_INVALID,
            f"{contract.CATALOG_FILENAME}.plant_count is {plant_count}, file has {len(rows)}",
        )


def _plants_from_rows(
    rows: tuple[Any, ...],
    plant_from_row: Callable[..., Any],
    filename: str,
) -> tuple[Any, ...]:
    return tuple(
        plant_from_row(row, f"{filename}:{index}") for index, row in enumerate(rows, start=1)
    )


def _read_catalog_plants(
    catalog_dir: Path,
    hooks: SimpleNamespace,
    pins: Mapping[str, Any],
) -> tuple[tuple[Any, ...], str]:
    contract = pins["contract"]
    refusal = pins["refusal"]
    plants_path = catalog_dir / contract.PLANTS_FILENAME
    payload = _read_bytes(plants_path, refusal, contract.FINDING_CATALOG_FILE_MISSING)
    digest = hooks.sha256_bytes(payload)
    _refuse_digest(digest, pins["plants_sha256"], contract, refusal)
    _refuse_unregistered(pins["factory"], hooks.registry_ids(), contract, refusal)
    rows = hooks.read_jsonl(plants_path)
    _refuse_row_count(rows, pins["plant_count"], contract, refusal)
    return _plants_from_rows(rows, hooks.plant_from_row, contract.PLANTS_FILENAME), digest


def _refuse_duplicate_ids(
    plants: tuple[Any, ...],
    contract: Any,
    refusal: Callable[..., BaseException],
) -> None:
    seen: set[str] = set()
    for plant in plants:
        if plant.plant_id in seen:
            raise refusal(
                contract.FINDING_PLANT_DUPLICATE_ID,
                f"duplicate plant_id {plant.plant_id}",
            )
        seen.add(plant.plant_id)


def _mill_counts(plants: tuple[Any, ...]) -> dict[str, int]:
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    return by_mill


def _refuse_mill_ids(
    mills: tuple[Any, ...],
    by_mill: Mapping[str, int],
    contract: Any,
    refusal: Callable[..., BaseException],
) -> None:
    mill_ids = {mill.mill_id for mill in mills}
    if mill_ids != set(by_mill):
        raise refusal(
            contract.FINDING_CATALOG_FIELD_INVALID,
            "catalog mills do not match plant mill_id values",
        )


def _refuse_plant_counts(
    mills: tuple[Any, ...],
    by_mill: Mapping[str, int],
    contract: Any,
    refusal: Callable[..., BaseException],
) -> None:
    for mill in mills:
        if by_mill[mill.mill_id] != mill.plant_count:
            raise refusal(
                contract.FINDING_CATALOG_FIELD_INVALID,
                f"{mill.mill_id} plant_count {mill.plant_count} != {by_mill[mill.mill_id]}",
            )


def _refuse_mill_shape(
    contract: Any,
    refusal: Callable[..., BaseException],
    plants: tuple[Any, ...],
    mills: tuple[Any, ...],
) -> None:
    _refuse_duplicate_ids(plants, contract, refusal)
    by_mill = _mill_counts(plants)
    _refuse_mill_ids(mills, by_mill, contract, refusal)
    _refuse_plant_counts(mills, by_mill, contract, refusal)


def load_pinned_catalog(
    directory: Path | None,
    module: Any,
    contract: Any,
    refusal: Callable[..., BaseException],
) -> Any:
    """Load one mill catalog. ``module`` reads rows; ``contract`` holds the pins."""

    hooks = _readers(module)
    catalog_dir = Path(hooks.default_catalog_dir() if directory is None else directory)
    pins = _read_catalog_meta(catalog_dir, hooks, contract, refusal)
    plants, digest = _read_catalog_plants(catalog_dir, hooks, pins)
    mills = pins["mills"]
    _refuse_mill_shape(contract, refusal, plants, mills)
    return hooks.catalog(
        catalog_id=pins["catalog_id"],
        directory=catalog_dir,
        factory=pins["factory"],
        plants_sha256=digest,
        plants=plants,
        mills=mills,
        meta=pins["meta"],
    )


def _parsed_tree(
    text: str,
    source: str,
    refusal: Callable[..., BaseException],
    code: str,
) -> ast.Module:
    try:
        return ast.parse(text)
    except SyntaxError as exc:
        raise refusal(code, f"{source} does not parse: {exc}") from exc


def _assign_target(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    return None


def _ann_target(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        value = node.value
        if value is not None:
            return node.target.id, value
    return None


def _bound_value(node: ast.AST) -> tuple[str, ast.AST] | None:
    assigned = _assign_target(node)
    if assigned is not None:
        return assigned
    return _ann_target(node)


def _matched(
    assigned: tuple[str, ast.AST] | None,
    wanted: str,
    evaluate: Callable[[ast.AST], Any],
) -> Any:
    if assigned is None:
        return _SKIP
    name, value = assigned
    if name != wanted:
        return _SKIP
    return evaluate(value)


def _value_named(tree: ast.Module, wanted: str, evaluate: Callable[[ast.AST], Any]) -> Any:
    found: Any = _SKIP
    for node in tree.body:
        matched = _matched(_bound_value(node), wanted, evaluate)
        if matched is not _SKIP:
            found = matched
    return found


def _found(value: Any) -> Any:
    if value is _SKIP:
        return None
    return value


def _require_list(
    raw: Any,
    names: tuple[str, str],
    refusal: Callable[..., BaseException],
    code: str,
) -> list[Any]:
    source, list_name = names
    if not isinstance(raw, list) or not raw:
        raise refusal(code, f"{source} has no {list_name} list")
    return raw


def _require_mill(
    mill_id: str,
    pattern: str,
    fullmatch: Callable[[str], Any],
    packed: tuple[Any, str],
) -> None:
    refusal, code = packed
    if fullmatch(mill_id):
        return
    raise refusal(code, f"mill_id {mill_id!r} is not {pattern}")


def _chosen_base(given: Any, inferred: Any) -> Any:
    if given is None:
        return inferred
    return given


def keyed_plants_from_source(
    text: str,
    identity: Mapping[str, Any],
    spec: Mapping[str, Any],
    refusals: tuple[Callable[..., BaseException], str, str, str],
) -> tuple[dict[str, Any], ...]:
    """AST-extract one keyed plant list. ``spec`` names the list, base, and prefix."""

    refusal, parse_code, invalid_code, missing_code = refusals
    source = identity["source"]
    tree = _parsed_tree(text, source, refusal, parse_code)
    raw = _found(_value_named(tree, spec["list_name"], spec["evaluate"]))
    inferred = _found(_value_named(tree, spec["base_name"], spec["evaluate"]))
    rows = _require_list(raw, (source, spec["list_name"]), refusal, parse_code)
    _require_mill(identity["mill_id"], spec["pattern"], spec["fullmatch"], (refusal, invalid_code))
    base = require_positive_base(
        _chosen_base(identity["base_round"], inferred),
        identity["mill_id"],
        spec["prefix"],
        lambda: refusal(invalid_code, f"{source} {spec['base_name']} must be a positive int"),
    )
    return keyed_plant_rows(
        rows,
        spec["keys"],
        {
            "mill_id": identity["mill_id"],
            "source": source,
            "base_round": base,
            "label": spec["label"],
        },
        (
            lambda message: refusal(parse_code, message),
            lambda message: refusal(missing_code, message),
        ),
    )


bind_import_twin(__name__)
