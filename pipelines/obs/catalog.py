#!/usr/bin/env python3
"""Pinned OBS plant catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` plus three jsonl members
(hop plants, leftover3 pairs, leftover-spec rows). Load verifies each
digest and every required field before a plant is trusted. Historical
mill scripts are read only as text through :func:`plants_from_source`.
"""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    DEFAULT_CATALOG_ID,
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
    SOURCE_COMMIT,
    SOURCE_METHOD,
    SOURCE_REF,
    bind_import_twin,
    dumps_exact_json,
    load_strict_json,
    repo_root,
)

MILL_ID_RE = re.compile(r"^obs_(?:r[0-9]+|leftover(?:3|[0-9]+))$")
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

SOURCE_ROWS = (
    {
        "mill_id": "obs_r245",
        "base_round": 245,
        "source": "experiments/obs-mill-r245.py",
        "shape": SHAPE_HOP,
    },
    {
        "mill_id": "obs_r293",
        "base_round": 293,
        "source": "experiments/obs-mill-plants-r293.py",
        "shape": SHAPE_HOP,
    },
    {
        "mill_id": "obs_r341",
        "base_round": 341,
        "source": "experiments/obs-mill-plants-r341.py",
        "shape": SHAPE_HOP,
    },
    {
        "mill_id": "obs_r401",
        "base_round": 401,
        "source": "experiments/obs-mill-plants-r401.py",
        "shape": SHAPE_HOP,
    },
    {
        "mill_id": "obs_r385",
        "base_round": 385,
        "source": "experiments/obs_r385_leftover3_mill.py",
        "shape": SHAPE_LEFTOVER3,
    },
    {
        "mill_id": "obs_leftover9",
        "base_round": 964,
        "source": "experiments/_gen_obs_leftover9.py",
        "shape": SHAPE_LEFTOVER_SPEC,
        "family": "leftover9",
    },
    {
        "mill_id": "obs_leftover10",
        "base_round": 1052,
        "source": "experiments/_gen_obs_leftover10.py",
        "shape": SHAPE_LEFTOVER_SPEC,
        "family": "leftover10",
    },
    {
        "mill_id": "obs_leftover14",
        "base_round": 1260,
        "source": "experiments/_gen_obs_leftover14.py",
        "shape": SHAPE_LEFTOVER_SPEC,
        "family": "leftover14",
    },
    {
        "mill_id": "obs_leftover15",
        "base_round": 1348,
        "source": "experiments/_gen_obs_leftover14.py",
        "shape": SHAPE_LEFTOVER_SPEC,
        "family": "leftover15",
    },
    {
        "mill_id": "obs_leftover16",
        "base_round": 1436,
        "source": "experiments/_gen_obs_leftover16.py",
        "shape": SHAPE_LEFTOVER_SPEC,
        "family": "leftover16",
    },
)

__all__ = [
    "Catalog",
    "Mill",
    "Plant",
    "SOURCE_ROWS",
    "catalog_check",
    "default_catalog_dir",
    "git_show_source",
    "load_catalog",
    "plants_from_source",
    "sha256_bytes",
    "write_catalog_dir",
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


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def git_show_source(path: str, commit: str = SOURCE_COMMIT) -> str:
    """Read mill source as text. Never import or exec the script."""

    proc = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise ObsRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"git show {commit}:{path} failed: {proc.stderr.strip() or proc.returncode}",
        )
    return proc.stdout


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
    if isinstance(node, ast.Dict):
        if any(key is None for key in node.keys):
            raise ObsRefusal(FINDING_SOURCE_NOT_PARSEABLE, "plant source uses dict unpacking")
        return {_const_eval(key): _const_eval(value) for key, value in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand)
    raise ObsRefusal(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"plant source is not a constant ({type(node).__name__})",
    )


def _assigned_name(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        if node.value is not None:
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


def _kind_bits(kind: str, svc: str, lsvc: str, fail_val: str) -> dict[str, str]:
    """Reconstruct r401 ``_kind_bits`` from extracted constants. Never exec."""

    if kind == "tempo":
        return {
            "query": f'{{resource.service.name="{svc}"}}',
            "lquery": f'{{resource.service.name="{lsvc}"}}',
            "exec_path": "/api/search",
            "exec_obs": f'{{"traces":[],"error":"max concurrent {fail_val}"}}',
            "exec_err": f"tempo empty {fail_val}",
            "exec_ok": '{"traces":[{"traceID":"r401a"}]}',
            "grafana_obs": '{"name":"Traces"}',
            "truth_cmd": (
                f"kubectl -n {svc.split('-')[0]} logs deploy/{svc} --tail=30 | grep -c otlp"
            ),
            "truth_obs": "18",
        }
    if kind == "loki":
        return {
            "query": f'{{job="{svc}"}}',
            "lquery": f'{{job="{lsvc}"}}',
            "exec_path": "/loki/api/v1/query_range",
            "exec_obs": f'{{"status":"error","error":"loki {fail_val}"}}',
            "exec_err": f"loki {fail_val}",
            "exec_ok": '{"status":"success","data":{"result":[{"values":[["1","ok"]]}]}}',
            "grafana_obs": '{"name":"Logs"}',
            "truth_cmd": f"kubectl -n loki logs deploy/ingester --tail=20 | grep -c {svc}",
            "truth_obs": "11",
        }
    if kind == "prom":
        return {
            "query": f'http_requests_total{{job="{svc}"}}',
            "lquery": f'http_requests_total{{job="{lsvc}"}}',
            "exec_path": "/api/v1/query",
            "exec_obs": f'{{"status":"error","error":"prom {fail_val}"}}',
            "exec_err": f"prom {fail_val}",
            "exec_ok": '{"status":"success","data":{"result":[{"value":[1,"7"]}]}}',
            "grafana_obs": '{"name":"Prom"}',
            "truth_cmd": f"curl -sS $APP/metrics | grep -c {svc.split('-')[0]}",
            "truth_obs": "9",
        }
    if kind == "mimir":
        return {
            "query": f'http_requests_total{{service="{svc}"}}',
            "lquery": f'http_requests_total{{service="{lsvc}"}}',
            "exec_path": "/prometheus/api/v1/query",
            "exec_obs": f'{{"status":"error","error":"mimir {fail_val}"}}',
            "exec_err": f"mimir {fail_val}",
            "exec_ok": '{"status":"success","data":{"result":[{"value":[1,"6"]}]}}',
            "grafana_obs": '{"name":"Mimir"}',
            "truth_cmd": "curl -sS $MIMIR/ready | head -1",
            "truth_obs": "ready",
        }
    if kind == "otel":
        return {
            "query": f'{{resource.service.name="{svc}"}}',
            "lquery": f'{{resource.service.name="{lsvc}"}}',
            "exec_path": "/api/search",
            "exec_obs": '{"traces":[]}',
            "exec_err": f"otel {fail_val}",
            "exec_ok": '{"traces":[{"traceID":"otel401"}]}',
            "grafana_obs": '{"name":"OTel"}',
            "truth_cmd": f"kubectl -n otel logs deploy/otelcol --tail=40 | grep -c {svc}",
            "truth_obs": "15",
        }
    if kind == "grafana":
        return {
            "query": f'{{resource.service.name="{svc}"}}',
            "lquery": f'{{resource.service.name="{lsvc}"}}',
            "exec_path": "/api/ds/query",
            "exec_obs": f'{{"message":"grafana {fail_val}"}}',
            "exec_err": f"grafana {fail_val}",
            "exec_ok": '{"results":{"A":{"frames":[{"schema":{"fields":[{"name":"Time"}]}}]}}}',
            "grafana_obs": '{"name":"Panel"}',
            "truth_cmd": (
                f"curl -sS $GRAFANA/api/dashboards/uid/{svc[:6]} | jq '.dashboard.panels|length'"
            ),
            "truth_obs": "2",
        }
    if kind == "thanos":
        return {
            "query": f'http_requests_total{{job="{svc}"}}',
            "lquery": f'http_requests_total{{job="{lsvc}"}}',
            "exec_path": "/api/v1/query",
            "exec_obs": f'{{"status":"error","error":"thanos {fail_val}"}}',
            "exec_err": f"thanos {fail_val}",
            "exec_ok": '{"status":"success","data":{"result":[{"value":[1,"4"]}]}}',
            "grafana_obs": '{"name":"Thanos"}',
            "truth_cmd": "curl -sS $THANOS/-/ready",
            "truth_obs": "OK",
        }
    if kind == "pyro":
        return {
            "query": f'process_cpu{{service_name="{svc}"}}',
            "lquery": f'process_cpu{{service_name="{lsvc}"}}',
            "exec_path": "/pyroscope/render",
            "exec_obs": "0",
            "exec_err": f"pyro {fail_val}",
            "exec_ok": "36",
            "grafana_obs": '{"name":"Flame"}',
            "truth_cmd": "curl -sS $APP/debug/pprof/profile?seconds=1 | wc -c",
            "truth_obs": "4096",
        }
    if kind == "vm":
        return {
            "query": f'http_requests_total{{job="{svc}"}}',
            "lquery": f'http_requests_total{{job="{lsvc}"}}',
            "exec_path": "/api/v1/query",
            "exec_obs": f'{{"status":"error","error":"vm {fail_val}"}}',
            "exec_err": f"vm {fail_val}",
            "exec_ok": '{"status":"success","data":{"result":[{"value":[1,"8"]}]}}',
            "grafana_obs": '{"name":"VM"}',
            "truth_cmd": "curl -sS $VM/health",
            "truth_obs": "OK",
        }
    if kind == "ch":
        return {
            "query": f"SELECT count() FROM otel.traces WHERE service='{svc}'",
            "lquery": f"SELECT count() FROM otel.traces WHERE service='{lsvc}'",
            "exec_path": "/",
            "exec_obs": "0\n",
            "exec_err": f"ch {fail_val}",
            "exec_ok": "88\n",
            "grafana_obs": '{"name":"SQL"}',
            "truth_cmd": (
                "clickhouse-client -q \"SELECT count() FROM otel.traces "
                f"WHERE service='{svc}' SETTINGS max_result_rows=100\""
            ),
            "truth_obs": "88",
        }
    return {
        "query": f'alerts{{service="{svc}"}}',
        "lquery": f'alerts{{service="{lsvc}"}}',
        "exec_path": "/api/v2/alerts",
        "exec_obs": "[]",
        "exec_err": f"am {fail_val}",
        "exec_ok": '[{"labels":{"alertname":"X"}}]',
        "grafana_obs": '{"name":"AM"}',
        "truth_cmd": "curl -sS $AM/-/ready",
        "truth_obs": "OK",
    }


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
        name = node.func.id
        if name == "dict" and not node.args:
            return {kw.arg: _const_eval(kw.value) for kw in node.keywords if kw.arg}
        if name in {"P", "_P"} and node.keywords and not node.args:
            raw = {kw.arg: _const_eval(kw.value) for kw in node.keywords if kw.arg}
            return _apply_hop_defaults(raw)
        if name == "P" and node.args and not node.keywords:
            return _expand_r401([_const_eval(item) for item in node.args], kind_ns)
    raise ObsRefusal(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"plant source is not a constant ({type(node).__name__})",
    )


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

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise ObsRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}"
        ) from exc
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
    wanted = _literal_names(mill_id)
    raw_name = next((name for name in wanted if name in found), None)
    if raw_name is None:
        raise ObsRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no plant literal")
    raw_node = found[raw_name]
    if not isinstance(raw_node, ast.List) or not raw_node.elts:
        raise ObsRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} plant literal is empty")
    if not MILL_ID_RE.fullmatch(mill_id):
        raise ObsRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not obs_*")
    base = inferred_base if base_round is None else base_round
    if base is None:
        digits = "".join(ch for ch in mill_id if ch.isdigit())
        base = int(digits) if digits else 1
    base = _require_int(base, f"{source} BASE", FINDING_PLANT_FIELD_INVALID, 1)
    resolved_shape = shape or (SHAPE_LEFTOVER_SPEC if raw_name != "PAIRS" else SHAPE_HOP)
    rows: list[dict[str, Any]] = []
    for index, node in enumerate(raw_node.elts):
        raw = _eval_plant_node(node, kind_ns)
        if resolved_shape == SHAPE_LEFTOVER_SPEC:
            rows.append(
                _spec_from_raw(
                    raw,
                    mill_id=mill_id,
                    source=source,
                    base_round=base,
                    index=index,
                    family=family or mill_id.removeprefix("obs_"),
                )
            )
        else:
            rows.append(
                _pair_from_raw(
                    raw,
                    mill_id=mill_id,
                    source=source,
                    base_round=base,
                    index=index,
                    shape=resolved_shape,
                )
            )
    return tuple(rows)


def _pair_from_raw(
    raw: Any,
    *,
    mill_id: str,
    source: str,
    base_round: int,
    index: int,
    shape: str,
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ObsRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source}[{index}] is not an object")
    missing = [key for key in HOP_REQUIRED if key not in raw]
    if missing:
        raise ObsRefusal(FINDING_PLANT_FIELD_MISSING, f"{source}[{index}] missing {missing[0]}")
    slug = _require_text(raw.get("slug"), f"{source}[{index}].slug", FINDING_PLANT_FIELD_MISSING)
    if not SLUG_RE.fullmatch(slug):
        raise ObsRefusal(FINDING_PLANT_FIELD_INVALID, f"{source}[{index}].slug is not a plant slug")
    row = {
        "base_round": base_round,
        "mill_id": mill_id,
        "plant_id": f"{mill_id}:{slug}",
        "shape": shape,
        "slug": slug,
        "source": source,
    }
    for key, value in raw.items():
        if key not in row:
            row[key] = value
    return row


def _spec_from_raw(
    raw: Any,
    *,
    mill_id: str,
    source: str,
    base_round: int,
    index: int,
    family: str,
) -> dict[str, Any]:
    if isinstance(raw, tuple):
        if len(raw) != len(SPEC_TUPLE_KEYS):
            raise ObsRefusal(
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{source}[{index}] is not a {len(SPEC_TUPLE_KEYS)}-tuple",
            )
        raw = dict(zip(SPEC_TUPLE_KEYS, raw))
    if not isinstance(raw, dict):
        raise ObsRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source}[{index}] is not an object")
    missing = [key for key in SPEC_REQUIRED if key not in raw]
    if missing:
        raise ObsRefusal(FINDING_PLANT_FIELD_MISSING, f"{source}[{index}] missing {missing[0]}")
    slug = _require_text(
        raw.get("ok_slug"), f"{source}[{index}].ok_slug", FINDING_PLANT_FIELD_MISSING
    )
    if not SLUG_RE.fullmatch(slug):
        raise ObsRefusal(FINDING_PLANT_FIELD_INVALID, f"{source}[{index}].ok_slug is not a slug")
    row = {
        "base_round": base_round,
        "family": family,
        "mill_id": mill_id,
        "plant_id": f"{mill_id}:{slug}",
        "shape": SHAPE_LEFTOVER_SPEC,
        "slug": slug,
        "source": source,
    }
    for key, value in raw.items():
        if key not in row:
            row[key] = value
    return row


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
    if shape in {SHAPE_HOP, SHAPE_LEFTOVER3}:
        missing = [key for key in HOP_REQUIRED if key not in row]
        if missing:
            raise ObsRefusal(FINDING_PLANT_FIELD_MISSING, f"{where} missing {missing[0]}")
    elif shape == SHAPE_LEFTOVER_SPEC:
        missing = [key for key in SPEC_REQUIRED if key not in row]
        if missing:
            raise ObsRefusal(FINDING_PLANT_FIELD_MISSING, f"{where} missing {missing[0]}")
    else:
        raise ObsRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.shape is not a reviewed shape")
    payload = {key: value for key, value in row.items()}
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


def _read_jsonl(path: Path) -> tuple[Any, ...]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ObsRefusal(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}") from exc
    if not text.endswith("\n") or "\r" in text:
        raise ObsRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name} must be LF-framed jsonl")
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise ObsRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError as exc:
            raise ObsRefusal(
                FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is not strict JSON"
            ) from exc
    return tuple(rows)


def _jsonl_bytes(rows: list[Mapping[str, Any]]) -> bytes:
    lines = [
        dumps_exact_json(dict(row), ensure_ascii=True, sort_keys=True) + "\n" for row in rows
    ]
    return "".join(lines).encode("utf-8")


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
    return {
        row.get("path_id")
        for row in factories
        if isinstance(row, dict) and isinstance(row.get("path_id"), str)
    }


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
    plant_count = _field(meta, "plant_count", int, CATALOG_FILENAME)
    mill_rows = _field(meta, "mills", list, CATALOG_FILENAME)
    mills = tuple(
        _mill_from_row(row, f"{CATALOG_FILENAME}.mills[{i}]") for i, row in enumerate(mill_rows)
    )
    files = _field(meta, "files", dict, CATALOG_FILENAME)
    digests = _field(meta, "digests", dict, CATALOG_FILENAME)
    members = (
        (HOP_FILENAME, "hop_plants_sha256", "hop_plants"),
        (LEFTOVER3_FILENAME, "leftover3_pairs_sha256", "leftover3_pairs"),
        (LEFTOVER_SPECS_FILENAME, "leftover_specs_sha256", "leftover_specs"),
    )
    rows: list[Any] = []
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
        rows.extend(_read_jsonl(path))
    if factory not in _registry_factory_ids():
        raise ObsRefusal(FINDING_FACTORY_NOT_REGISTERED, f"{factory} is not a registry path_id")
    if len(rows) != plant_count:
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.plant_count is {plant_count}, files have {len(rows)}",
        )
    plants = tuple(_plant_from_row(row, f"plants:{i}") for i, row in enumerate(rows, start=1))
    seen: set[str] = set()
    for plant in plants:
        if plant.plant_id in seen:
            raise ObsRefusal(FINDING_PLANT_DUPLICATE_ID, f"duplicate plant_id {plant.plant_id}")
        seen.add(plant.plant_id)
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    mill_ids = {mill.mill_id for mill in mills}
    if mill_ids != set(by_mill):
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID, "catalog mills do not match plant mill_id values"
        )
    for mill in mills:
        if by_mill[mill.mill_id] != mill.plant_count:
            raise ObsRefusal(
                FINDING_CATALOG_FIELD_INVALID,
                f"{mill.mill_id} plant_count {mill.plant_count} != {by_mill[mill.mill_id]}",
            )
    return Catalog(
        catalog_id=catalog_id,
        directory=catalog_dir,
        factory=factory,
        plants=plants,
        mills=mills,
        meta=meta,
    )


def catalog_check(directory: Path | None = None) -> list[dict[str, str]]:
    """Load the catalog. An invalid catalog is a refusal, not a finding list."""

    load_catalog(directory)
    return []


def extract_family(read_source) -> dict[str, Any]:
    """AST-extract every reviewed source through ``read_source(path)``."""

    hop: list[dict[str, Any]] = []
    leftover3: list[dict[str, Any]] = []
    specs: list[dict[str, Any]] = []
    mills: list[dict[str, Any]] = []
    source_pins: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for spec in SOURCE_ROWS:
        path = spec["source"]
        text = read_source(path)
        rows = plants_from_source(
            text,
            mill_id=spec["mill_id"],
            source=path,
            base_round=spec["base_round"],
            shape=spec["shape"],
            family=spec.get("family"),
        )
        if spec["shape"] == SHAPE_HOP:
            hop.extend(rows)
        elif spec["shape"] == SHAPE_LEFTOVER3:
            leftover3.extend(rows)
        else:
            specs.extend(rows)
        mills.append(
            {
                "base_round": spec["base_round"],
                "mill_id": spec["mill_id"],
                "plant_count": len(rows),
                "shape": spec["shape"],
                "source": path,
            }
        )
        if path not in seen_paths:
            seen_paths.add(path)
            source_pins.append(
                {
                    "path": path,
                    "sha256": sha256_text(text),
                }
            )
    return {
        "hop": hop,
        "leftover3": leftover3,
        "leftover_specs": specs,
        "mills": mills,
        "source_pins": source_pins,
    }


def write_catalog_dir(
    directory: Path,
    family: Mapping[str, Any],
    *,
    catalog_id: str = DEFAULT_CATALOG_ID,
) -> dict[str, Any]:
    """Write a brand-new catalog directory. Refuses one that exists."""

    dest = Path(directory)
    if dest.exists():
        raise ObsRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"catalog destination {dest} already exists"
        )
    dest.mkdir(parents=True)
    hop_bytes = _jsonl_bytes(list(family["hop"]))
    leftover3_bytes = _jsonl_bytes(list(family["leftover3"]))
    spec_bytes = _jsonl_bytes(list(family["leftover_specs"]))
    (dest / HOP_FILENAME).write_bytes(hop_bytes)
    (dest / LEFTOVER3_FILENAME).write_bytes(leftover3_bytes)
    (dest / LEFTOVER_SPECS_FILENAME).write_bytes(spec_bytes)
    plant_count = len(family["hop"]) + len(family["leftover3"]) + len(family["leftover_specs"])
    meta = {
        "catalog_id": catalog_id,
        "digests": {
            "hop_plants_sha256": sha256_bytes(hop_bytes),
            "leftover3_pairs_sha256": sha256_bytes(leftover3_bytes),
            "leftover_specs_sha256": sha256_bytes(spec_bytes),
        },
        "factory": FACTORY,
        "files": {
            "hop_plants": HOP_FILENAME,
            "leftover3_pairs": LEFTOVER3_FILENAME,
            "leftover_specs": LEFTOVER_SPECS_FILENAME,
        },
        "format": CATALOG_FORMAT,
        "mill_prefix": MILL_PREFIX,
        "mills": list(family["mills"]),
        "pair_counts": {
            "hop": len(family["hop"]),
            "leftover3": len(family["leftover3"]),
            "leftover_specs": len(family["leftover_specs"]),
        },
        "plant_count": plant_count,
        "quota_per_round": QUOTA_PER_ROUND,
        "record_kind": RECORD_KIND,
        "source": {
            "commit": SOURCE_COMMIT,
            "method": SOURCE_METHOD,
            "ref": SOURCE_REF,
            "scripts": list(family["source_pins"]),
        },
    }
    rendered = dumps_exact_json(meta, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    (dest / CATALOG_FILENAME).write_text(rendered, encoding="utf-8")
    return meta


bind_import_twin(__name__)
