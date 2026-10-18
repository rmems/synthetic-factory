#!/usr/bin/env python3
"""Engine-specific SQL spelling for the db mill (AST-extracted, cleaned)."""

from __future__ import annotations

from . import config as cfg
from .import_twins import bind_import_twin
from .plant import Plant

__all__ = ["default_lock_fail", "engine_cmd", "expand_sql", "lock_sql", "seed_cmd_for"]


# Engine spellings, one template per engine. ``_engine_template`` refuses an
# engine missing from a table with the same ValueError every builder raises.
_ENGINE_CLI = {
    "mysql": 'mysql --batch -N -e "{sql}"',
    "mariadb": 'mariadb --batch -N -e "{sql}"',
    "sqlite": 'sqlite3 {db} "{sql}"',
    "mssql": 'sqlcmd -b -I -Q "{sql}"',
    "oracle": 'echo "{sql};" | sqlplus -L -S app/app',
    "crdb": 'cockroach sql --insecure -e "{sql}"',
}
_ADD_COLUMN = "ALTER TABLE {table} ADD COLUMN {col_v2} {col_type}"
_EXPAND_SQL = {
    "mssql": "ALTER TABLE {table} ADD {col_v2} {col_type} NULL",
    "oracle": "ALTER TABLE {table} ADD ({col_v2} {col_type})",
    "sqlite": _ADD_COLUMN,
    "mysql": _ADD_COLUMN,
    "mariadb": _ADD_COLUMN,
    "crdb": _ADD_COLUMN,
}
_LOCK_SQL = {
    "mysql": "SET lock_wait_timeout=8; " + _ADD_COLUMN,
    "mariadb": "SET lock_wait_timeout=8; " + _ADD_COLUMN,
    "sqlite": "PRAGMA busy_timeout=8000; " + _ADD_COLUMN,
    "mssql": "SET LOCK_TIMEOUT 8000; ALTER TABLE {table} ADD {col_v2} {col_type} NULL",
    "oracle": (
        "ALTER SESSION SET DDL_LOCK_TIMEOUT=8; ALTER TABLE {table} ADD ({col_v2} {col_type})"
    ),
    "crdb": (
        "SET lock_timeout = '8s'; "
        "ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_v2} {col_type}"
    ),
}
_LOCK_FAIL = {
    "mysql": "ERROR 1205 (HY000): Lock wait timeout exceeded ADD {col_v2} on {table}",
    "mariadb": "ERROR 1205 (HY000): Lock wait timeout exceeded ADD {col_v2} on {table}",
    "sqlite": "Error: database is locked ADD {col_v2} on {table}",
    "mssql": "Msg 1222: Lock request time out period exceeded ADD {col_v2} on {table}",
    "oracle": "ORA-00054: resource busy and acquire with NOWAIT specified ADD {col_v2} on {table}",
    "crdb": "pq: lock timeout ADD {col_v2} on {table}",
}


def _engine_template(templates: dict[str, str], engine: str) -> str:
    if engine not in templates:
        raise ValueError(f"unknown engine {engine!r}")
    return templates[engine]


def seed_cmd_for(p: Plant) -> str:
    """Runnable seed command; online-schema tools run as-is."""
    if p["seed"].startswith(("pt-", "gh-ost")):
        return p["seed"]
    return engine_cmd(p, p["seed"])


def engine_cmd(p: Plant, sql: str) -> str:
    """Wrap ``sql`` in the engine's CLI invocation."""
    engine, db = p["engine"], p.get("db", "app.db")
    return _engine_template(_ENGINE_CLI, engine).format(sql=sql, db=db)


def expand_sql(p: Plant) -> str:
    """Expand-only DDL adding ``col_v2`` while keeping ``col``."""
    engine, table, col_v2, col_type = p["engine"], p["table"], p["col_v2"], p["col_type"]
    template = _engine_template(_EXPAND_SQL, engine)
    return template.format(table=table, col_v2=col_v2, col_type=col_type)


def lock_sql(p: Plant) -> str:
    """The same expand guarded by an 8s lock timeout."""
    engine, table, col_v2, col_type = p["engine"], p["table"], p["col_v2"], p["col_type"]
    template = _engine_template(_LOCK_SQL, engine)
    return template.format(table=table, col_v2=col_v2, col_type=col_type)


def default_lock_fail(p: Plant) -> str:
    """Expected lock-timeout observation, or the plant's override."""
    if p.get("lock_fail"):
        return p["lock_fail"]
    engine, table, col_v2 = p["engine"], p["table"], p["col_v2"]
    return _engine_template(_LOCK_FAIL, engine).format(table=table, col_v2=col_v2)


assert set(cfg.ENGINES) == {"mysql", "sqlite", "mssql", "oracle", "mariadb", "crdb"}

bind_import_twin(__name__)
