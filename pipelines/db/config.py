#!/usr/bin/env python3
"""Cleaned constants for the db-migration-repair mill (r845+, AST-extracted)."""

from __future__ import annotations

import re

from .import_twins import bind_import_twin

__all__ = [
    "BANNED_FRAGMENTS",
    "BANNED_KEYS",
    "COVERAGE_FLOOR",
    "ENGINES",
    "FACTORY_SLUG",
    "GENERATOR",
    "MAX_ROUNDS",
    "MIN_ROUNDS",
    "RECYCLE_SUFFIX",
    "START_ROUND",
]

FACTORY_SLUG = "db-migration-repair-factory"
GENERATOR = "grok-4.6"
START_ROUND = 845
MIN_ROUNDS = 12
MAX_ROUNDS = 16
COVERAGE_FLOOR = 28
ENGINES = ("mysql", "sqlite", "mssql", "oracle", "mariadb", "crdb")
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
RECYCLE_SUFFIX = re.compile(r"-r\d+$")
BANNED_FRAGMENTS = (
    "concurrent-unique",
    "fk-not-valid",
    "not-valid-fk",
    "generated-set-expression",
    "partition-attach",
    "replica-identity",
    "nulls-not-distinct",
    "spgist",
    "gin-fastupdate",
    "brin-desummarize",
    "hash-index-bucket",
    "tid-range",
    "fillfactor",
    "tablespace-set",
    "amcheck",
    "pgrepack",
    "citus-",
    "django-",
    "alembic-",
    "flyway-",
    "liquibase-",
    "typeorm-",
    "rails-",
    "goose-",
    "dbmate-",
    "prisma-",
    "spanner-",
    "redshift-",
    "alloydb-",
    "ferretdb-",
    "tidb-dxf",
    "bq-continuous",
    "ch-shared",
    "neon-branch",
    "neon-pageserver",
)

bind_import_twin(__name__)
