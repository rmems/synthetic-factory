#!/usr/bin/env python3
"""Engine-specific SQL spelling for the db mill (AST-extracted, cleaned)."""

from __future__ import annotations

from . import config as cfg
from .import_twins import bind_import_twin
from .plant import Plant

__all__ = ["default_lock_fail", "engine_cmd", "expand_sql", "lock_sql", "seed_cmd_for"]


def seed_cmd_for(p: Plant) -> str:
    """Runnable seed command; online-schema tools run as-is."""
    if p["seed"].startswith("pt-") or p["seed"].startswith("gh-ost"):
        return p["seed"]
    return engine_cmd(p, p["seed"])


def engine_cmd(p: Plant, sql: str) -> str:
    """Wrap ``sql`` in the engine's CLI invocation."""
    engine, db = p["engine"], p.get("db", "app.db")
    if engine == "mysql":
        return f'mysql --batch -N -e "{sql}"'
    if engine == "mariadb":
        return f'mariadb --batch -N -e "{sql}"'
    if engine == "sqlite":
        return f'sqlite3 {db} "{sql}"'
    if engine == "mssql":
        return f'sqlcmd -b -I -Q "{sql}"'
    if engine == "oracle":
        return f'echo "{sql};" | sqlplus -L -S app/app'
    if engine == "crdb":
        return f'cockroach sql --insecure -e "{sql}"'
    raise ValueError(f"unknown engine {engine!r}")


def expand_sql(p: Plant) -> str:
    """Expand-only DDL adding ``col_v2`` while keeping ``col``."""
    engine, table, col_v2, col_type = p["engine"], p["table"], p["col_v2"], p["col_type"]
    if engine == "mssql":
        return f"ALTER TABLE {table} ADD {col_v2} {col_type} NULL"
    if engine == "oracle":
        return f"ALTER TABLE {table} ADD ({col_v2} {col_type})"
    if engine == "sqlite":
        return f"ALTER TABLE {table} ADD COLUMN {col_v2} {col_type}"
    if engine in ("mysql", "mariadb", "crdb"):
        return f"ALTER TABLE {table} ADD COLUMN {col_v2} {col_type}"
    raise ValueError(f"unknown engine {engine!r}")


def lock_sql(p: Plant) -> str:
    """The same expand guarded by an 8s lock timeout."""
    engine, table, col_v2, col_type = p["engine"], p["table"], p["col_v2"], p["col_type"]
    if engine in ("mysql", "mariadb"):
        return f"SET lock_wait_timeout=8; ALTER TABLE {table} ADD COLUMN {col_v2} {col_type}"
    if engine == "sqlite":
        return f"PRAGMA busy_timeout=8000; ALTER TABLE {table} ADD COLUMN {col_v2} {col_type}"
    if engine == "mssql":
        return f"SET LOCK_TIMEOUT 8000; ALTER TABLE {table} ADD {col_v2} {col_type} NULL"
    if engine == "oracle":
        return f"ALTER SESSION SET DDL_LOCK_TIMEOUT=8; ALTER TABLE {table} ADD ({col_v2} {col_type})"
    if engine == "crdb":
        return f"SET lock_timeout = '8s'; ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_v2} {col_type}"
    raise ValueError(f"unknown engine {engine!r}")


def default_lock_fail(p: Plant) -> str:
    """Expected lock-timeout observation, or the plant's override."""
    if p.get("lock_fail"):
        return p["lock_fail"]
    engine, table, col_v2 = p["engine"], p["table"], p["col_v2"]
    if engine in ("mysql", "mariadb"):
        return f"ERROR 1205 (HY000): Lock wait timeout exceeded ADD {col_v2} on {table}"
    if engine == "sqlite":
        return f"Error: database is locked ADD {col_v2} on {table}"
    if engine == "mssql":
        return f"Msg 1222: Lock request time out period exceeded ADD {col_v2} on {table}"
    if engine == "oracle":
        return f"ORA-00054: resource busy and acquire with NOWAIT specified ADD {col_v2} on {table}"
    if engine == "crdb":
        return f"pq: lock timeout ADD {col_v2} on {table}"
    raise ValueError(f"unknown engine {engine!r}")


assert set(cfg.ENGINES) == {"mysql", "sqlite", "mssql", "oracle", "mariadb", "crdb"}

bind_import_twin(__name__)
