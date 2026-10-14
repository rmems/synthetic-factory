#!/usr/bin/env python3
"""Pinned OBS plant catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` plus three jsonl members
(hop plants, leftover3 pairs, leftover-spec rows). Load verifies each
digest and field before a plant is trusted. Mill scripts are text only
via :func:`plants_from_source`.
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    FACTORY,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_DUPLICATE_ID,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    HOP_FILENAME,
    LEFTOVER3_FILENAME,
    LEFTOVER_SPECS_FILENAME,
    MILL_PREFIX,
    ObsRefusal,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    SHAPE_HOP,
    SHAPE_LEFTOVER3,
    SHAPE_LEFTOVER_SPEC,
    bind_import_twin,
    load_strict_json,
    repo_root,
)

MILL_ID_RE = re.compile(r"^obs_(?:r\d+|leftover\d+)$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

HOP_REQUIRED = (
    "slug",
    "lslug",
    "svc",
    "lsvc",
    "lie",
    "llie",
    "file",
    "lfile",
    "fail_val",
    "fix_val",
    "query",
    "lquery",
)
SPEC_REQUIRED = (
    "vendor",
    "ok_slug",
    "bad_slug",
    "noun",
    "prefix",
    "panel",
    "needle",
    "lie_core",
    "false_lead",
    "knob",
    "old",
    "new",
    "wrong_knob",
    "wrong_old",
    "wrong_new",
    "wrong2_old",
    "wrong2_new",
)
SPEC_TUPLE_KEYS = (
    "vendor",
    "prefix",
    "noun",
    "panel",
    "needle",
    "ok_slug",
    "bad_slug",
    "lie_core",
    "false_lead",
    "knob",
    "old",
    "new",
    "wrong_knob",
    "wrong_old",
    "wrong_new",
    "wrong2_old",
    "wrong2_new",
)
R401_ARG_NAMES = (
    "kind",
    "slug",
    "lslug",
    "svc",
    "lsvc",
    "dash",
    "ldash",
    "yq",
    "fail_line",
    "fix_line",
    "fail_val",
    "fix_val",
    "false_yq",
    "false_lead",
    "false_old",
    "false_new",
    "false_patch",
    "false2_old",
    "false2_new",
    "false2_patch",
    "lie",
    "llie",
    "new_vs",
    "novel",
)
DEFAULT_KIND_NS = {
    "tempo": ("tempo", "querier"),
    "loki": ("loki", "querier"),
    "prom": ("monitoring", "prometheus"),
    "mimir": ("mimir", "querier"),
    "otel": ("otel", "otelcol"),
    "grafana": ("grafana", "grafana"),
    "thanos": ("thanos", "query"),
    "pyro": ("pyro", "pyroscope"),
    "vm": ("vm", "vmselect"),
    "ch": ("clickhouse", "clickhouse"),
    "am": ("monitoring", "alertmanager"),
}
SPEC_INDEX_KIND = "obs-leftover-spec-index/1"
PROM_QUERY_PATH = "/api/v1/query"
_CH_WHERE = "SELECT count() FROM otel.traces WHERE service="
_KIND_BIT_KEYS = (
    "query",
    "lquery",
    "exec_path",
    "exec_obs",
    "exec_err",
    "exec_ok",
    "grafana_obs",
    "truth_cmd",
    "truth_obs",
)

__all__ = [
    "Catalog",
    "Mill",
    "Plant",
    "catalog_check",
    "default_catalog_dir",
    "load_catalog",
    "plants_from_source",
    "sha256_bytes",
]

@dataclass(frozen=True)
class Plant:
    """One observability plant: hop pair, leftover3 pair, or leftover spec."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    shape: str
    slug: str
    payload: Mapping[str, Any]

@dataclass(frozen=True)
class Mill:
    mill_id: str
    base_round: int
    source: str
    plant_count: int
    shape: str

@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    directory: Path
    factory: str
    plants: tuple[Plant, ...]
    mills: tuple[Mill, ...]
    meta: Mapping[str, Any]
    leftover_spec_index: Mapping[str, Any] | None = None

    def plant(self, plant_id: str) -> Plant:
        for item in self.plants:
            if item.plant_id == plant_id:
                return item
        raise ObsRefusal(FINDING_PLANT_NOT_FOUND, f"no plant {plant_id!r} in the catalog")

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        found = tuple(item for item in self.plants if item.mill_id == mill_id)
        if not found:
            raise ObsRefusal(FINDING_MILL_NOT_FOUND, f"no mill {mill_id!r} in the catalog")
        return found

    def pair_plants(self) -> tuple[Plant, ...]:
        return tuple(
            item for item in self.plants if item.shape in {SHAPE_HOP, SHAPE_LEFTOVER3}
        )

def default_catalog_dir() -> Path:
    return repo_root() / "config" / "obs"

def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()

def _const_eval(node: ast.AST) -> Any:
    """Literal values only. Other calls refuse."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.Set):
        return {_const_eval(item) for item in node.elts}
    return _const_mapping_or_negative(node)

def _const_mapping_or_negative(node: ast.AST) -> Any:
    """A dict display (``**`` unpacking refused) or ``-operand``; other node types are refused."""

    if isinstance(node, ast.Dict):
        # Refuse ``**`` unpacking before any key or value is evaluated.
        pairs: list[tuple[ast.expr, ast.expr]] = []
        for key, value in zip(node.keys, node.values):
            if key is None:
                raise ObsRefusal(FINDING_SOURCE_NOT_PARSEABLE, "plant source uses dict unpacking")
            pairs.append((key, value))
        return {_const_eval(key): _const_eval(value) for key, value in pairs}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand)
    raise _not_a_constant(node)

def _not_a_constant(node: ast.AST) -> ObsRefusal:
    return ObsRefusal(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"plant source is not a constant ({type(node).__name__})",
    )

def _assigned_name(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    if (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
    ):
        return node.target.id, node.value
    return None

def _require_text(value: Any, where: str, code: str, *, strip: bool = True) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ObsRefusal(code, f"{where} must be a non-empty string")
    if strip and value != value.strip():
        raise ObsRefusal(code, f"{where} must be a stripped string")
    return value

def _require_int(value: Any, where: str, code: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ObsRefusal(code, f"{where} must be an int >= {minimum}")
    return value

# r401 ``_kind_bits`` rows as ``str.format`` templates, one per kind, in ``_KIND_BIT_KEYS``
# order. Fields: ``svc``, ``lsvc``, ``fail_val``, ``ns`` (the service's first ``-`` part) and
# ``svc6`` (its first six characters); literal braces are doubled. An unknown kind reads as ``am``.
_KIND_TEMPLATES: dict[str, tuple[str, ...]] = {
    "tempo": (
        '{{resource.service.name="{svc}"}}',
        '{{resource.service.name="{lsvc}"}}',
        "/api/search",
        '{{"traces":[],"error":"max concurrent {fail_val}"}}',
        "tempo empty {fail_val}",
        '{{"traces":[{{"traceID":"r401a"}}]}}',
        '{{"name":"Traces"}}',
        "kubectl -n {ns} logs deploy/{svc} --tail=30 | grep -c otlp",
        "18",
    ),
    "loki": (
        '{{job="{svc}"}}',
        '{{job="{lsvc}"}}',
        "/loki/api/v1/query_range",
        '{{"status":"error","error":"loki {fail_val}"}}',
        "loki {fail_val}",
        '{{"status":"success","data":{{"result":[{{"values":[["1","ok"]]}}]}}}}',
        '{{"name":"Logs"}}',
        "kubectl -n loki logs deploy/ingester --tail=20 | grep -c {svc}",
        "11",
    ),
    "prom": (
        'http_requests_total{{job="{svc}"}}',
        'http_requests_total{{job="{lsvc}"}}',
        PROM_QUERY_PATH,
        '{{"status":"error","error":"prom {fail_val}"}}',
        "prom {fail_val}",
        '{{"status":"success","data":{{"result":[{{"value":[1,"7"]}}]}}}}',
        '{{"name":"Prom"}}',
        "curl -sS $APP/metrics | grep -c {ns}",
        "9",
    ),
    "mimir": (
        'http_requests_total{{service="{svc}"}}',
        'http_requests_total{{service="{lsvc}"}}',
        "/prometheus/api/v1/query",
        '{{"status":"error","error":"mimir {fail_val}"}}',
        "mimir {fail_val}",
        '{{"status":"success","data":{{"result":[{{"value":[1,"6"]}}]}}}}',
        '{{"name":"Mimir"}}',
        "curl -sS $MIMIR/ready | head -1",
        "ready",
    ),
    "otel": (
        '{{resource.service.name="{svc}"}}',
        '{{resource.service.name="{lsvc}"}}',
        "/api/search",
        '{{"traces":[]}}',
        "otel {fail_val}",
        '{{"traces":[{{"traceID":"otel401"}}]}}',
        '{{"name":"OTel"}}',
        "kubectl -n otel logs deploy/otelcol --tail=40 | grep -c {svc}",
        "15",
    ),
    "grafana": (
        '{{resource.service.name="{svc}"}}',
        '{{resource.service.name="{lsvc}"}}',
        "/api/ds/query",
        '{{"message":"grafana {fail_val}"}}',
        "grafana {fail_val}",
        '{{"results":{{"A":{{"frames":[{{"schema":{{"fields":[{{"name":"Time"}}]}}}}]}}}}}}',
        '{{"name":"Panel"}}',
        "curl -sS $GRAFANA/api/dashboards/uid/{svc6} | jq '.dashboard.panels|length'",
        "2",
    ),
    "thanos": (
        'http_requests_total{{job="{svc}"}}',
        'http_requests_total{{job="{lsvc}"}}',
        PROM_QUERY_PATH,
        '{{"status":"error","error":"thanos {fail_val}"}}',
        "thanos {fail_val}",
        '{{"status":"success","data":{{"result":[{{"value":[1,"4"]}}]}}}}',
        '{{"name":"Thanos"}}',
        "curl -sS $THANOS/-/ready",
        "OK",
    ),
    "pyro": (
        'process_cpu{{service_name="{svc}"}}',
        'process_cpu{{service_name="{lsvc}"}}',
        "/pyroscope/render",
        "0",
        "pyro {fail_val}",
        "36",
        '{{"name":"Flame"}}',
        "curl -sS $APP/debug/pprof/profile?seconds=1 | wc -c",
        "4096",
    ),
    "vm": (
        'http_requests_total{{job="{svc}"}}',
        'http_requests_total{{job="{lsvc}"}}',
        PROM_QUERY_PATH,
        '{{"status":"error","error":"vm {fail_val}"}}',
        "vm {fail_val}",
        '{{"status":"success","data":{{"result":[{{"value":[1,"8"]}}]}}}}',
        '{{"name":"VM"}}',
        "curl -sS $VM/health",
        "OK",
    ),
    "ch": (
        _CH_WHERE + "'{svc}'",
        _CH_WHERE + "'{lsvc}'",
        "/",
        "0\n",
        "ch {fail_val}",
        "88\n",
        '{{"name":"SQL"}}',
        "clickhouse-client -q \"" + _CH_WHERE + "'{svc}' SETTINGS max_result_rows=100\"",
        "88",
    ),
    "am": (
        'alerts{{service="{svc}"}}',
        'alerts{{service="{lsvc}"}}',
        "/api/v2/alerts",
        "[]",
        "am {fail_val}",
        '[{{"labels":{{"alertname":"X"}}}}]',
        '{{"name":"AM"}}',
        "curl -sS $AM/-/ready",
        "OK",
    ),
}

def _kind_bits(kind: str, svc: str, lsvc: str, fail_val: str) -> dict[str, str]:
    """Reconstruct r401 ``_kind_bits`` from extracted constants. Never exec."""

    fields = {
        "svc": svc,
        "lsvc": lsvc,
        "fail_val": fail_val,
        "ns": svc.split("-")[0],
        "svc6": svc[:6],
    }
    templates = _KIND_TEMPLATES.get(kind, _KIND_TEMPLATES["am"])
    return {key: text.format(**fields) for key, text in zip(_KIND_BIT_KEYS, templates)}

def _apply_hop_defaults(row: dict[str, Any]) -> dict[str, Any]:
    kind = _require_text(row.get("kind"), "P().kind", FINDING_SOURCE_NOT_PARSEABLE)
    svc = _require_text(row.get("svc"), "P().svc", FINDING_SOURCE_NOT_PARSEABLE)
    lsvc = _require_text(row.get("lsvc"), "P().lsvc", FINDING_SOURCE_NOT_PARSEABLE)
    dash = _require_text(row.get("dash"), "P().dash", FINDING_SOURCE_NOT_PARSEABLE)
    ldash = _require_text(row.get("ldash"), "P().ldash", FINDING_SOURCE_NOT_PARSEABLE)
    out = dict(row)
    out.setdefault("panel", f"{svc.split('-')[0]} {kind}")
    out.setdefault("lpanel", f"{lsvc.split('-')[0]} leftover")
    out.setdefault("file", f"{kind}/{dash}.yaml")
    out.setdefault("lfile", f"{kind}/{ldash}.yaml")
    out.setdefault("false_file", f"{kind}/{dash}.false.yaml")
    out.setdefault("lfalse_file", f"{kind}/{ldash}.false.yaml")
    out.setdefault("novel", 73)
    return out

def _expand_r401(args: list[Any], kind_ns: Mapping[str, Any]) -> dict[str, Any]:
    if len(args) != len(R401_ARG_NAMES):
        raise ObsRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"r401 P() expected {len(R401_ARG_NAMES)} args, got {len(args)}",
        )
    raw = dict(zip(R401_ARG_NAMES, args))
    kind = _require_text(raw.get("kind"), "P().kind", FINDING_SOURCE_NOT_PARSEABLE)
    if kind not in kind_ns:
        raise ObsRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"unknown r401 kind {kind!r}")
    ns, deploy = kind_ns[kind]
    bits = _kind_bits(kind, raw["svc"], raw["lsvc"], raw["fail_val"])
    false_yq = _require_text(raw.get("false_yq"), "P().false_yq", FINDING_SOURCE_NOT_PARSEABLE)
    false_lead = _require_text(
        raw.get("false_lead"), "P().false_lead", FINDING_SOURCE_NOT_PARSEABLE
    )
    expanded = _apply_hop_defaults(
        {
            **raw,
            "ns": ns,
            "deploy": deploy,
            "false_obs": f"{false_yq.split('.')[-1]} healthy  # not the lie",
            "false_read": f"{false_lead} looks healthy",
            "confirm_obs": raw["fail_val"],
            "side_svc": "ssr-meal-svc",
            "side_obs": "1",
            **bits,
        }
    )
    return expanded

def _eval_plant_node(node: ast.AST, kind_ns: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Dict):
        return _const_eval(node)
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return _eval_plant_call(node, node.func.id, kind_ns)
    raise _not_a_constant(node)

def _keyword_values(node: ast.Call) -> dict[str, Any]:
    return {kw.arg: _const_eval(kw.value) for kw in node.keywords if kw.arg}

def _eval_plant_call(node: ast.Call, name: str, kind_ns: Mapping[str, Any]) -> Any:
    """``dict(k=v)``, keyword ``P(...)``/``_P(...)`` with hop defaults, or positional r401 ``P``."""

    if name == "dict" and not node.args:
        return _keyword_values(node)
    if name in {"P", "_P"} and _is_keyword_only_call(node):
        return _apply_hop_defaults(_keyword_values(node))
    if name == "P" and _is_positional_only_call(node):
        return _expand_r401([_const_eval(item) for item in node.args], kind_ns)
    raise _not_a_constant(node)

def _is_keyword_only_call(node: ast.Call) -> bool:
    return bool(node.keywords) and not node.args

def _is_positional_only_call(node: ast.Call) -> bool:
    return bool(node.args) and not node.keywords

def _literal_names(mill_id: str) -> tuple[str, ...]:
    if mill_id == "obs_leftover14":
        return ("L14",)
    if mill_id == "obs_leftover15":
        return ("L15",)
    if mill_id == "obs_leftover16":
        return ("L16",)
    if mill_id.startswith("obs_leftover"):
        return ("SPECS",)
    return ("PAIRS",)

def _source_assignments(tree: ast.AST) -> tuple[dict[str, ast.AST], Any, Mapping[str, Any]]:
    found: dict[str, ast.AST] = {}
    inferred_base: Any = None
    kind_ns: Mapping[str, Any] = DEFAULT_KIND_NS
    for node in tree.body:
        assigned = _assigned_name(node)
        if assigned is None:
            continue
        name, value = assigned
        if name == "CATALOG_FIRST":
            inferred_base = _const_eval(value)
        elif name == "KIND_NS":
            kind_ns = _const_eval(value)
        elif name in {"PAIRS", "SPECS", "L14", "L15", "L16"}:
            found[name] = value
    return found, inferred_base, kind_ns

class _Origin(NamedTuple):
    """Where one source's plant rows come from: mill, source path, and base round."""

    mill_id: str
    source: str
    base_round: int

def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
    shape: str | None = None,
    family: str | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract plant literals from mill source text. Never exec."""

    tree = _parse_source(text, source)
    found, inferred_base, kind_ns = _source_assignments(tree)
    raw_name, raw_node = _plant_literal(found, mill_id, source)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise ObsRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not obs_*")
    base = _base_round(inferred_base if base_round is None else base_round, mill_id, source)
    origin = _Origin(mill_id, source, base)
    resolved_shape = shape or (SHAPE_LEFTOVER_SPEC if raw_name != "PAIRS" else SHAPE_HOP)
    if resolved_shape == SHAPE_LEFTOVER_SPEC:
        spec_family = family or mill_id.removeprefix("obs_")
        return _spec_rows(raw_node.elts, origin, spec_family, kind_ns)
    return _pair_rows(raw_node.elts, origin, resolved_shape, kind_ns)

def _parse_source(text: str, source: str) -> ast.Module:
    try:
        return ast.parse(text)
    except SyntaxError as exc:
        raise ObsRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}"
        ) from exc

def _plant_literal(
    found: Mapping[str, ast.AST], mill_id: str, source: str
) -> tuple[str, ast.List]:
    """The first of the mill's literal names bound in the source, as a non-empty list."""

    wanted = _literal_names(mill_id)
    raw_name = next((name for name in wanted if name in found), None)
    if raw_name is None:
        raise ObsRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no plant literal")
    raw_node = found[raw_name]
    if not isinstance(raw_node, ast.List) or not raw_node.elts:
        raise ObsRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} plant literal is empty")
    return raw_name, raw_node

def _base_round(base: Any, mill_id: str, source: str) -> int:
    """The given round, else the digits of the mill id, else 1; an int of at least 1."""

    if base is None:
        digits = "".join(ch for ch in mill_id if ch.isdigit())
        base = int(digits) if digits else 1
    return _require_int(base, f"{source} BASE", FINDING_PLANT_FIELD_INVALID, 1)

def _spec_rows(
    nodes: list[ast.expr], origin: _Origin, family: str, kind_ns: Mapping[str, Any]
) -> tuple[dict[str, Any], ...]:
    return tuple(
        _spec_from_raw(_eval_plant_node(node, kind_ns), origin, index, family)
        for index, node in enumerate(nodes)
    )

def _pair_rows(
    nodes: list[ast.expr], origin: _Origin, shape: str, kind_ns: Mapping[str, Any]
) -> tuple[dict[str, Any], ...]:
    return tuple(
        _pair_from_raw(_eval_plant_node(node, kind_ns), origin, index, shape)
        for index, node in enumerate(nodes)
    )

def _with_raw_keys(row: dict[str, Any], raw: Mapping[str, Any]) -> dict[str, Any]:
    """The identity row, then every raw key it does not already carry, in raw order."""

    for key, value in raw.items():
        if key not in row:
            row[key] = value
    return row

def _raw_object(raw: Any, where: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ObsRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} is not an object")
    return raw

def _refuse_missing(row: Mapping[str, Any], required: tuple[str, ...], where: str) -> None:
    missing = [key for key in required if key not in row]
    if missing:
        raise ObsRefusal(FINDING_PLANT_FIELD_MISSING, f"{where} missing {missing[0]}")

def _raw_slug(raw: Mapping[str, Any], where: str, key: str, noun: str) -> str:
    """``raw[key]`` as a stripped slug; ``noun`` names what it must be in the refusal."""

    slug = _require_text(raw.get(key), f"{where}.{key}", FINDING_PLANT_FIELD_MISSING)
    if not SLUG_RE.fullmatch(slug):
        raise ObsRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.{key} is not {noun}")
    return slug

def _pair_from_raw(raw: Any, origin: _Origin, index: int, shape: str) -> dict[str, Any]:
    where = f"{origin.source}[{index}]"
    checked = _raw_object(raw, where)
    _refuse_missing(checked, HOP_REQUIRED, where)
    slug = _raw_slug(checked, where, "slug", "a plant slug")
    row = {
        "base_round": origin.base_round,
        "mill_id": origin.mill_id,
        "plant_id": f"{origin.mill_id}:{slug}",
        "shape": shape,
        "slug": slug,
        "source": origin.source,
    }
    return _with_raw_keys(row, checked)

def _spec_mapping(raw: Any, where: str) -> Any:
    """A positional spec tuple as its keyed mapping; anything else unchanged."""

    if not isinstance(raw, tuple):
        return raw
    if len(raw) != len(SPEC_TUPLE_KEYS):
        raise ObsRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{where} is not a {len(SPEC_TUPLE_KEYS)}-tuple",
        )
    return dict(zip(SPEC_TUPLE_KEYS, raw))

def _spec_from_raw(raw: Any, origin: _Origin, index: int, family: str) -> dict[str, Any]:
    where = f"{origin.source}[{index}]"
    checked = _raw_object(_spec_mapping(raw, where), where)
    _refuse_missing(checked, SPEC_REQUIRED, where)
    slug = _raw_slug(checked, where, "ok_slug", "a slug")
    row = {
        "base_round": origin.base_round,
        "family": family,
        "mill_id": origin.mill_id,
        "plant_id": f"{origin.mill_id}:{slug}",
        "shape": SHAPE_LEFTOVER_SPEC,
        "slug": slug,
        "source": origin.source,
    }
    return _with_raw_keys(row, checked)

def _field(mapping: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
    if not isinstance(mapping, dict):
        raise ObsRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where} must be an object")
    if key not in mapping:
        raise ObsRefusal(FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    value = mapping[key]
    if isinstance(value, bool) and kinds is not bool:
        raise ObsRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    if not isinstance(value, kinds):
        raise ObsRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    return value

def _required_shape_keys(shape: str, where: str) -> tuple[str, ...]:
    if shape in {SHAPE_HOP, SHAPE_LEFTOVER3}:
        return HOP_REQUIRED
    if shape == SHAPE_LEFTOVER_SPEC:
        return SPEC_REQUIRED
    raise ObsRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.shape is not a reviewed shape")

def _refuse_missing_shape_keys(row: Mapping[str, Any], shape: str, where: str) -> None:
    _refuse_missing(row, _required_shape_keys(shape, where), where)

def _plant_from_row(row: Any, where: str) -> Plant:
    if not isinstance(row, dict):
        raise ObsRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_PLANT_FIELD_INVALID)
    slug = _require_text(row.get("slug"), f"{where}.slug", FINDING_PLANT_FIELD_INVALID)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise ObsRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.mill_id is not obs_*")
    if not SLUG_RE.fullmatch(slug):
        raise ObsRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.slug is not a plant slug")
    plant_id = _require_text(row.get("plant_id"), f"{where}.plant_id", FINDING_PLANT_FIELD_INVALID)
    expected = f"{mill_id}:{slug}"
    if plant_id != expected:
        raise ObsRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.plant_id must be {expected!r}")
    base_round = _require_int(
        row.get("base_round"), f"{where}.base_round", FINDING_PLANT_FIELD_INVALID, 1
    )
    shape = _require_text(row.get("shape"), f"{where}.shape", FINDING_PLANT_FIELD_INVALID)
    source = _require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING)
    _refuse_missing_shape_keys(row, shape, where)
    payload = dict(row.items())
    return Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=source,
        base_round=base_round,
        shape=shape,
        slug=slug,
        payload=payload,
    )

def _mill_from_row(row: Any, where: str) -> Mill:
    mill_id = _require_text(
        _field(row, "mill_id", str, where), f"{where}.mill_id", FINDING_CATALOG_FIELD_INVALID
    )
    if not MILL_ID_RE.fullmatch(mill_id):
        raise ObsRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.mill_id is not obs_*")
    base_round = _field(row, "base_round", int, where)
    if isinstance(base_round, bool) or base_round < 1:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{where}.base_round must be a positive int"
        )
    plant_count = _field(row, "plant_count", int, where)
    if isinstance(plant_count, bool) or plant_count < 1:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{where}.plant_count must be a positive int"
        )
    return Mill(
        mill_id=mill_id,
        base_round=base_round,
        source=_require_text(
            _field(row, "source", str, where), f"{where}.source", FINDING_CATALOG_FIELD_INVALID
        ),
        plant_count=plant_count,
        shape=_require_text(
            _field(row, "shape", str, where), f"{where}.shape", FINDING_CATALOG_FIELD_INVALID
        ),
    )

def _leftover_spec_index(rows: tuple[Any, ...]) -> Mapping[str, Any] | None:
    if (
        len(rows) == 1
        and isinstance(rows[0], dict)
        and rows[0].get("kind") == SPEC_INDEX_KIND
    ):
        return rows[0]
    return None

def _read_jsonl(payload: bytes, filename: str) -> tuple[Any, ...]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ObsRefusal(FINDING_CATALOG_FIELD_INVALID, f"{filename} is not valid UTF-8") from exc
    if not text.endswith("\n") or "\r" in text:
        raise ObsRefusal(FINDING_CATALOG_FIELD_INVALID, f"{filename} must be LF-framed jsonl")
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise ObsRefusal(FINDING_CATALOG_FIELD_INVALID, f"{filename}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError as exc:
            raise ObsRefusal(FINDING_CATALOG_FIELD_INVALID, f"{filename}:{index} is not strict JSON") from exc
    return tuple(rows)

def _registry_factory_ids() -> set[str]:
    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        payload = load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ObsRefusal(
            FINDING_FACTORY_NOT_REGISTERED, f"factory registry is unreadable: {exc}"
        ) from exc
    factories = payload.get("factories") if isinstance(payload, dict) else None
    if not isinstance(factories, list):
        raise ObsRefusal(FINDING_FACTORY_NOT_REGISTERED, "factory registry factories is not a list")
    found: list[str] = []
    for row in factories:
        path_id = row.get("path_id") if isinstance(row, dict) else None
        if isinstance(path_id, str):
            found.append(path_id)
    return set(found)

def _load_member_rows(
    catalog_dir: Path, files: Mapping[str, Any], digests: Mapping[str, Any]
) -> tuple[list[Any], Mapping[str, Any] | None]:
    members = (
        (HOP_FILENAME, "hop_plants_sha256", "hop_plants"),
        (LEFTOVER3_FILENAME, "leftover3_pairs_sha256", "leftover3_pairs"),
        (LEFTOVER_SPECS_FILENAME, "leftover_specs_sha256", "leftover_specs"),
    )
    rows: list[Any] = []
    spec_index: Mapping[str, Any] | None = None
    for filename, digest_key, file_key in members:
        expected_name = _field(files, file_key, str, f"{CATALOG_FILENAME}.files")
        if expected_name != filename:
            raise ObsRefusal(
                FINDING_CATALOG_FIELD_INVALID,
                f"{CATALOG_FILENAME}.files.{file_key} must be {filename}",
            )
        path = catalog_dir / filename
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise ObsRefusal(FINDING_CATALOG_FILE_MISSING, f"{path} is missing") from exc
        digest = sha256_bytes(payload)
        pinned = _field(digests, digest_key, str, f"{CATALOG_FILENAME}.digests")
        if digest != pinned:
            raise ObsRefusal(
                FINDING_CATALOG_SHA256_MISMATCH,
                f"{filename} digest {digest} != catalog pin {pinned}",
            )
        member_rows = _read_jsonl(payload, filename)
        if filename == LEFTOVER_SPECS_FILENAME:
            spec_index = _leftover_spec_index(member_rows)
            if spec_index is not None:
                continue
        rows.extend(member_rows)
    return rows, spec_index

def _refuse_spec_index_count(meta: Mapping[str, Any], spec_index: Mapping[str, Any] | None) -> None:
    if spec_index is None:
        return
    pair_counts = _field(meta, "pair_counts", dict, CATALOG_FILENAME)
    leftover_specs = _field(pair_counts, "leftover_specs", int, f"{CATALOG_FILENAME}.pair_counts")
    total = _field(spec_index, "total", int, f"{LEFTOVER_SPECS_FILENAME}.total")
    if leftover_specs != total:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.pair_counts.leftover_specs is {leftover_specs}, "
            f"index total is {total}",
        )

def _refuse_duplicate_plants(plants: tuple[Plant, ...]) -> None:
    seen: set[str] = set()
    for plant in plants:
        if plant.plant_id in seen:
            raise ObsRefusal(FINDING_PLANT_DUPLICATE_ID, f"duplicate plant_id {plant.plant_id}")
        seen.add(plant.plant_id)

def _refuse_count(mill: Mill, actual: int) -> None:
    if actual != mill.plant_count:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{mill.mill_id} plant_count {mill.plant_count} != {actual}",
        )

def _plants_per_mill(plants: tuple[Plant, ...]) -> dict[str, int]:
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    return by_mill

def _indexed_spec_mills(
    spec_index: Mapping[str, Any], spec_mill_ids: set[str]
) -> dict[str, Any]:
    """The leftover-spec index rows by mill id; they must name exactly the spec mills."""

    indexed_rows = _field(spec_index, "mills", list, f"{LEFTOVER_SPECS_FILENAME}.mills")
    indexed = {
        _require_text(
            _field(row, "mill_id", str, f"{LEFTOVER_SPECS_FILENAME}.mills"),
            f"{LEFTOVER_SPECS_FILENAME}.mills.mill_id",
            FINDING_CATALOG_FIELD_INVALID,
        ): row
        for row in indexed_rows
    }
    if set(indexed) != spec_mill_ids:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            "leftover-spec index mills do not match catalog leftover_spec mills",
        )
    return indexed

def _refuse_spec_pin(mill: Mill, pin: Any) -> None:
    count = _field(pin, "count", int, f"{LEFTOVER_SPECS_FILENAME}.mills")
    first = _require_text(
        _field(pin, "first", str, f"{LEFTOVER_SPECS_FILENAME}.mills"),
        f"{LEFTOVER_SPECS_FILENAME}.mills.first",
        FINDING_CATALOG_FIELD_INVALID,
    )
    last = _require_text(
        _field(pin, "last", str, f"{LEFTOVER_SPECS_FILENAME}.mills"),
        f"{LEFTOVER_SPECS_FILENAME}.mills.last",
        FINDING_CATALOG_FIELD_INVALID,
    )
    if count != mill.plant_count or not first or not last:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{mill.mill_id} leftover-spec index does not match mill pin",
        )

def _refuse_mill_pins(
    mills: tuple[Mill, ...],
    plants: tuple[Plant, ...],
    spec_index: Mapping[str, Any] | None,
) -> None:
    by_mill = _plants_per_mill(plants)
    mill_ids = {mill.mill_id for mill in mills}
    spec_mill_ids = {mill.mill_id for mill in mills if mill.shape == SHAPE_LEFTOVER_SPEC}
    expected = mill_ids if spec_index is None else mill_ids - spec_mill_ids
    if expected != set(by_mill):
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID, "catalog mills do not match plant mill_id values"
        )
    indexed = None if spec_index is None else _indexed_spec_mills(spec_index, spec_mill_ids)
    for mill in mills:
        _refuse_mill_pin(mill, by_mill, indexed)

def _refuse_mill_pin(
    mill: Mill, by_mill: Mapping[str, int], indexed: Mapping[str, Any] | None
) -> None:
    """A spec mill (when indexed) matches its index pin; any other mill its plant count."""

    if indexed is None or mill.shape != SHAPE_LEFTOVER_SPEC:
        _refuse_count(mill, by_mill[mill.mill_id])
    else:
        _refuse_spec_pin(mill, indexed[mill.mill_id])

def load_catalog(directory: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    catalog_dir = Path(default_catalog_dir() if directory is None else directory)
    meta_path = catalog_dir / CATALOG_FILENAME
    try:
        meta_text = meta_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ObsRefusal(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing") from exc
    try:
        meta = load_strict_json(meta_text)
    except ValueError as exc:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON"
        ) from exc
    catalog_id, factory = _header_identity(meta)
    return _catalog_from_members(catalog_dir, meta, catalog_id, factory)

def _header_identity(meta: Any) -> tuple[str, str]:
    """``catalog_id`` and ``factory`` once every pinned header field holds."""

    catalog_id = _require_text(
        _field(meta, "catalog_id", str, CATALOG_FILENAME),
        f"{CATALOG_FILENAME}.catalog_id",
        FINDING_CATALOG_FIELD_INVALID,
    )
    fmt = _field(meta, "format", str, CATALOG_FILENAME)
    if fmt != CATALOG_FORMAT:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.format must be {CATALOG_FORMAT}",
        )
    factory = _field(meta, "factory", str, CATALOG_FILENAME)
    if factory != FACTORY:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME}.factory must be {FACTORY}"
        )
    prefix = _field(meta, "mill_prefix", str, CATALOG_FILENAME)
    if prefix != MILL_PREFIX:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.mill_prefix must be {MILL_PREFIX}",
        )
    kind = _field(meta, "record_kind", str, CATALOG_FILENAME)
    if kind != RECORD_KIND:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.record_kind must be {RECORD_KIND}",
        )
    quota = _field(meta, "quota_per_round", int, CATALOG_FILENAME)
    if isinstance(quota, bool) or quota != QUOTA_PER_ROUND:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.quota_per_round must be {QUOTA_PER_ROUND}",
        )
    return catalog_id, factory

def _catalog_from_members(
    catalog_dir: Path, meta: Any, catalog_id: str, factory: str
) -> Catalog:
    """Load the member files and bind every plant to its mill pin."""

    plant_count = _field(meta, "plant_count", int, CATALOG_FILENAME)
    mill_rows = _field(meta, "mills", list, CATALOG_FILENAME)
    mills = tuple(
        _mill_from_row(row, f"{CATALOG_FILENAME}.mills[{i}]") for i, row in enumerate(mill_rows)
    )
    files = _field(meta, "files", dict, CATALOG_FILENAME)
    digests = _field(meta, "digests", dict, CATALOG_FILENAME)
    rows, spec_index = _load_member_rows(catalog_dir, files, digests)
    if factory not in _registry_factory_ids():
        raise ObsRefusal(FINDING_FACTORY_NOT_REGISTERED, f"{factory} is not a registry path_id")
    _refuse_spec_index_count(meta, spec_index)
    if len(rows) != plant_count:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.plant_count is {plant_count}, files have {len(rows)}",
        )
    plants = tuple(_plant_from_row(row, f"plants:{i}") for i, row in enumerate(rows, start=1))
    _refuse_duplicate_plants(plants)
    _refuse_mill_pins(mills, plants, spec_index)
    return Catalog(
        catalog_id=catalog_id,
        directory=catalog_dir,
        factory=factory,
        plants=plants,
        mills=mills,
        meta=meta,
        leftover_spec_index=spec_index,
    )

def catalog_check(directory: Path | None = None) -> list[dict[str, str]]:
    """Load the catalog. An invalid catalog is a refusal, not a finding list."""
    load_catalog(directory)
    return []

bind_import_twin(__name__)
