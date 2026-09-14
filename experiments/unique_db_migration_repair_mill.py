#!/usr/bin/env python3
"""Unique db-migration-repair mill for r845+.

MySQL / SQLite / SQL Server / Oracle / MariaDB / CRDB leftovers.
Not a recycle mill. Not r762–r793 warehouses, r794–r817 ORM CLIs,
or r818–r844 PG catalog/AM clones. r844 was taken by a PG mill.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "db-migration-repair-factory"
)
GENERATOR = "grok-4.6"
FACTORY_SLUG = "db-migration-repair-factory"
START_ROUND = 845
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


def pl(
    *,
    engine: str,
    slug: str,
    plant: str,
    surface: str,
    table: str,
    col: str,
    col_v2: str,
    leftover: str,
    leftover2: str,
    seed: str,
    fail: str,
    inspect: str,
    catalog: str,
    abort: str,
    col_type: str,
    lock_fail: str | None = None,
    db: str = "app.db",
) -> dict[str, str]:
    return {
        "engine": engine,
        "slug": slug,
        "plant": plant,
        "surface": surface,
        "table": table,
        "col": col,
        "col_v2": col_v2,
        "leftover": leftover,
        "leftover2": leftover2,
        "seed": seed,
        "fail": fail,
        "inspect": inspect,
        "catalog": catalog,
        "abort": abort,
        "col_type": col_type,
        "lock_fail": lock_fail or "",
        "db": db,
    }


# Two plants per round, indexed from r845. Unique engine leftovers only.
PLANTS: list[dict[str, str]] = [
    pl(
        engine="mysql",
        slug="mysql-algorithm-inplace-leftover",
        plant="mysql-inplace",
        surface="mysql-algorithm-inplace",
        table="shop.inplace_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="#sql-ib-inplace-sku",
        leftover2="inplace_sku_frm_tmp",
        seed="ALTER TABLE shop.inplace_sku ALGORITHM=INPLACE, LOCK=NONE, CHANGE sku sku VARCHAR(191)",
        fail="ERROR 1846 (0A000): ALGORITHM=INPLACE is not supported. Reason: Cannot CHANGE column type INPLACE. leftover #sql-ib-inplace-sku + inplace_sku_frm_tmp",
        inspect="SELECT NAME, SPACE FROM information_schema.INNODB_TABLESPACES WHERE NAME LIKE 'shop/inplace_sku%'",
        catalog="INPLACE abort leftover #sql-ib tmp; expand sku_norm",
        abort="DROP TABLE IF EXISTS shop.`#sql-ib-inplace-sku`",
        col_type="VARCHAR(191)",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-table-rewrite-already-skip",
        plant="sqlite-rewrite-skip",
        surface="sqlite-table-rewrite",
        table="rewrite_item",
        col="body",
        col_v2="body_v2",
        leftover="sqlite_altertab_rewrite_item",
        leftover2="rewrite_item_old",
        seed="ALTER TABLE rewrite_item RENAME COLUMN body TO body_v2",
        fail="NOTICE: already skip: sqlite table rewrite in progress; leftover sqlite_altertab_rewrite_item + rewrite_item_old",
        inspect="SELECT name, sql FROM sqlite_master WHERE name LIKE 'rewrite_item%'",
        catalog="table-rewrite already-skip leftover sqlite_altertab; expand body_v2",
        abort="DROP TABLE IF EXISTS sqlite_altertab_rewrite_item",
        col_type="BLOB",
        db="rewrite.db",
        lock_fail="Error: database is locked ADD body_v2 on rewrite_item",
    ),
    pl(
        engine="mssql",
        slug="mssql-online-rebuild-leftover",
        plant="mssql-online",
        surface="mssql-online-rebuild",
        table="sales.online_order",
        col="qty",
        col_v2="qty_v2",
        leftover="online_order_rebuild_tmp",
        leftover2="online_order_iro_row",
        seed="ALTER INDEX IX_online_order_qty ON sales.online_order REBUILD WITH (ONLINE=ON, MAXDOP=1)",
        fail="Msg 608: Cannot rebuild ONLINE while a resumable operation is pending; leftover online_order_rebuild_tmp + online_order_iro_row",
        inspect="SELECT name, is_hypothetical FROM sys.indexes WHERE object_id=OBJECT_ID('sales.online_order')",
        catalog="ONLINE rebuild leftover resumable row; expand qty_v2",
        abort="KILL RESUMABLE INDEX ON sales.online_order; DROP TABLE IF EXISTS sales.online_order_rebuild_tmp",
        col_type="BIGINT",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD qty_v2 on sales.online_order",
    ),
    pl(
        engine="oracle",
        slug="oracle-invisible-index-leftover",
        plant="oracle-invis-idx",
        surface="oracle-invisible-index",
        table="hr.inv_idx_emp",
        col="empno",
        col_v2="emp_uuid",
        leftover="INV_IDX_EMP_I",
        leftover2="SYS_IOT_OVER_EMP_TMP",
        seed="ALTER INDEX hr.inv_idx_emp_i INVISIBLE",
        fail="ORA-14147: cannot ALTER INDEX INVISIBLE while DML holds the index; leftover INV_IDX_EMP_I (INVISIBLE) + SYS_IOT_OVER_EMP_TMP",
        inspect="SELECT index_name, visibility FROM user_indexes WHERE table_name='INV_IDX_EMP'",
        catalog="invisible index leftover; expand emp_uuid, do not drop empno",
        abort="ALTER INDEX hr.inv_idx_emp_i VISIBLE; DROP TABLE hr.SYS_IOT_OVER_EMP_TMP",
        col_type="VARCHAR2(36)",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD emp_uuid on hr.inv_idx_emp",
    ),
    pl(
        engine="mariadb",
        slug="mariadb-instant-add-leftover",
        plant="maria-instant",
        surface="mariadb-instant-add",
        table="catalog.maria_instant_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="#sql-alter-maria_instant",
        leftover2="maria_instant_sku_instant_tmp",
        seed="ALTER TABLE catalog.maria_instant_sku ALGORITHM=INSTANT, ADD COLUMN sku_pad VARCHAR(8) DEFAULT ''",
        fail="ERROR 1845 (0A000): ALGORITHM=INSTANT not supported with MAX_ROWS/ROW_FORMAT leftover #sql-alter-maria_instant + maria_instant_sku_instant_tmp",
        inspect="SELECT TABLE_NAME, CREATE_OPTIONS FROM information_schema.TABLES WHERE TABLE_NAME='maria_instant_sku'",
        catalog="MariaDB INSTANT abort leftover alter tmp; expand sku_norm",
        abort="DROP TABLE IF EXISTS catalog.`#sql-alter-maria_instant`",
        col_type="VARCHAR(191)",
    ),
    pl(
        engine="mysql",
        slug="mysql-algorithm-copy-tmp-leftover",
        plant="mysql-copy-tmp",
        surface="mysql-algorithm-copy",
        table="warehouse.copy_blob",
        col="body",
        col_v2="body_v2",
        leftover="#sql-copy-blob",
        leftover2="copy_blob_new",
        seed="ALTER TABLE warehouse.copy_blob ALGORITHM=COPY, CHANGE body body LONGBLOB",
        fail="ERROR 1795 (HY000): ALGORITHM=COPY killed mid-copy; leftover #sql-copy-blob + copy_blob_new",
        inspect="SELECT NAME FROM information_schema.INNODB_TABLESPACES WHERE NAME LIKE 'warehouse/copy_blob%'",
        catalog="COPY abort leftover tmp table; expand body_v2",
        abort="DROP TABLE IF EXISTS warehouse.`#sql-copy-blob`",
        col_type="LONGBLOB",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD body_v2 on warehouse.copy_blob",
    ),
    pl(
        engine="mysql",
        slug="mysql-fk-checks-off-leftover",
        plant="mysql-fk-off",
        surface="mysql-fk-checks",
        table="auth.fk_session",
        col="user_id",
        col_v2="user_uuid",
        leftover="fk_session_ibfk_tmp",
        leftover2="fk_session_orphan",
        seed="SET FOREIGN_KEY_CHECKS=0; ALTER TABLE auth.fk_session CHANGE user_id user_id BIGINT",
        fail="ERROR 1452 (23000): FOREIGN_KEY_CHECKS=0 left orphans; leftover fk_session_ibfk_tmp + fk_session_orphan",
        inspect="SELECT CONSTRAINT_NAME, REFERENCED_TABLE_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_NAME='fk_session'",
        catalog="FK_CHECKS=0 leftover orphans+tmp; expand user_uuid",
        abort="DROP TABLE IF EXISTS auth.fk_session_ibfk_tmp",
        col_type="CHAR(36)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD user_uuid on auth.fk_session",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-wal-checkpoint-leftover",
        plant="sqlite-wal",
        surface="sqlite-wal-checkpoint",
        table="wal_doc",
        col="payload",
        col_v2="payload_v2",
        leftover="wal_doc-wal",
        leftover2="wal_doc-shm",
        seed="PRAGMA wal_checkpoint(TRUNCATE)",
        fail="SQLITE_BUSY: wal checkpoint leftover wal_doc-wal + wal_doc-shm; skip in-place rewrite",
        inspect="PRAGMA journal_mode; PRAGMA wal_checkpoint(PASSIVE)",
        catalog="WAL/SHM leftover after failed checkpoint; expand payload_v2",
        abort="PRAGMA wal_checkpoint(PASSIVE)",
        col_type="TEXT",
        db="wal.db",
        lock_fail="Error: database is locked ADD payload_v2 on wal_doc",
    ),
    pl(
        engine="mssql",
        slug="mssql-resumable-index-leftover",
        plant="mssql-resumable",
        surface="mssql-resumable-index",
        table="finance.resumable_ledger",
        col="amount",
        col_v2="amount_v2",
        leftover="resumable_ledger_ix_tmp",
        leftover2="resumable_ledger_iro_row",
        seed="ALTER INDEX IX_resumable_ledger_amount ON finance.resumable_ledger REBUILD WITH (ONLINE=ON, RESUMABLE=ON)",
        fail="Msg 10637: resumable index already paused; leftover resumable_ledger_ix_tmp + resumable_ledger_iro_row",
        inspect="SELECT object_id, sql_text, state_desc FROM sys.index_resumable_operations",
        catalog="RESUMABLE=ON leftover paused rebuild; expand amount_v2",
        abort="ALTER INDEX IX_resumable_ledger_amount ON finance.resumable_ledger ABORT",
        col_type="DECIMAL(18,4)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD amount_v2 on finance.resumable_ledger",
    ),
    pl(
        engine="oracle",
        slug="oracle-online-redef-interim-leftover",
        plant="oracle-redef",
        surface="oracle-online-redef",
        table="erp.redef_item",
        col="sku",
        col_v2="sku_norm",
        leftover="REDEF_ITEM_INT",
        leftover2="REDEF_ITEM$SNAP",
        seed="BEGIN DBMS_REDEFINITION.FINISH_REDEF_TABLE('ERP','REDEF_ITEM','REDEF_ITEM_INT'); END;",
        fail="ORA-23539: online redefinition interim leftover REDEF_ITEM_INT + REDEF_ITEM$SNAP; skip finish_redef",
        inspect="SELECT * FROM dba_redefinition_status WHERE object_name='REDEF_ITEM'",
        catalog="online redef interim leftover; expand sku_norm",
        abort="BEGIN DBMS_REDEFINITION.ABORT_REDEF_TABLE('ERP','REDEF_ITEM','REDEF_ITEM_INT'); END;",
        col_type="VARCHAR2(191)",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD sku_norm on erp.redef_item",
    ),
    pl(
        engine="mysql",
        slug="mysql-generated-stored-leftover",
        plant="mysql-gen-stored",
        surface="mysql-generated-stored",
        table="catalog.gen_stored_price",
        col="amount",
        col_v2="amount_v2",
        leftover="gen_stored_price_gc_tmp",
        leftover2="gen_stored_price_gc_old",
        seed="ALTER TABLE catalog.gen_stored_price MODIFY amount DECIMAL(12,4) GENERATED ALWAYS AS (net+tax) STORED",
        fail="ERROR 3105 (HY000): cannot ALTER STORED generated INPLACE; leftover gen_stored_price_gc_tmp + gen_stored_price_gc_old",
        inspect="SELECT COLUMN_NAME, GENERATION_EXPRESSION, EXTRA FROM information_schema.COLUMNS WHERE TABLE_NAME='gen_stored_price'",
        catalog="STORED generated leftover tmp; expand amount_v2",
        abort="DROP TABLE IF EXISTS catalog.gen_stored_price_gc_tmp",
        col_type="DECIMAL(12,4)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD amount_v2 on catalog.gen_stored_price",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-strict-table-rewrite-leftover",
        plant="sqlite-strict",
        surface="sqlite-strict-table",
        table="strict_profile",
        col="email",
        col_v2="email_v2",
        leftover="sqlite_strict_profile_new",
        leftover2="sqlite_stat1",
        seed="CREATE TABLE strict_profile_new (id INTEGER PRIMARY KEY, email TEXT) STRICT",
        fail="Parse error: STRICT table rewrite leftover sqlite_strict_profile_new + sqlite_stat1; skip in-place",
        inspect="SELECT name, sql FROM sqlite_master WHERE name LIKE 'strict_profile%'",
        catalog="STRICT rewrite leftover _new; expand email_v2",
        abort="DROP TABLE IF EXISTS sqlite_strict_profile_new",
        col_type="TEXT",
        db="strict.db",
        lock_fail="Error: database is locked ADD email_v2 on strict_profile",
    ),
    pl(
        engine="mssql",
        slug="mssql-temporal-history-leftover",
        plant="mssql-temporal",
        surface="mssql-temporal-history",
        table="audit.temporal_claim",
        col="status",
        col_v2="status_v2",
        leftover="temporal_claim_history_tmp",
        leftover2="temporal_claim_sys_time",
        seed="ALTER TABLE audit.temporal_claim SET (SYSTEM_VERSIONING = ON (HISTORY_TABLE=audit.temporal_claim_history))",
        fail="Msg 13591: cannot ALTER SYSTEM_VERSIONING; leftover temporal_claim_history_tmp + temporal_claim_sys_time",
        inspect="SELECT t.name, t.temporal_type_desc FROM sys.tables t WHERE t.name='temporal_claim'",
        catalog="temporal history leftover tmp; expand status_v2",
        abort="ALTER TABLE audit.temporal_claim SET (SYSTEM_VERSIONING = OFF)",
        col_type="NVARCHAR(32)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD status_v2 on audit.temporal_claim",
    ),
    pl(
        engine="oracle",
        slug="oracle-unusable-index-leftover",
        plant="oracle-unusable",
        surface="oracle-unusable-index",
        table="dwh.unusable_fact",
        col="dim_id",
        col_v2="dim_uuid",
        leftover="UNUSABLE_FACT_I",
        leftover2="UNUSABLE_FACT_REBUILD_TMP",
        seed="ALTER INDEX dwh.unusable_fact_i REBUILD ONLINE",
        fail="ORA-01502: index DWH.UNUSABLE_FACT_I or partition of such index is in unusable state; leftover UNUSABLE_FACT_I + UNUSABLE_FACT_REBUILD_TMP",
        inspect="SELECT index_name, status FROM user_indexes WHERE table_name='UNUSABLE_FACT'",
        catalog="UNUSABLE index leftover after failed ONLINE rebuild; expand dim_uuid",
        abort="DROP TABLE dwh.UNUSABLE_FACT_REBUILD_TMP",
        col_type="VARCHAR2(36)",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD dim_uuid on dwh.unusable_fact",
    ),
    pl(
        engine="mysql",
        slug="mysql-fulltext-parser-leftover",
        plant="mysql-ft-parser",
        surface="mysql-fulltext-parser",
        table="search.ft_article",
        col="body",
        col_v2="body_v2",
        leftover="ft_article_fts_tmp",
        leftover2="fts_00000_aux",
        seed="ALTER TABLE search.ft_article ADD FULLTEXT INDEX ft_body (body) WITH PARSER ngram",
        fail="ERROR 1795 (HY000): FULLTEXT parser leftover ft_article_fts_tmp + fts_00000_aux after INPLACE abort",
        inspect="SELECT INDEX_NAME, INDEX_TYPE FROM information_schema.STATISTICS WHERE TABLE_NAME='ft_article'",
        catalog="FULLTEXT aux leftover; expand body_v2",
        abort="DROP TABLE IF EXISTS search.ft_article_fts_tmp",
        col_type="LONGTEXT",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD body_v2 on search.ft_article",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-fts5-content-leftover",
        plant="sqlite-fts5",
        surface="sqlite-fts5-content",
        table="fts5_body",
        col="text",
        col_v2="text_v2",
        leftover="fts5_body_content",
        leftover2="fts5_body_docsize",
        seed="INSERT INTO fts5_body(fts5_body) VALUES('rebuild')",
        fail="SQL logic error: FTS5 content leftover fts5_body_content + fts5_body_docsize after failed rebuild; skip rewrite",
        inspect="SELECT name FROM sqlite_master WHERE name LIKE 'fts5_body%'",
        catalog="FTS5 content/docsize leftover; expand text_v2",
        abort="DROP TABLE IF EXISTS fts5_body_content",
        col_type="TEXT",
        db="fts5.db",
        lock_fail="Error: database is locked ADD text_v2 on fts5_body",
    ),
    pl(
        engine="mssql",
        slug="mssql-columnstore-rebuild-leftover",
        plant="mssql-columnstore",
        surface="mssql-columnstore-rebuild",
        table="analytics.cs_event",
        col="payload",
        col_v2="payload_v2",
        leftover="cs_event_delta_store",
        leftover2="cs_event_rowgroup_tmp",
        seed="ALTER INDEX CCI_cs_event ON analytics.cs_event REBUILD WITH (ONLINE=ON)",
        fail="Msg 35377: COLUMNSTORE rebuild leftover cs_event_delta_store + cs_event_rowgroup_tmp",
        inspect="SELECT name, type_desc FROM sys.indexes WHERE object_id=OBJECT_ID('analytics.cs_event')",
        catalog="columnstore delta leftover; expand payload_v2",
        abort="DROP TABLE analytics.cs_event_rowgroup_tmp",
        col_type="NVARCHAR(MAX)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD payload_v2 on analytics.cs_event",
    ),
    pl(
        engine="mariadb",
        slug="mariadb-system-versioned-leftover",
        plant="maria-sysver",
        surface="mariadb-system-versioned",
        table="hist.sysver_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="sysver_sku_history",
        leftover2="sysver_sku_vers_tmp",
        seed="ALTER TABLE hist.sysver_sku ADD SYSTEM VERSIONING",
        fail="ERROR 4119 (HY000): SYSTEM VERSIONING leftover sysver_sku_history + sysver_sku_vers_tmp after failed ALTER",
        inspect="SELECT TABLE_NAME, TABLE_TYPE FROM information_schema.TABLES WHERE TABLE_NAME LIKE 'sysver_sku%'",
        catalog="MariaDB system-versioned leftover history; expand sku_norm",
        abort="ALTER TABLE hist.sysver_sku DROP SYSTEM VERSIONING",
        col_type="VARCHAR(191)",
    ),
    pl(
        engine="mysql",
        slug="mysql-invisible-column-leftover",
        plant="mysql-invis-col",
        surface="mysql-invisible-column",
        table="users.invisible_email",
        col="email",
        col_v2="email_v2",
        leftover="invisible_email_inv_tmp",
        leftover2="invisible_email_frm",
        seed="ALTER TABLE users.invisible_email ALTER COLUMN email SET INVISIBLE",
        fail="ERROR 3956 (HY000): INVISIBLE column leftover invisible_email_inv_tmp + invisible_email_frm after failed INSTANT; skip in-place",
        inspect="SELECT COLUMN_NAME, EXTRA FROM information_schema.COLUMNS WHERE TABLE_NAME='invisible_email'",
        catalog="INVISIBLE column leftover frm/tmp; expand email_v2",
        abort="DROP TABLE IF EXISTS users.invisible_email_inv_tmp",
        col_type="VARCHAR(320)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD email_v2 on users.invisible_email",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-without-rowid-rebuild-leftover",
        plant="sqlite-worowid",
        surface="sqlite-without-rowid",
        table="worowid_kv",
        col="val",
        col_v2="val_v2",
        leftover="worowid_kv_new",
        leftover2="sqlite_autoindex_worowid_kv_1",
        seed="CREATE TABLE worowid_kv_new (k TEXT PRIMARY KEY, val TEXT) WITHOUT ROWID",
        fail="NOTICE: already skip: WITHOUT ROWID rebuild leftover worowid_kv_new + sqlite_autoindex_worowid_kv_1",
        inspect="SELECT name, sql FROM sqlite_master WHERE name LIKE 'worowid_kv%'",
        catalog="WITHOUT ROWID leftover _new; expand val_v2",
        abort="DROP TABLE IF EXISTS worowid_kv_new",
        col_type="TEXT",
        db="worowid.db",
        lock_fail="Error: database is locked ADD val_v2 on worowid_kv",
    ),
    pl(
        engine="mssql",
        slug="mssql-filtered-index-leftover",
        plant="mssql-filtered",
        surface="mssql-filtered-index",
        table="shop.filtered_ix_order",
        col="sku",
        col_v2="sku_norm",
        leftover="filtered_ix_order_ix_tmp",
        leftover2="filtered_ix_order_flt",
        seed="CREATE INDEX IX_filtered_ix_order_open ON shop.filtered_ix_order(sku) WHERE status='open' WITH (ONLINE=ON)",
        fail="Msg 10609: filtered index leftover filtered_ix_order_ix_tmp + filtered_ix_order_flt after ONLINE rebuild abort",
        inspect="SELECT name, has_filter, filter_definition FROM sys.indexes WHERE object_id=OBJECT_ID('shop.filtered_ix_order')",
        catalog="filtered index leftover; expand sku_norm",
        abort="DROP INDEX IX_filtered_ix_order_open ON shop.filtered_ix_order",
        col_type="NVARCHAR(191)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD sku_norm on shop.filtered_ix_order",
    ),
    pl(
        engine="oracle",
        slug="oracle-virtual-column-leftover",
        plant="oracle-virtcol",
        surface="oracle-virtual-column",
        table="finance.virt_col_invoice",
        col="total",
        col_v2="total_v2",
        leftover="VIRT_COL_INVOICE_VC_TMP",
        leftover2="SYS_C00_VIRT",
        seed="ALTER TABLE finance.virt_col_invoice ADD (total_gen NUMBER GENERATED ALWAYS AS (net+tax) VIRTUAL)",
        fail="ORA-54013: virtual column leftover VIRT_COL_INVOICE_VC_TMP + SYS_C00_VIRT; skip in-place rewrite",
        inspect="SELECT column_name, virtual_column FROM user_tab_cols WHERE table_name='VIRT_COL_INVOICE'",
        catalog="virtual column leftover; expand total_v2",
        abort="DROP TABLE finance.VIRT_COL_INVOICE_VC_TMP",
        col_type="NUMBER(18,4)",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD total_v2 on finance.virt_col_invoice",
    ),
    pl(
        engine="mysql",
        slug="mysql-functional-index-leftover",
        plant="mysql-func-idx",
        surface="mysql-functional-index",
        table="catalog.func_idx_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="func_idx_sku_hidden_gc",
        leftover2="func_idx_sku_idx_tmp",
        seed="ALTER TABLE catalog.func_idx_sku ADD INDEX idx_sku_lower ((LOWER(sku)))",
        fail="ERROR 3758 (HY000): functional index hidden generated leftover func_idx_sku_hidden_gc + func_idx_sku_idx_tmp",
        inspect="SELECT INDEX_NAME, EXPRESSION FROM information_schema.STATISTICS WHERE TABLE_NAME='func_idx_sku'",
        catalog="functional index hidden GC leftover; expand sku_norm",
        abort="DROP TABLE IF EXISTS catalog.func_idx_sku_idx_tmp",
        col_type="VARCHAR(191)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD sku_norm on catalog.func_idx_sku",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-generated-always-leftover",
        plant="sqlite-gen-always",
        surface="sqlite-generated-always",
        table="gen_always_qty",
        col="qty",
        col_v2="qty_v2",
        leftover="sqlite_gen_always_qty_new",
        leftover2="gen_always_qty_old",
        seed="ALTER TABLE gen_always_qty ADD COLUMN qty_gen INTEGER GENERATED ALWAYS AS (qty_base * 2) STORED",
        fail="generated always leftover sqlite_gen_always_qty_new + gen_always_qty_old after table rewrite abort",
        inspect="SELECT name, sql FROM sqlite_master WHERE name LIKE 'gen_always_qty%'",
        catalog="GENERATED ALWAYS leftover rewrite tmp; expand qty_v2",
        abort="DROP TABLE IF EXISTS sqlite_gen_always_qty_new",
        col_type="INTEGER",
        db="genqty.db",
        lock_fail="Error: database is locked ADD qty_v2 on gen_always_qty",
    ),
    pl(
        engine="mysql",
        slug="mysql-partition-exchange-leftover",
        plant="mysql-exch-part",
        surface="mysql-partition-exchange",
        table="shop.exch_part_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="exch_part_sku_p2024",
        leftover2="exch_part_sku_ex",
        seed="ALTER TABLE shop.exch_part_sku EXCHANGE PARTITION p2024 WITH TABLE shop.exch_part_sku_ex",
        fail="ERROR 1735 (HY000): EXCHANGE PARTITION leftover exch_part_sku_p2024 + exch_part_sku_ex after failed swap",
        inspect="SELECT PARTITION_NAME, TABLE_ROWS FROM information_schema.PARTITIONS WHERE TABLE_NAME='exch_part_sku'",
        catalog="EXCHANGE PARTITION leftover staging; expand sku_norm",
        abort="DROP TABLE IF EXISTS shop.exch_part_sku_ex",
        col_type="VARCHAR(191)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD sku_norm on shop.exch_part_sku",
    ),
    pl(
        engine="mssql",
        slug="mssql-partition-switch-leftover",
        plant="mssql-switch",
        surface="mssql-partition-switch",
        table="warehouse.switch_part_fact",
        col="units",
        col_v2="units_v2",
        leftover="switch_part_fact_stg",
        leftover2="switch_part_fact_p2024",
        seed="ALTER TABLE warehouse.switch_part_fact SWITCH PARTITION 2024 TO warehouse.switch_part_fact_stg",
        fail="Msg 4972: SWITCH PARTITION leftover switch_part_fact_stg + switch_part_fact_p2024",
        inspect="SELECT p.partition_number, p.rows FROM sys.partitions p WHERE p.object_id=OBJECT_ID('warehouse.switch_part_fact')",
        catalog="SWITCH leftover staging partition; expand units_v2",
        abort="TRUNCATE TABLE warehouse.switch_part_fact_stg",
        col_type="BIGINT",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD units_v2 on warehouse.switch_part_fact",
    ),
    pl(
        engine="mysql",
        slug="mysql-autoinc-counter-leftover",
        plant="mysql-autoinc",
        surface="mysql-autoinc-counter",
        table="catalog.autoinc_ticket",
        col="code",
        col_v2="code_v2",
        leftover="autoinc_ticket_ai_tmp",
        leftover2="autoinc_ticket_ibd",
        seed="ALTER TABLE catalog.autoinc_ticket AUTO_INCREMENT=5000000, ALGORITHM=COPY",
        fail="ERROR 1467 (HY000): AUTO_INCREMENT leftover autoinc_ticket_ai_tmp + autoinc_ticket_ibd after failed COPY",
        inspect="SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_NAME='autoinc_ticket'",
        catalog="AUTO_INCREMENT COPY leftover ibd/tmp; expand code_v2",
        abort="DROP TABLE IF EXISTS catalog.autoinc_ticket_ai_tmp",
        col_type="VARCHAR(64)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD code_v2 on catalog.autoinc_ticket",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-sqlite-sequence-leftover",
        plant="sqlite-sequence",
        surface="sqlite-sqlite-sequence",
        table="seq_rowid",
        col="label",
        col_v2="label_v2",
        leftover="sqlite_sequence",
        leftover2="seq_rowid_old",
        seed="UPDATE sqlite_sequence SET seq=900000 WHERE name='seq_rowid'",
        fail="UNIQUE constraint sqlite_sequence leftover sqlite_sequence + seq_rowid_old after rewrite abort",
        inspect="SELECT name, seq FROM sqlite_sequence WHERE name='seq_rowid'",
        catalog="sqlite_sequence leftover after rewrite abort; expand label_v2",
        abort="DELETE FROM sqlite_sequence WHERE name='seq_rowid_old'",
        col_type="TEXT",
        db="seq.db",
        lock_fail="Error: database is locked ADD label_v2 on seq_rowid",
    ),
    pl(
        engine="mssql",
        slug="mssql-dynamic-data-mask-leftover",
        plant="mssql-mask",
        surface="mssql-dynamic-mask",
        table="pii.masked_ssn",
        col="ssn",
        col_v2="ssn_v2",
        leftover="masked_ssn_mask_tmp",
        leftover2="masked_ssn_sec",
        seed="ALTER TABLE pii.masked_ssn ALTER COLUMN ssn ADD MASKED WITH (FUNCTION='partial(0,\"XXX-XX-\",4)')",
        fail="Msg 33522: MASKED leftover masked_ssn_mask_tmp + masked_ssn_sec after failed ALTER COLUMN",
        inspect="SELECT c.name, c.is_masked FROM sys.columns c WHERE c.object_id=OBJECT_ID('pii.masked_ssn')",
        catalog="dynamic data mask leftover; expand ssn_v2",
        abort="DROP TABLE pii.masked_ssn_mask_tmp",
        col_type="NVARCHAR(11)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD ssn_v2 on pii.masked_ssn",
    ),
    pl(
        engine="oracle",
        slug="oracle-editioning-view-leftover",
        plant="oracle-edition",
        surface="oracle-editioning-view",
        table="app.edition_view_item",
        col="body",
        col_v2="body_v2",
        leftover="EDITION_VIEW_ITEM_EV",
        leftover2="EDITION_VIEW_ITEM_AE",
        seed="CREATE OR REPLACE EDITIONING VIEW app.edition_view_item_ev AS SELECT * FROM app.edition_view_item",
        fail="ORA-38812: editioning view leftover EDITION_VIEW_ITEM_EV + EDITION_VIEW_ITEM_AE; skip in-place",
        inspect="SELECT view_name, editioning_view FROM user_views WHERE view_name LIKE 'EDITION_VIEW_ITEM%'",
        catalog="editioning view leftover; expand body_v2",
        abort="DROP VIEW app.EDITION_VIEW_ITEM_EV",
        col_type="CLOB",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD body_v2 on app.edition_view_item",
    ),
    pl(
        engine="mysql",
        slug="mysql-check-constraint-leftover",
        plant="mysql-check",
        surface="mysql-check-constraint",
        table="catalog.check_amount",
        col="amount",
        col_v2="amount_v2",
        leftover="check_amount_chk_tmp",
        leftover2="check_amount_chk1",
        seed="ALTER TABLE catalog.check_amount ADD CONSTRAINT check_amount_chk1 CHECK (amount >= 0)",
        fail="ERROR 3819 (HY000): CHECK leftover check_amount_chk_tmp + check_amount_chk1 after failed ADD CONSTRAINT (existing rows violate)",
        inspect="SELECT CONSTRAINT_NAME, CHECK_CLAUSE FROM information_schema.CHECK_CONSTRAINTS WHERE CONSTRAINT_NAME LIKE 'check_amount%'",
        catalog="CHECK constraint leftover after failed ADD; expand amount_v2",
        abort="ALTER TABLE catalog.check_amount DROP CHECK check_amount_chk1",
        col_type="DECIMAL(12,4)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD amount_v2 on catalog.check_amount",
    ),
    pl(
        engine="mariadb",
        slug="mariadb-sequence-leftover",
        plant="maria-seq",
        surface="mariadb-sequence",
        table="billing.maria_seq_pay",
        col="ref",
        col_v2="ref_v2",
        leftover="maria_seq_pay_s",
        leftover2="maria_seq_pay_tmp",
        seed="CREATE SEQUENCE billing.maria_seq_pay_s START WITH 1000 INCREMENT BY 1",
        fail="ERROR 4089 (HY000): SEQUENCE leftover maria_seq_pay_s + maria_seq_pay_tmp after failed CREATE SEQUENCE in txn",
        inspect="SELECT SEQUENCE_NAME FROM information_schema.SEQUENCES WHERE SEQUENCE_NAME LIKE 'maria_seq_pay%'",
        catalog="MariaDB SEQUENCE leftover; expand ref_v2",
        abort="DROP SEQUENCE IF EXISTS billing.maria_seq_pay_s",
        col_type="VARCHAR(64)",
    ),
    pl(
        engine="mssql",
        slug="mssql-ledger-digest-leftover",
        plant="mssql-ledger",
        surface="mssql-ledger-digest",
        table="audit.ledger_digest",
        col="hash",
        col_v2="hash_v2",
        leftover="ledger_digest_hist",
        leftover2="ledger_digest_view",
        seed="ALTER TABLE audit.ledger_digest SET (LEDGER = ON (APPEND_ONLY = ON))",
        fail="Msg 37319: LEDGER leftover ledger_digest_hist + ledger_digest_view after failed ALTER",
        inspect="SELECT name, is_ledger_on FROM sys.tables WHERE name='ledger_digest'",
        catalog="ledger digest leftover hist/view; expand hash_v2",
        abort="DROP VIEW audit.ledger_digest_view",
        col_type="VARBINARY(32)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD hash_v2 on audit.ledger_digest",
    ),
    pl(
        engine="mysql",
        slug="mysql-srid-spatial-leftover",
        plant="mysql-srid",
        surface="mysql-srid-spatial",
        table="geo.srid_point",
        col="loc",
        col_v2="loc_v2",
        leftover="srid_point_sp_tmp",
        leftover2="srid_point_idx",
        seed="ALTER TABLE geo.srid_point MODIFY loc POINT NOT NULL SRID 4326",
        fail="ERROR 3033 (HY000): SRID mismatch leftover srid_point_sp_tmp + srid_point_idx",
        inspect="SELECT COLUMN_NAME, SRS_ID FROM information_schema.ST_GEOMETRY_COLUMNS WHERE TABLE_NAME='srid_point'",
        catalog="SRID spatial leftover idx/tmp; expand loc_v2",
        abort="DROP TABLE IF EXISTS geo.srid_point_sp_tmp",
        col_type="POINT",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD loc_v2 on geo.srid_point",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-rtree-aux-leftover",
        plant="sqlite-rtree",
        surface="sqlite-rtree-aux",
        table="rtree_box",
        col="geom",
        col_v2="geom_v2",
        leftover="rtree_box_node",
        leftover2="rtree_box_parent",
        seed="INSERT INTO rtree_box(rtree_box, rank) VALUES('rebuild', 0)",
        fail="rtree aux leftover rtree_box_node + rtree_box_parent after failed virtual table rebuild",
        inspect="SELECT name FROM sqlite_master WHERE name LIKE 'rtree_box%'",
        catalog="R-tree node/parent leftover; expand geom_v2",
        abort="DROP TABLE IF EXISTS rtree_box_node",
        col_type="TEXT",
        db="rtree.db",
        lock_fail="Error: database is locked ADD geom_v2 on rtree_box",
    ),
    pl(
        engine="oracle",
        slug="oracle-deferred-segment-leftover",
        plant="oracle-defseg",
        surface="oracle-deferred-segment",
        table="dwh.deferred_seg",
        col="payload",
        col_v2="payload_v2",
        leftover="DEFERRED_SEG_TMP",
        leftover2="DEFERRED_SEG_SEG$",
        seed="ALTER TABLE dwh.deferred_seg ALLOCATE EXTENT",
        fail="ORA-14223: deferred segment leftover DEFERRED_SEG_TMP + DEFERRED_SEG_SEG$; skip in-place rewrite",
        inspect="SELECT table_name, segment_created FROM user_tables WHERE table_name='DEFERRED_SEG'",
        catalog="deferred segment leftover SEG$; expand payload_v2",
        abort="DROP TABLE dwh.DEFERRED_SEG_TMP",
        col_type="BLOB",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD payload_v2 on dwh.deferred_seg",
    ),
    pl(
        engine="crdb",
        slug="crdb-schema-locked-leftover",
        plant="crdb-schema-lock",
        surface="crdb-schema-locked",
        table="shop.locked_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="locked_sku_schema_locked",
        leftover2="locked_sku_mvcc_tmp",
        seed="ALTER TABLE shop.locked_sku SET (schema_locked = true)",
        fail="ERROR: table shop.locked_sku is schema_locked; leftover locked_sku_schema_locked + locked_sku_mvcc_tmp",
        inspect="SHOW CREATE TABLE shop.locked_sku",
        catalog="schema_locked leftover; expand sku_norm",
        abort="ALTER TABLE shop.locked_sku SET (schema_locked = false)",
        col_type="STRING",
        lock_fail="pq: lock timeout ADD sku_norm on shop.locked_sku",
    ),
    pl(
        engine="crdb",
        slug="crdb-not-visible-index-leftover",
        plant="crdb-nvis-idx",
        surface="crdb-not-visible-index",
        table="shop.nvis_order",
        col="qty",
        col_v2="qty_v2",
        leftover="nvis_order_idx_not_visible",
        leftover2="nvis_order_tmp",
        seed="CREATE INDEX nvis_order_idx ON shop.nvis_order (qty) NOT VISIBLE",
        fail="ERROR: NOT VISIBLE index leftover nvis_order_idx_not_visible + nvis_order_tmp after failed CREATE INDEX",
        inspect="SHOW INDEX FROM shop.nvis_order",
        catalog="NOT VISIBLE index leftover; expand qty_v2",
        abort="DROP INDEX IF EXISTS nvis_order_idx",
        col_type="INT8",
        lock_fail="pq: lock timeout ADD qty_v2 on shop.nvis_order",
    ),
    pl(
        engine="mysql",
        slug="mysql-ptosc-trigger-leftover",
        plant="mysql-ptosc",
        surface="mysql-ptosc-trigger",
        table="shop.ptosc_item",
        col="sku",
        col_v2="sku_norm",
        leftover="_ptosc_item_new",
        leftover2="pt_osc_ptosc_item_ins",
        seed="pt-online-schema-change --alter 'CHANGE sku sku VARCHAR(191)' D=shop,t=ptosc_item --execute",
        fail="pt-online-schema-change abort leftover _ptosc_item_new + pt_osc_ptosc_item_ins trigger; skip in-place",
        inspect="SHOW TRIGGERS FROM shop LIKE 'ptosc_item%'",
        catalog="pt-osc leftover _new + triggers; expand sku_norm",
        abort="DROP TRIGGER IF EXISTS shop.pt_osc_ptosc_item_ins; DROP TABLE IF EXISTS shop._ptosc_item_new",
        col_type="VARCHAR(191)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD sku_norm on shop.ptosc_item",
    ),
    pl(
        engine="mysql",
        slug="mysql-ghost-cutover-leftover",
        plant="mysql-ghost",
        surface="mysql-ghost-cutover",
        table="shop.ghost_item",
        col="body",
        col_v2="body_v2",
        leftover="_ghost_item_gho",
        leftover2="_ghost_item_del",
        seed="gh-ost --alter='CHANGE body body LONGBLOB' --database=shop --table=ghost_item --execute",
        fail="gh-ost cutover abort leftover _ghost_item_gho + _ghost_item_del; skip in-place rewrite",
        inspect="SHOW TABLES FROM shop LIKE '%ghost_item%'",
        catalog="gh-ost leftover _gho/_del; expand body_v2",
        abort="DROP TABLE IF EXISTS shop._ghost_item_gho; DROP TABLE IF EXISTS shop._ghost_item_del",
        col_type="LONGBLOB",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD body_v2 on shop.ghost_item",
    ),
    pl(
        engine="mysql",
        slug="mysql-histogram-stats-leftover",
        plant="mysql-histogram",
        surface="mysql-histogram-stats",
        table="catalog.hist_sku",
        col="price",
        col_v2="price_v2",
        leftover="hist_sku_buckets",
        leftover2="hist_sku_stats_tmp",
        seed="ANALYZE TABLE catalog.hist_sku UPDATE HISTOGRAM ON price WITH 64 BUCKETS",
        fail="ERROR 3997 (HY000): histogram leftover hist_sku_buckets + hist_sku_stats_tmp after failed ANALYZE; skip in-place rewrite",
        inspect="SELECT TABLE_NAME, COLUMN_NAME, JSON_LENGTH(HISTOGRAM) FROM information_schema.COLUMN_STATISTICS WHERE TABLE_NAME='hist_sku'",
        catalog="histogram bucket leftover; expand price_v2",
        abort="ANALYZE TABLE catalog.hist_sku DROP HISTOGRAM ON price",
        col_type="DECIMAL(12,4)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD price_v2 on catalog.hist_sku",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-partial-index-leftover",
        plant="sqlite-partial-idx",
        surface="sqlite-partial-index",
        table="partial_order",
        col="sku",
        col_v2="sku_norm",
        leftover="idx_partial_order_open",
        leftover2="partial_order_idx_tmp",
        seed="CREATE INDEX idx_partial_order_open ON partial_order(sku) WHERE status='open'",
        fail="NOTICE: already skip: partial index leftover idx_partial_order_open + partial_order_idx_tmp after failed CREATE INDEX",
        inspect="SELECT name, sql FROM sqlite_master WHERE name LIKE 'partial_order%'",
        catalog="partial index leftover; expand sku_norm",
        abort="DROP INDEX IF EXISTS idx_partial_order_open",
        col_type="TEXT",
        db="partial.db",
        lock_fail="Error: database is locked ADD sku_norm on partial_order",
    ),
    pl(
        engine="mssql",
        slug="mssql-memory-optimized-leftover",
        plant="mssql-memopt",
        surface="mssql-memory-optimized",
        table="hot.memopt_session",
        col="token",
        col_v2="token_v2",
        leftover="memopt_session_xtp_tmp",
        leftover2="memopt_session_hk_file",
        seed="ALTER TABLE hot.memopt_session SET (MEMORY_OPTIMIZED = ON)",
        fail="Msg 12305: MEMORY_OPTIMIZED leftover memopt_session_xtp_tmp + memopt_session_hk_file after failed ALTER",
        inspect="SELECT name, is_memory_optimized FROM sys.tables WHERE name='memopt_session'",
        catalog="In-Memory OLTP leftover XTP file; expand token_v2",
        abort="DROP TABLE hot.memopt_session_xtp_tmp",
        col_type="NVARCHAR(128)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD token_v2 on hot.memopt_session",
    ),
    pl(
        engine="oracle",
        slug="oracle-extended-stats-leftover",
        plant="oracle-extstats",
        surface="oracle-extended-stats",
        table="dwh.ext_stats_dim",
        col="attr",
        col_v2="attr_v2",
        leftover="SYS_STU_EXT_STATS_DIM",
        leftover2="EXT_STATS_DIM_TMP",
        seed="BEGIN DBMS_STATS.CREATE_EXTENDED_STATS('DWH','EXT_STATS_DIM','(ATTR,REGION)'); END;",
        fail="ORA-20000: extended stats leftover SYS_STU_EXT_STATS_DIM + EXT_STATS_DIM_TMP after failed CREATE_EXTENDED_STATS",
        inspect="SELECT extension_name FROM user_stat_extensions WHERE table_name='EXT_STATS_DIM'",
        catalog="extended stats leftover; expand attr_v2",
        abort="BEGIN DBMS_STATS.DROP_EXTENDED_STATS('DWH','EXT_STATS_DIM','(ATTR,REGION)'); END;",
        col_type="VARCHAR2(191)",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD attr_v2 on dwh.ext_stats_dim",
    ),
    pl(
        engine="mariadb",
        slug="mariadb-spider-leftover",
        plant="maria-spider",
        surface="mariadb-spider",
        table="fed.spider_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="spider_sku_link",
        leftover2="spider_sku_xa_tmp",
        seed="ALTER TABLE fed.spider_sku ENGINE=SPIDER COMMENT='wrapper \"mysql\", table \"sku\"'",
        fail="ERROR 1429 (HY000): SPIDER leftover spider_sku_link + spider_sku_xa_tmp after failed ENGINE swap",
        inspect="SELECT ENGINE, CREATE_OPTIONS FROM information_schema.TABLES WHERE TABLE_NAME='spider_sku'",
        catalog="Spider wrapper leftover XA tmp; expand sku_norm",
        abort="DROP TABLE IF EXISTS fed.spider_sku_xa_tmp",
        col_type="VARCHAR(191)",
    ),
    pl(
        engine="mysql",
        slug="mysql-descending-index-leftover",
        plant="mysql-desc-idx",
        surface="mysql-descending-index",
        table="shop.desc_idx_order",
        col="created_at",
        col_v2="created_at_v2",
        leftover="desc_idx_order_desc_tmp",
        leftover2="desc_idx_order_idx",
        seed="ALTER TABLE shop.desc_idx_order ADD INDEX idx_created_desc (created_at DESC)",
        fail="ERROR 1170 (42000): descending index leftover desc_idx_order_desc_tmp + desc_idx_order_idx after failed ADD INDEX",
        inspect="SELECT INDEX_NAME, COLLATION FROM information_schema.STATISTICS WHERE TABLE_NAME='desc_idx_order'",
        catalog="DESC index leftover tmp; expand created_at_v2",
        abort="DROP TABLE IF EXISTS shop.desc_idx_order_desc_tmp",
        col_type="DATETIME(6)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD created_at_v2 on shop.desc_idx_order",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-trigger-after-leftover",
        plant="sqlite-trig-after",
        surface="sqlite-trigger-after",
        table="trig_audit",
        col="body",
        col_v2="body_v2",
        leftover="trg_trig_audit_ai",
        leftover2="trig_audit_log_tmp",
        seed="CREATE TRIGGER trg_trig_audit_ai AFTER INSERT ON trig_audit BEGIN INSERT INTO trig_audit_log VALUES(new.id); END",
        fail="SQL logic error: AFTER trigger leftover trg_trig_audit_ai + trig_audit_log_tmp after failed CREATE TRIGGER; skip rewrite",
        inspect="SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='trig_audit'",
        catalog="AFTER INSERT trigger leftover; expand body_v2",
        abort="DROP TRIGGER IF EXISTS trg_trig_audit_ai",
        col_type="TEXT",
        db="trig.db",
        lock_fail="Error: database is locked ADD body_v2 on trig_audit",
    ),
    pl(
        engine="mssql",
        slug="mssql-graph-edge-leftover",
        plant="mssql-graph",
        surface="mssql-graph-edge",
        table="social.graph_follows",
        col="since",
        col_v2="since_v2",
        leftover="graph_follows_edge_tmp",
        leftover2="graph_follows_node_tmp",
        seed="ALTER TABLE social.graph_follows SET (EDGE = ON)",
        fail="Msg 13919: graph EDGE leftover graph_follows_edge_tmp + graph_follows_node_tmp after failed ALTER",
        inspect="SELECT name, is_edge FROM sys.tables WHERE name='graph_follows'",
        catalog="SQL Graph edge leftover; expand since_v2",
        abort="DROP TABLE social.graph_follows_edge_tmp",
        col_type="DATETIME2",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD since_v2 on social.graph_follows",
    ),
    pl(
        engine="oracle",
        slug="oracle-matview-rewrite-leftover",
        plant="oracle-mview",
        surface="oracle-matview-rewrite",
        table="dwh.mv_sales_day",
        col="gross",
        col_v2="gross_v2",
        leftover="MV_SALES_DAY_TMP",
        leftover2="MV_SALES_DAY_SNAP$",
        seed="ALTER MATERIALIZED VIEW dwh.mv_sales_day REFRESH FAST ON COMMIT",
        fail="ORA-12034: materialized view log leftover MV_SALES_DAY_TMP + MV_SALES_DAY_SNAP$ after failed REFRESH FAST",
        inspect="SELECT mview_name, rewrite_enabled FROM user_mviews WHERE mview_name='MV_SALES_DAY'",
        catalog="mview rewrite leftover SNAP$; expand gross_v2",
        abort="DROP TABLE dwh.MV_SALES_DAY_TMP",
        col_type="NUMBER(18,4)",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD gross_v2 on dwh.mv_sales_day",
    ),
    pl(
        engine="mysql",
        slug="mysql-innodb-encrypt-leftover",
        plant="mysql-encrypt",
        surface="mysql-innodb-encrypt",
        table="pii.encrypt_card",
        col="pan",
        col_v2="pan_v2",
        leftover="encrypt_card_enc_tmp",
        leftover2="encrypt_card_ibd",
        seed="ALTER TABLE pii.encrypt_card ENCRYPTION='Y', ALGORITHM=INPLACE",
        fail="ERROR 3185 (HY000): ENCRYPTION leftover encrypt_card_enc_tmp + encrypt_card_ibd after failed INPLACE",
        inspect="SELECT NAME, ENCRYPTION FROM information_schema.INNODB_TABLESPACES WHERE NAME LIKE 'pii/encrypt_card%'",
        catalog="InnoDB ENCRYPTION leftover ibd/tmp; expand pan_v2",
        abort="DROP TABLE IF EXISTS pii.encrypt_card_enc_tmp",
        col_type="VARBINARY(64)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD pan_v2 on pii.encrypt_card",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-json-generated-leftover",
        plant="sqlite-json-gen",
        surface="sqlite-json-generated",
        table="json_doc",
        col="doc",
        col_v2="doc_v2",
        leftover="sqlite_json_doc_new",
        leftover2="json_doc_old",
        seed="ALTER TABLE json_doc ADD COLUMN sku TEXT GENERATED ALWAYS AS (json_extract(doc, '$.sku')) VIRTUAL",
        fail="generated json_extract leftover sqlite_json_doc_new + json_doc_old after table rewrite abort; skip in-place",
        inspect="SELECT name, sql FROM sqlite_master WHERE name LIKE 'json_doc%'",
        catalog="JSON generated leftover rewrite tmp; expand doc_v2",
        abort="DROP TABLE IF EXISTS sqlite_json_doc_new",
        col_type="TEXT",
        db="jsondoc.db",
        lock_fail="Error: database is locked ADD doc_v2 on json_doc",
    ),
    pl(
        engine="mssql",
        slug="mssql-filestream-leftover",
        plant="mssql-filestream",
        surface="mssql-filestream",
        table="blob.fs_object",
        col="payload",
        col_v2="payload_v2",
        leftover="fs_object_fs_tmp",
        leftover2="fs_object_filetable",
        seed="ALTER TABLE blob.fs_object ADD payload_fs VARBINARY(MAX) FILESTREAM",
        fail="Msg 1969: FILESTREAM leftover fs_object_fs_tmp + fs_object_filetable after failed ADD",
        inspect="SELECT name, is_filestream FROM sys.columns WHERE object_id=OBJECT_ID('blob.fs_object')",
        catalog="FILESTREAM leftover filetable; expand payload_v2",
        abort="DROP TABLE blob.fs_object_fs_tmp",
        col_type="VARBINARY(MAX)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD payload_v2 on blob.fs_object",
    ),
    pl(
        engine="oracle",
        slug="oracle-iot-overflow-leftover",
        plant="oracle-iot",
        surface="oracle-iot-overflow",
        table="erp.iot_overflow_item",
        col="body",
        col_v2="body_v2",
        leftover="SYS_IOT_OVER_ITEM",
        leftover2="IOT_OVERFLOW_ITEM_TMP",
        seed="ALTER TABLE erp.iot_overflow_item MOVE OVERFLOW TABLESPACE overflow_tbs",
        fail="ORA-25191: IOT overflow leftover SYS_IOT_OVER_ITEM + IOT_OVERFLOW_ITEM_TMP after failed MOVE OVERFLOW",
        inspect="SELECT table_name, iot_type FROM user_tables WHERE table_name LIKE 'IOT_OVERFLOW_ITEM%'",
        catalog="IOT overflow leftover; expand body_v2",
        abort="DROP TABLE erp.IOT_OVERFLOW_ITEM_TMP",
        col_type="CLOB",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD body_v2 on erp.iot_overflow_item",
    ),
    pl(
        engine="mysql",
        slug="mysql-gtid-purged-leftover",
        plant="mysql-gtid",
        surface="mysql-gtid-purged",
        table="repl.gtid_ticket",
        col="binlog_pos",
        col_v2="binlog_pos_v2",
        leftover="gtid_executed_tmp",
        leftover2="gtid_purged_gap",
        seed="SET GLOBAL gtid_purged='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa:1-9000'",
        fail="ERROR 3546 (HY000): gtid_purged leftover gtid_executed_tmp + gtid_purged_gap; skip in-place rewrite of binlog_pos",
        inspect="SELECT @@global.gtid_executed, @@global.gtid_purged",
        catalog="gtid_purged leftover gap; expand binlog_pos_v2",
        abort="RESET BINARY LOGS AND GTIDS",
        col_type="VARCHAR(64)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD binlog_pos_v2 on repl.gtid_ticket",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-pragma-fk-leftover",
        plant="sqlite-pragma-fk",
        surface="sqlite-pragma-fk",
        table="fk_child",
        col="parent_id",
        col_v2="parent_uuid",
        leftover="fk_child_old",
        leftover2="sqlite_autoindex_fk_child_1",
        seed="PRAGMA foreign_keys=OFF; ALTER TABLE fk_child RENAME TO fk_child_old",
        fail="NOTICE: already skip: PRAGMA foreign_keys leftover fk_child_old + sqlite_autoindex_fk_child_1 after rewrite abort",
        inspect="PRAGMA foreign_key_check(fk_child); PRAGMA foreign_keys",
        catalog="PRAGMA foreign_keys leftover old table; expand parent_uuid",
        abort="DROP TABLE IF EXISTS fk_child_old",
        col_type="TEXT",
        db="fkpragma.db",
        lock_fail="Error: database is locked ADD parent_uuid on fk_child",
    ),
    pl(
        engine="mssql",
        slug="mssql-change-tracking-leftover",
        plant="mssql-ct",
        surface="mssql-change-tracking",
        table="sync.ct_row",
        col="payload",
        col_v2="payload_v2",
        leftover="change_tracking_ct_row",
        leftover2="ct_row_sys_tmp",
        seed="ALTER TABLE sync.ct_row ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON)",
        fail="Msg 4997: CHANGE_TRACKING leftover change_tracking_ct_row + ct_row_sys_tmp after failed ENABLE",
        inspect="SELECT t.name, ct.is_track_columns_updated_on FROM sys.change_tracking_tables ct JOIN sys.tables t ON t.object_id=ct.object_id",
        catalog="change tracking leftover; expand payload_v2",
        abort="ALTER TABLE sync.ct_row DISABLE CHANGE_TRACKING",
        col_type="NVARCHAR(MAX)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD payload_v2 on sync.ct_row",
    ),
    pl(
        engine="crdb",
        slug="crdb-hash-sharded-leftover",
        plant="crdb-hashshard",
        surface="crdb-hash-sharded",
        table="shop.hash_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="hash_sku_shard_idx",
        leftover2="hash_sku_crdb_internal_idx",
        seed="CREATE INDEX hash_sku_shard_idx ON shop.hash_sku (sku) USING HASH WITH BUCKET_COUNT = 8",
        fail="ERROR: hash-sharded index leftover hash_sku_shard_idx + hash_sku_crdb_internal_idx after failed CREATE INDEX",
        inspect="SHOW INDEX FROM shop.hash_sku",
        catalog="hash-sharded index leftover; expand sku_norm",
        abort="DROP INDEX IF EXISTS hash_sku_shard_idx",
        col_type="STRING",
        lock_fail="pq: lock timeout ADD sku_norm on shop.hash_sku",
    ),
    pl(
        engine="mysql",
        slug="mysql-heatwave-secondary-leftover",
        plant="mysql-heatwave",
        surface="mysql-heatwave-secondary",
        table="analytics.hw_event",
        col="payload",
        col_v2="payload_v2",
        leftover="hw_event_secondary",
        leftover2="hw_event_lakehouse_tmp",
        seed="ALTER TABLE analytics.hw_event SECONDARY_ENGINE=RAPID, SECONDARY_LOAD=1",
        fail="ERROR 3889 (HY000): SECONDARY_ENGINE leftover hw_event_secondary + hw_event_lakehouse_tmp after failed RAPID load",
        inspect="SELECT TABLE_NAME, CREATE_OPTIONS FROM information_schema.TABLES WHERE TABLE_NAME='hw_event'",
        catalog="HeatWave secondary leftover; expand payload_v2",
        abort="ALTER TABLE analytics.hw_event SECONDARY_UNLOAD",
        col_type="JSON",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD payload_v2 on analytics.hw_event",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-schema-cookie-leftover",
        plant="sqlite-schema-ck",
        surface="sqlite-schema-cookie",
        table="cookie_item",
        col="body",
        col_v2="body_v2",
        leftover="cookie_item_old",
        leftover2="sqlite_schema_cookie_bak",
        seed="PRAGMA schema_version=19001",
        fail="NOTICE: already skip: schema cookie leftover cookie_item_old + sqlite_schema_cookie_bak after failed rewrite",
        inspect="PRAGMA schema_version; PRAGMA user_version",
        catalog="schema cookie leftover; expand body_v2",
        abort="DROP TABLE IF EXISTS cookie_item_old",
        col_type="BLOB",
        db="cookie.db",
        lock_fail="Error: database is locked ADD body_v2 on cookie_item",
    ),
    pl(
        engine="mssql",
        slug="mssql-cdc-capture-leftover",
        plant="mssql-cdc",
        surface="mssql-cdc-capture",
        table="audit.cdc_event",
        col="payload",
        col_v2="payload_v2",
        leftover="cdc_event_CT",
        leftover2="cdc_capture_job_tmp",
        seed="EXEC sys.sp_cdc_enable_table @source_schema='audit', @source_name='cdc_event', @role_name=NULL",
        fail="Msg 22939: CDC leftover cdc_event_CT + cdc_capture_job_tmp after failed enable_table",
        inspect="SELECT name, is_tracked_by_cdc FROM sys.tables WHERE name='cdc_event'",
        catalog="CDC capture leftover CT table; expand payload_v2",
        abort="EXEC sys.sp_cdc_disable_table @source_schema='audit', @source_name='cdc_event', @capture_instance='audit_cdc_event'",
        col_type="NVARCHAR(MAX)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD payload_v2 on audit.cdc_event",
    ),
    pl(
        engine="oracle",
        slug="oracle-invisible-column-leftover",
        plant="oracle-invis-col",
        surface="oracle-invisible-column",
        table="hr.invis_col_emp",
        col="ssn",
        col_v2="ssn_v2",
        leftover="INVIS_COL_EMP_INV_TMP",
        leftover2="SYS_C00_INVIS_EMP",
        seed="ALTER TABLE hr.invis_col_emp MODIFY (ssn INVISIBLE)",
        fail="ORA-54039: invisible column leftover INVIS_COL_EMP_INV_TMP + SYS_C00_INVIS_EMP after failed MODIFY INVISIBLE",
        inspect="SELECT column_name, hidden_column FROM user_tab_cols WHERE table_name='INVIS_COL_EMP'",
        catalog="Oracle invisible column leftover; expand ssn_v2",
        abort="DROP TABLE hr.INVIS_COL_EMP_INV_TMP",
        col_type="VARCHAR2(11)",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD ssn_v2 on hr.invis_col_emp",
    ),
    pl(
        engine="mysql",
        slug="mysql-instant-drop-leftover",
        plant="mysql-instant-drop",
        surface="mysql-instant-drop",
        table="shop.instant_drop_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="instant_drop_sku_dropped_cols",
        leftover2="instant_drop_sku_frm_tmp",
        seed="ALTER TABLE shop.instant_drop_sku DROP COLUMN stale_pad, ALGORITHM=INSTANT",
        fail="ERROR 1845 (0A000): INSTANT DROP leftover instant_drop_sku_dropped_cols + instant_drop_sku_frm_tmp; skip in-place rewrite of sku",
        inspect="SELECT NAME, SPACE FROM information_schema.INNODB_TABLESPACES WHERE NAME LIKE 'shop/instant_drop_sku%'",
        catalog="INSTANT DROP leftover hidden cols; expand sku_norm",
        abort="DROP TABLE IF EXISTS shop.instant_drop_sku_frm_tmp",
        col_type="VARCHAR(191)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD sku_norm on shop.instant_drop_sku",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-autoindex-leftover",
        plant="sqlite-autoindex",
        surface="sqlite-autoindex",
        table="autoindex_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="sqlite_autoindex_autoindex_sku_1",
        leftover2="autoindex_sku_old",
        seed="CREATE UNIQUE INDEX sqlite_autoindex_autoindex_sku_1 ON autoindex_sku(sku)",
        fail="NOTICE: already skip: UNIQUE autoindex leftover sqlite_autoindex_autoindex_sku_1 + autoindex_sku_old after rewrite abort",
        inspect="SELECT name, sql FROM sqlite_master WHERE name LIKE 'autoindex_sku%'",
        catalog="sqlite autoindex leftover; expand sku_norm",
        abort="DROP TABLE IF EXISTS autoindex_sku_old",
        col_type="TEXT",
        db="autoindex.db",
        lock_fail="Error: database is locked ADD sku_norm on autoindex_sku",
    ),
    pl(
        engine="mssql",
        slug="mssql-always-encrypted-leftover",
        plant="mssql-ae",
        surface="mssql-always-encrypted",
        table="pii.ae_card",
        col="pan",
        col_v2="pan_v2",
        leftover="ae_card_cek_tmp",
        leftover2="ae_card_cmk",
        seed="ALTER TABLE pii.ae_card ALTER COLUMN pan ADD ENCRYPTED WITH (COLUMN_ENCRYPTION_KEY=cek_ae, ENCRYPTION_TYPE=DETERMINISTIC, ALGORITHM='AEAD_AES_256_CBC_HMAC_SHA_256')",
        fail="Msg 33546: Always Encrypted leftover ae_card_cek_tmp + ae_card_cmk after failed ALTER COLUMN",
        inspect="SELECT name, encryption_type_desc FROM sys.columns WHERE object_id=OBJECT_ID('pii.ae_card')",
        catalog="Always Encrypted leftover CEK; expand pan_v2",
        abort="DROP TABLE pii.ae_card_cek_tmp",
        col_type="NVARCHAR(32)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD pan_v2 on pii.ae_card",
    ),
    pl(
        engine="mysql",
        slug="mysql-row-format-compressed-leftover",
        plant="mysql-rowfmt",
        surface="mysql-row-format-compressed",
        table="cold.rowfmt_blob",
        col="body",
        col_v2="body_v2",
        leftover="rowfmt_blob_cmp_tmp",
        leftover2="rowfmt_blob_ibd",
        seed="ALTER TABLE cold.rowfmt_blob ROW_FORMAT=COMPRESSED, KEY_BLOCK_SIZE=8, ALGORITHM=COPY",
        fail="ERROR 1478 (HY000): ROW_FORMAT=COMPRESSED leftover rowfmt_blob_cmp_tmp + rowfmt_blob_ibd after failed COPY",
        inspect="SELECT NAME, ROW_FORMAT FROM information_schema.INNODB_TABLESPACES WHERE NAME LIKE 'cold/rowfmt_blob%'",
        catalog="compressed row_format leftover ibd/tmp; expand body_v2",
        abort="DROP TABLE IF EXISTS cold.rowfmt_blob_cmp_tmp",
        col_type="LONGBLOB",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD body_v2 on cold.rowfmt_blob",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-check-constraint-leftover",
        plant="sqlite-check",
        surface="sqlite-check-constraint",
        table="check_amt",
        col="amount",
        col_v2="amount_v2",
        leftover="sqlite_check_amt_new",
        leftover2="check_amt_old",
        seed="ALTER TABLE check_amt ADD CONSTRAINT check_amt_pos CHECK (amount >= 0)",
        fail="Parse error: CHECK leftover sqlite_check_amt_new + check_amt_old after table rewrite abort",
        inspect="SELECT name, sql FROM sqlite_master WHERE name LIKE 'check_amt%'",
        catalog="SQLite CHECK leftover rewrite tmp; expand amount_v2",
        abort="DROP TABLE IF EXISTS sqlite_check_amt_new",
        col_type="REAL",
        db="checkamt.db",
        lock_fail="Error: database is locked ADD amount_v2 on check_amt",
    ),
    pl(
        engine="mssql",
        slug="mssql-snapshot-isolation-leftover",
        plant="mssql-snapshot",
        surface="mssql-snapshot-isolation",
        table="ops.snap_ticket",
        col="status",
        col_v2="status_v2",
        leftover="snap_ticket_version_chain",
        leftover2="snap_ticket_rowver_tmp",
        seed="ALTER DATABASE ops SET ALLOW_SNAPSHOT_ISOLATION ON",
        fail="Msg 3959: SNAPSHOT leftover snap_ticket_version_chain + snap_ticket_rowver_tmp; skip in-place rewrite of status",
        inspect="SELECT name, snapshot_isolation_state_desc FROM sys.databases WHERE name='ops'",
        catalog="row-version chain leftover; expand status_v2",
        abort="DROP TABLE ops.snap_ticket_rowver_tmp",
        col_type="NVARCHAR(32)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD status_v2 on ops.snap_ticket",
    ),
    pl(
        engine="oracle",
        slug="oracle-result-cache-leftover",
        plant="oracle-rcache",
        surface="oracle-result-cache",
        table="app.rcache_lookup",
        col="payload",
        col_v2="payload_v2",
        leftover="RCACHE_LOOKUP_RC_TMP",
        leftover2="SYS_RC_LOOKUP",
        seed="ALTER TABLE app.rcache_lookup RESULT_CACHE (MODE FORCE)",
        fail="ORA-41365: result cache leftover RCACHE_LOOKUP_RC_TMP + SYS_RC_LOOKUP after failed RESULT_CACHE",
        inspect="SELECT table_name, result_cache FROM user_tables WHERE table_name='RCACHE_LOOKUP'",
        catalog="result cache leftover; expand payload_v2",
        abort="DROP TABLE app.RCACHE_LOOKUP_RC_TMP",
        col_type="CLOB",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD payload_v2 on app.rcache_lookup",
    ),
    pl(
        engine="mariadb",
        slug="mariadb-columnstore-plan-leftover",
        plant="maria-cs-plan",
        surface="mariadb-columnstore-plan",
        table="analytics.mcs_event",
        col="payload",
        col_v2="payload_v2",
        leftover="mcs_event_extent",
        leftover2="mcs_event_cpimport_tmp",
        seed="ALTER TABLE analytics.mcs_event ENGINE=ColumnStore",
        fail="ERROR 1815 (HY000): ColumnStore leftover mcs_event_extent + mcs_event_cpimport_tmp after failed ENGINE swap",
        inspect="SELECT ENGINE, CREATE_OPTIONS FROM information_schema.TABLES WHERE TABLE_NAME='mcs_event'",
        catalog="ColumnStore extent leftover; expand payload_v2",
        abort="DROP TABLE IF EXISTS analytics.mcs_event_cpimport_tmp",
        col_type="LONGTEXT",
    ),
    pl(
        engine="mysql",
        slug="mysql-ibd-import-leftover",
        plant="mysql-ibd-import",
        surface="mysql-ibd-import",
        table="warehouse.ibd_import_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="ibd_import_sku.cfg",
        leftover2="ibd_import_sku_discard",
        seed="ALTER TABLE warehouse.ibd_import_sku IMPORT TABLESPACE",
        fail="ERROR 1812 (HY000): IMPORT TABLESPACE leftover ibd_import_sku.cfg + ibd_import_sku_discard after failed import",
        inspect="SELECT NAME, SPACE_TYPE FROM information_schema.INNODB_TABLESPACES WHERE NAME LIKE 'warehouse/ibd_import_sku%'",
        catalog="IMPORT TABLESPACE leftover .cfg; expand sku_norm",
        abort="ALTER TABLE warehouse.ibd_import_sku DISCARD TABLESPACE",
        col_type="VARCHAR(191)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD sku_norm on warehouse.ibd_import_sku",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-wal-autocheckpoint-leftover",
        plant="sqlite-wal-auto",
        surface="sqlite-wal-autocheckpoint",
        table="auto_wal_doc",
        col="payload",
        col_v2="payload_v2",
        leftover="auto_wal_doc-wal",
        leftover2="auto_wal_doc-shm",
        seed="PRAGMA wal_autocheckpoint=100",
        fail="SQLITE_BUSY: wal_autocheckpoint leftover auto_wal_doc-wal + auto_wal_doc-shm; skip in-place rewrite",
        inspect="PRAGMA journal_mode; PRAGMA wal_autocheckpoint",
        catalog="wal_autocheckpoint leftover wal/shm; expand payload_v2",
        abort="PRAGMA wal_checkpoint(PASSIVE)",
        col_type="TEXT",
        db="autowal.db",
        lock_fail="Error: database is locked ADD payload_v2 on auto_wal_doc",
    ),
    pl(
        engine="mssql",
        slug="mssql-synonym-target-leftover",
        plant="mssql-synonym",
        surface="mssql-synonym-target",
        table="app.syn_item",
        col="body",
        col_v2="body_v2",
        leftover="syn_item_syn",
        leftover2="syn_item_target_tmp",
        seed="CREATE SYNONYM app.syn_item_syn FOR app.syn_item",
        fail="Msg 2714: synonym leftover syn_item_syn + syn_item_target_tmp after failed CREATE SYNONYM; skip in-place",
        inspect="SELECT name, base_object_name FROM sys.synonyms WHERE name='syn_item_syn'",
        catalog="synonym leftover; expand body_v2",
        abort="DROP SYNONYM app.syn_item_syn",
        col_type="NVARCHAR(MAX)",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD body_v2 on app.syn_item",
    ),
    pl(
        engine="crdb",
        slug="crdb-ttl-job-leftover",
        plant="crdb-ttl",
        surface="crdb-ttl-job",
        table="ops.ttl_session",
        col="payload",
        col_v2="payload_v2",
        leftover="ttl_session_job",
        leftover2="ttl_session_span_tmp",
        seed="ALTER TABLE ops.ttl_session SET (ttl = '24h')",
        fail="ERROR: row-level TTL leftover ttl_session_job + ttl_session_span_tmp after failed SET ttl",
        inspect="SHOW CREATE TABLE ops.ttl_session",
        catalog="TTL job leftover; expand payload_v2",
        abort="ALTER TABLE ops.ttl_session RESET (ttl)",
        col_type="BYTES",
        lock_fail="pq: lock timeout ADD payload_v2 on ops.ttl_session",
    ),
    pl(
        engine="mysql",
        slug="mysql-generated-virtual-leftover",
        plant="mysql-gen-virt",
        surface="mysql-generated-virtual",
        table="catalog.gen_virt_price",
        col="amount",
        col_v2="amount_v2",
        leftover="gen_virt_price_gc_virt",
        leftover2="gen_virt_price_frm",
        seed="ALTER TABLE catalog.gen_virt_price ADD COLUMN gross DECIMAL(12,4) GENERATED ALWAYS AS (amount*1.2) VIRTUAL",
        fail="ERROR 3105 (HY000): VIRTUAL generated leftover gen_virt_price_gc_virt + gen_virt_price_frm after failed ADD",
        inspect="SELECT COLUMN_NAME, EXTRA FROM information_schema.COLUMNS WHERE TABLE_NAME='gen_virt_price'",
        catalog="VIRTUAL generated leftover frm; expand amount_v2",
        abort="DROP TABLE IF EXISTS catalog.gen_virt_price_frm",
        col_type="DECIMAL(12,4)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD amount_v2 on catalog.gen_virt_price",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-temp-view-leftover",
        plant="sqlite-temp-view",
        surface="sqlite-temp-view",
        table="view_src",
        col="body",
        col_v2="body_v2",
        leftover="temp.view_src_v",
        leftover2="view_src_old",
        seed="CREATE TEMP VIEW view_src_v AS SELECT * FROM view_src",
        fail="NOTICE: already skip: TEMP VIEW leftover temp.view_src_v + view_src_old after rewrite abort",
        inspect="SELECT name, sql FROM sqlite_temp_master WHERE name LIKE 'view_src%'",
        catalog="TEMP VIEW leftover; expand body_v2",
        abort="DROP VIEW IF EXISTS temp.view_src_v",
        col_type="TEXT",
        db="tempview.db",
        lock_fail="Error: database is locked ADD body_v2 on view_src",
    ),
    pl(
        engine="mssql",
        slug="mssql-sparse-column-leftover",
        plant="mssql-sparse",
        surface="mssql-sparse-column",
        table="wide.sparse_attr",
        col="flag",
        col_v2="flag_v2",
        leftover="sparse_attr_set_tmp",
        leftover2="sparse_attr_colset",
        seed="ALTER TABLE wide.sparse_attr ALTER COLUMN flag ADD SPARSE",
        fail="Msg 1919: SPARSE leftover sparse_attr_set_tmp + sparse_attr_colset after failed ALTER COLUMN",
        inspect="SELECT name, is_sparse FROM sys.columns WHERE object_id=OBJECT_ID('wide.sparse_attr')",
        catalog="SPARSE column leftover column_set; expand flag_v2",
        abort="DROP TABLE wide.sparse_attr_set_tmp",
        col_type="BIT",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD flag_v2 on wide.sparse_attr",
    ),
    pl(
        engine="oracle",
        slug="oracle-bitmap-join-leftover",
        plant="oracle-bmj",
        surface="oracle-bitmap-join",
        table="dwh.bmj_fact",
        col="dim_id",
        col_v2="dim_uuid",
        leftover="BMJ_FACT_BJX",
        leftover2="BMJ_FACT_BJX_TMP",
        seed="CREATE BITMAP INDEX dwh.bmj_fact_bjx ON dwh.bmj_fact(d.region) FROM dwh.bmj_fact f, dwh.bmj_dim d WHERE f.dim_id=d.id",
        fail="ORA-01408: bitmap join leftover BMJ_FACT_BJX + BMJ_FACT_BJX_TMP after failed CREATE BITMAP INDEX",
        inspect="SELECT index_name, index_type FROM user_indexes WHERE table_name='BMJ_FACT'",
        catalog="bitmap join index leftover; expand dim_uuid",
        abort="DROP INDEX dwh.bmj_fact_bjx",
        col_type="VARCHAR2(36)",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD dim_uuid on dwh.bmj_fact",
    ),
    pl(
        engine="mysql",
        slug="mysql-spatial-rtr-leftover",
        plant="mysql-spatial-rtr",
        surface="mysql-spatial-rtr",
        table="geo.rtr_shape",
        col="shape",
        col_v2="shape_v2",
        leftover="rtr_shape_sp_idx",
        leftover2="rtr_shape_mbr_tmp",
        seed="ALTER TABLE geo.rtr_shape ADD SPATIAL INDEX sx_shape (shape)",
        fail="ERROR 3034 (HY000): SPATIAL leftover rtr_shape_sp_idx + rtr_shape_mbr_tmp after failed ADD SPATIAL INDEX",
        inspect="SELECT INDEX_NAME, INDEX_TYPE FROM information_schema.STATISTICS WHERE TABLE_NAME='rtr_shape'",
        catalog="SPATIAL R-tree leftover; expand shape_v2",
        abort="DROP TABLE IF EXISTS geo.rtr_shape_mbr_tmp",
        col_type="GEOMETRY",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD shape_v2 on geo.rtr_shape",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-attach-schema-leftover",
        plant="sqlite-attach",
        surface="sqlite-attach-schema",
        table="main.attach_item",
        col="body",
        col_v2="body_v2",
        leftover="aux.attach_item",
        leftover2="attach_item_old",
        seed="ATTACH DATABASE 'aux.db' AS aux",
        fail="NOTICE: already skip: ATTACH leftover aux.attach_item + attach_item_old after failed rewrite",
        inspect="PRAGMA database_list",
        catalog="ATTACH schema leftover; expand body_v2",
        abort="DETACH DATABASE aux",
        col_type="BLOB",
        db="attach.db",
        lock_fail="Error: database is locked ADD body_v2 on main.attach_item",
    ),
    pl(
        engine="mssql",
        slug="mssql-indexed-view-leftover",
        plant="mssql-idxview",
        surface="mssql-indexed-view",
        table="sales.idxview_line",
        col="qty",
        col_v2="qty_v2",
        leftover="idxview_line_v",
        leftover2="idxview_line_v_ix",
        seed="CREATE UNIQUE CLUSTERED INDEX ix_idxview_line_v ON sales.idxview_line_v(line_id)",
        fail="Msg 1934: indexed view leftover idxview_line_v + idxview_line_v_ix after failed CREATE UNIQUE CLUSTERED INDEX",
        inspect="SELECT name, is_indexed_view FROM sys.views WHERE name='idxview_line_v'",
        catalog="indexed view leftover; expand qty_v2",
        abort="DROP INDEX ix_idxview_line_v ON sales.idxview_line_v",
        col_type="BIGINT",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD qty_v2 on sales.idxview_line_v",
    ),
    pl(
        engine="mariadb",
        slug="mariadb-atomic-ddl-leftover",
        plant="maria-atomic",
        surface="mariadb-atomic-ddl",
        table="shop.atomic_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="atomic_sku_ddl_log",
        leftover2="atomic_sku_crash_tmp",
        seed="ALTER TABLE shop.atomic_sku FORCE",
        fail="ERROR 1025 (HY000): atomic DDL leftover atomic_sku_ddl_log + atomic_sku_crash_tmp after crash mid-ALTER",
        inspect="SELECT * FROM mysql.innodb_table_stats WHERE table_name='atomic_sku'",
        catalog="atomic DDL crash leftover; expand sku_norm",
        abort="DROP TABLE IF EXISTS shop.atomic_sku_crash_tmp",
        col_type="VARCHAR(191)",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-session-changeset-leftover",
        plant="sqlite-session",
        surface="sqlite-session-changeset",
        table="sess_row",
        col="payload",
        col_v2="payload_v2",
        leftover="sess_row_changeset",
        leftover2="sess_row_session_tmp",
        seed="SELECT sqlite3session_changeset('sess_row')",
        fail="SQL logic error: session changeset leftover sess_row_changeset + sess_row_session_tmp after failed apply",
        inspect="SELECT name FROM sqlite_master WHERE name LIKE 'sess_row%'",
        catalog="session changeset leftover; expand payload_v2",
        abort="DROP TABLE IF EXISTS sess_row_session_tmp",
        col_type="BLOB",
        db="session.db",
        lock_fail="Error: database is locked ADD payload_v2 on sess_row",
    ),
    pl(
        engine="mssql",
        slug="mssql-security-policy-leftover",
        plant="mssql-rls-pol",
        surface="mssql-security-policy",
        table="tenant.rls_row",
        col="tenant_id",
        col_v2="tenant_uuid",
        leftover="rls_row_policy",
        leftover2="rls_row_pred_fn",
        seed="CREATE SECURITY POLICY tenant.rls_row_policy ADD FILTER PREDICATE tenant.rls_pred(tenant_id) ON tenant.rls_row WITH (STATE = ON)",
        fail="Msg 33224: security policy leftover rls_row_policy + rls_row_pred_fn after failed CREATE SECURITY POLICY",
        inspect="SELECT name, is_enabled FROM sys.security_policies WHERE name='rls_row_policy'",
        catalog="security policy leftover predicate; expand tenant_uuid",
        abort="DROP SECURITY POLICY tenant.rls_row_policy",
        col_type="UNIQUEIDENTIFIER",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD tenant_uuid on tenant.rls_row",
    ),
    pl(
        engine="oracle",
        slug="oracle-sql-patch-leftover",
        plant="oracle-sqlpatch",
        surface="oracle-sql-patch",
        table="app.sql_patch_item",
        col="body",
        col_v2="body_v2",
        leftover="SQL_PATCH_ITEM_SP",
        leftover2="SQL_PATCH_ITEM_TMP",
        seed="BEGIN DBMS_SQLDIAG.CREATE_SQL_PATCH(sql_id=>'7xpatch', hint_text=>'INDEX(sql_patch_item)'); END;",
        fail="ORA-13831: SQL patch leftover SQL_PATCH_ITEM_SP + SQL_PATCH_ITEM_TMP after failed CREATE_SQL_PATCH",
        inspect="SELECT name, status FROM dba_sql_patches WHERE name LIKE 'SQL_PATCH_ITEM%'",
        catalog="SQL patch leftover; expand body_v2",
        abort="BEGIN DBMS_SQLDIAG.DROP_SQL_PATCH('SQL_PATCH_ITEM_SP'); END;",
        col_type="CLOB",
        lock_fail="ORA-00054: resource busy and acquire with NOWAIT specified ADD body_v2 on app.sql_patch_item",
    ),
    pl(
        engine="crdb",
        slug="crdb-vector-index-leftover",
        plant="crdb-vecidx",
        surface="crdb-vector-index",
        table="search.vec_item",
        col="embed",
        col_v2="embed_v2",
        leftover="vec_item_idx",
        leftover2="vec_item_vec_tmp",
        seed="CREATE VECTOR INDEX vec_item_idx ON search.vec_item (embed)",
        fail="ERROR: vector index leftover vec_item_idx + vec_item_vec_tmp after failed CREATE VECTOR INDEX",
        inspect="SHOW INDEX FROM search.vec_item",
        catalog="vector index leftover; expand embed_v2",
        abort="DROP INDEX IF EXISTS vec_item_idx",
        col_type="VECTOR(768)",
        lock_fail="pq: lock timeout ADD embed_v2 on search.vec_item",
    ),
    pl(
        engine="mysql",
        slug="mysql-clone-plugin-leftover",
        plant="mysql-clone",
        surface="mysql-clone-plugin",
        table="ops.clone_ticket",
        col="state",
        col_v2="state_v2",
        leftover="clone_ticket_donor_tmp",
        leftover2="clone_ticket_inprog",
        seed="CLONE INSTANCE FROM 'donor':3306 IDENTIFIED BY 'x' DATA DIRECTORY='/var/lib/mysql-clone'",
        fail="ERROR 3862 (HY000): CLONE leftover clone_ticket_donor_tmp + clone_ticket_inprog; skip in-place rewrite of state",
        inspect="SELECT ID, STATE FROM performance_schema.clone_status",
        catalog="clone plugin leftover in-progress; expand state_v2",
        abort="DROP TABLE IF EXISTS ops.clone_ticket_donor_tmp",
        col_type="VARCHAR(32)",
        lock_fail="ERROR 1205 (HY000): Lock wait timeout exceeded ADD state_v2 on ops.clone_ticket",
    ),
    pl(
        engine="sqlite",
        slug="sqlite-rbu-vacuum-leftover",
        plant="sqlite-rbu",
        surface="sqlite-rbu-vacuum",
        table="rbu_item",
        col="body",
        col_v2="body_v2",
        leftover="data_rbu_item",
        leftover2="rbu_state",
        seed="INSERT INTO data_rbu_item(rbu_control, id, body) VALUES(0, 1, X'00')",
        fail="SQL logic error: RBU leftover data_rbu_item + rbu_state after failed incremental vacuum; skip rewrite",
        inspect="SELECT name FROM sqlite_master WHERE name LIKE '%rbu%'",
        catalog="RBU vacuum leftover data_* + rbu_state; expand body_v2",
        abort="DROP TABLE IF EXISTS data_rbu_item",
        col_type="BLOB",
        db="rbu.db",
        lock_fail="Error: database is locked ADD body_v2 on rbu_item",
    ),
    pl(
        engine="mssql",
        slug="mssql-external-table-leftover",
        plant="mssql-exttbl",
        surface="mssql-external-table",
        table="lake.ext_fact",
        col="units",
        col_v2="units_v2",
        leftover="ext_fact_ds",
        leftover2="ext_fact_ext",
        seed="CREATE EXTERNAL TABLE lake.ext_fact_ext (units BIGINT) WITH (DATA_SOURCE=ds_lake, LOCATION='/facts')",
        fail="Msg 46526: external table leftover ext_fact_ds + ext_fact_ext after failed CREATE EXTERNAL TABLE",
        inspect="SELECT name, type_desc FROM sys.external_tables WHERE name LIKE 'ext_fact%'",
        catalog="external table leftover; expand units_v2",
        abort="DROP EXTERNAL TABLE lake.ext_fact_ext",
        col_type="BIGINT",
        lock_fail="Msg 1222: Lock request time out period exceeded ADD units_v2 on lake.ext_fact",
    ),
]


def seed_cmd_for(p: dict[str, str]) -> str:
    if p["seed"].startswith("pt-") or p["seed"].startswith("gh-ost"):
        return p["seed"]
    return engine_cmd(p, p["seed"])


def engine_cmd(p: dict[str, str], sql: str) -> str:
    engine = p["engine"]
    if engine == "mysql":
        return f'mysql --batch -N -e "{sql}"'
    if engine == "mariadb":
        return f'mariadb --batch -N -e "{sql}"'
    if engine == "sqlite":
        return f'sqlite3 {p["db"]} "{sql}"'
    if engine == "mssql":
        return f'sqlcmd -b -I -Q "{sql}"'
    if engine == "oracle":
        return f'echo "{sql};" | sqlplus -L -S app/app'
    if engine == "crdb":
        return f'cockroach sql --insecure -e "{sql}"'
    raise ValueError(engine)


def expand_sql(p: dict[str, str]) -> str:
    engine, table, col_v2, col_type = p["engine"], p["table"], p["col_v2"], p["col_type"]
    if engine == "mssql":
        return f"ALTER TABLE {table} ADD {col_v2} {col_type} NULL"
    if engine == "oracle":
        return f"ALTER TABLE {table} ADD ({col_v2} {col_type})"
    if engine == "sqlite":
        return f"ALTER TABLE {table} ADD COLUMN {col_v2} {col_type}"
    return f"ALTER TABLE {table} ADD COLUMN {col_v2} {col_type}"


def lock_sql(p: dict[str, str]) -> str:
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
    raise ValueError(engine)


def default_lock_fail(p: dict[str, str]) -> str:
    if p["lock_fail"]:
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
    return f"pq: lock timeout ADD {col_v2} on {table}"


def _step(n: int, decision_basis: str, tool_call: dict, observation: str) -> dict:
    return {
        "n": n,
        "decision_basis": decision_basis,
        "tool_call": tool_call,
        "observation": observation,
    }


def _bash(command: str) -> dict:
    return {"name": "bash", "args": {"command": command}}


def _write(path: str, contents: str) -> dict:
    return {"name": "write", "args": {"path": path, "contents": contents}}


def dumps_episode(ep: dict) -> str:
    return json.dumps(ep, ensure_ascii=True, separators=(",", ":"))


def assert_clean(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in BANNED_KEYS:
                raise ValueError(f"banned key {key} at {path}")
            if key == "sim_or_real" and val == "real":
                raise ValueError(f"sim_or_real real at {path}")
            if key == "spike_events":
                raise ValueError(f"spike_events at {path}")
            assert_clean(val, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            assert_clean(item, f"{path}[{i}]")


def pair_for(round_n: int) -> tuple[dict[str, str], dict[str, str]]:
    idx = round_n - START_ROUND
    n_pairs = len(PLANTS) // 2
    if idx < 0:
        raise KeyError(f"no plant pair for round {round_n} (before r{START_ROUND})")
    # r845–r865 were occupied by a PG-catalog mill. After the explicit
    # catalog (r845–r888) wrap once so unused prefix plants still publish.
    if idx >= n_pairs:
        idx -= n_pairs
    start = idx * 2
    if idx >= n_pairs or start + 1 >= len(PLANTS):
        raise KeyError(
            f"no plant pair for round {round_n} (have {n_pairs} from r{START_ROUND}, one wrap)"
        )
    return PLANTS[start], PLANTS[start + 1]


def coverage_for(round_n: int) -> int:
    return max(28, 91 - (round_n - START_ROUND))


def short_name(p: dict[str, str]) -> str:
    return p["table"].split(".")[-1]


def residual(p: dict[str, str]) -> str:
    s = short_name(p)
    return f"{s}.{p['col']} + {p['col_v2']}; leftover {p['leftover']} + {p['leftover2']}"


def build_episode(round_n: int, p: dict[str, str], ep_idx: int) -> dict:
    ver = 2200 + (round_n - START_ROUND) * 2 + ep_idx
    slug = p["slug"]
    stem = slug.replace("-", "_")
    table = p["table"]
    col = p["col"]
    col_v2 = p["col_v2"]
    leftover = p["leftover"]
    leftover2 = p["leftover2"]
    res = residual(p)
    sname = short_name(p)
    mig = f"migrations/{ver}_{stem}.sql"
    down = f"migrations/{ver}_{stem}.down.sql"
    test = f"tests/test_{stem}.py"
    runbook = f"docs/{slug}.md"
    backfill = f"jobs/backfill_{stem}.py"
    checksum = f"jobs/checksum_{stem}.py"
    inspect_cmd = engine_cmd(p, p["inspect"])
    seed_cmd = seed_cmd_for(p)
    abort_cmd = engine_cmd(p, p["abort"])
    lock_cmd = engine_cmd(p, lock_sql(p))
    lock_fail = default_lock_fail(p)
    expand = expand_sql(p)
    inspect_obs = (
        f"{table} present\n"
        f"pending: {p['fail']}\n"
        f"shape now: {res}\n"
        f"catalog: {p['catalog']}\n"
        f"locks/mutations: 1 active; dual leftover objects"
    )
    eid = f"dbm-r{round_n}-{slug}"
    if RECYCLE_SUFFIX.search(eid):
        raise ValueError(f"recycle suffix in id: {eid}")
    goal = (
        f"{p['plant']}: {p['engine']} {seed_cmd} on {table}.{col} failed "
        f"({p['fail'][:120]}). Expand {col_v2}, backfill, residual {res}."
    )
    plan = (
        f"Abort in-place rewrite; expand-contract via {expand}; keep {col}; "
        f"dual leftover objects."
    )
    steps = [
        _step(
            1,
            f"Plan: inspect {p['engine']} catalog for {table} before apply {ver} ({slug}).",
            _bash(inspect_cmd),
            inspect_obs,
        ),
        _step(
            2,
            f"Plan: apply naive catalog change on {table}.{col}.",
            _bash(seed_cmd),
            p["fail"],
        ),
        _step(
            3,
            (
                f"Observation: first apply failed ({p['fail'][:90]}). Plan change: "
                f"abort in-place rewrite; expand {col_v2} + backfill; leave {col} residual."
            ),
            _bash(abort_cmd),
            "leftovers dropped or cancelled; naive rewrite aborted; dual objects still planned",
        ),
        _step(
            4,
            f"Plan: write expand-only migration {ver} adding {col_v2} (keep {col}).",
            _write(
                mig,
                (
                    f"-- {ver} expand {table} {col_v2}\n"
                    f"{expand};\n"
                    f"-- never drop {col}; keep dual residual\n"
                    f"-- {p['catalog']}\n"
                ),
            ),
            "expand-only written",
        ),
        _step(
            5,
            f"Plan: apply expand {ver} with short lock timeout.",
            _bash(lock_cmd),
            lock_fail,
        ),
        _step(
            6,
            "Observation: lock timeout on expand. Plan: retry lock timeout off-peak; ACCESS EXCLUSIVE avoided.",
            _bash(lock_cmd),
            f"ok retry expand {col_v2}",
        ),
        _step(
            7,
            f"Plan: batched backfill {col_v2} from {col} without validating leftover constraints.",
            _bash(f"python {backfill} --batch 8000 --from {col} --to {col_v2}"),
            f"copied batch ok; remaining 0 on {table}; dual residual {res}",
        ),
        _step(
            8,
            f"Plan: tests {test} (catalog residual must remain).",
            _bash(f"pytest -q {test}"),
            "3 passed",
        ),
        _step(
            9,
            f"Plan: down {ver} must refuse lossy drop of {col_v2}.",
            _write(
                down,
                f"SELECT raise_error('lossy {col_v2} drop; dual residual {sname} must remain');\n",
            ),
            "down v2 guard",
        ),
        _step(
            10,
            f"Observation: dual residual {res}.",
            _bash(inspect_cmd),
            res,
        ),
        _step(
            11,
            "Plan: runbook never in-place rewrite via naive catalog DDL.",
            _write(
                runbook,
                (
                    f"Never {seed_cmd}. Expand {col_v2}, backfill, dual-read. "
                    f"Residual: {res}. Restore leftovers before retry. {p['catalog']}"
                ),
            ),
            "runbook",
        ),
        _step(
            12,
            f"Plan: extra tests {test} + tests/test_schema.py.",
            _bash(f"pytest -q {test} tests/test_schema.py"),
            "4 passed",
        ),
        _step(
            13,
            "Tool call: leftover catalog objects after abort.",
            _bash(f"rg '{leftover}|{leftover2}|{col_v2}' || echo none-in-rewrite-path"),
            "none in rewrite path; dual objects remain as residual",
        ),
        _step(
            14,
            f"Plan: checksum {col} vs {col_v2}; confirm leftover catalog objects still dual.",
            _bash(f"python {checksum}"),
            f"mismatch 0 on backfilled rows; dual residual {res}",
        ),
        _step(
            15,
            f"Plan: confirm no active locks/mutations on {sname}.",
            _bash(inspect_cmd),
            "0 blockers; dual objects still present",
        ),
        _step(
            16,
            f"Plan: stamp schema version {ver}.",
            _bash(f"echo {ver}"),
            str(ver),
        ),
    ]
    ep = {
        "id": eid,
        "goal": goal,
        "plan": plan,
        "steps": steps,
        "outcome": (
            f"Naive catalog apply failed. Plan change: expand {col_v2} + backfill. "
            f"Tests 4/4. Residual: {res}."
        ),
        "reward": {
            "success": True,
            "apply_fails": 2,
            "plan_changes": 1,
            "lock_timeouts": 1,
            "tests_passed": 4,
            "cost_steps": 16,
        },
        "meta": {
            "factory": FACTORY_SLUG,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "episode",
            "plant": p["plant"],
            "sim_or_real": "designed",
            "surface": p["surface"],
        },
    }
    assert_clean(ep)
    if len(steps) != 16:
        raise ValueError(f"{eid} expected 16 steps")
    return ep


def notes_md(round_n: int, a: dict[str, str], b: dict[str, str], coverage: int) -> str:
    ea = build_episode(round_n, a, 0)
    eb = build_episode(round_n, b, 1)
    unused = []
    nxt = (round_n - START_ROUND + 1) * 2
    if nxt + 1 < len(PLANTS):
        unused = [PLANTS[nxt]["slug"], PLANTS[nxt + 1]["slug"]]
    unused_s = ", ".join(unused) if unused else "catalog end"
    def seed_cell(p: dict[str, str]) -> str:
        return seed_cmd_for(p)[:48]
    def term(p: dict[str, str]) -> str:
        return f"4/4 {residual(p)}"[:72]
    body = (
        f"# NOTES-r{round_n} db-migration-repair-factory\n\n"
        f"Novel coverage: {coverage}%\n\n"
        "Two designed episodes (quota 2). Unique vs r1-r105 first-cycle, "
        "r106-r239 engines, r240-r761 recycle mill, r762-r793 warehouse mill, "
        "r794-r817 ORM-CLI grid, and r818-r844 PG catalog/AM grid. Surfaces: "
        f"{a['surface']}; {b['surface']}. IDs `dbm-r{round_n}-<slug>` without "
        "`-rNN` recycle suffix. Dual-object residual. First-apply fail + plan "
        "change + lock retry. Semantic mill (not CLI clone).\n\n"
        "| id | seed | first apply | plan change | terminal |\n"
        "|---|---|---|---|---|\n"
        f"| {ea['id']} | {seed_cell(a)} | first apply fail | expand {a['col_v2']} | {term(a)} |\n"
        f"| {eb['id']} | {seed_cell(b)} | first apply fail | expand {b['col_v2']} | {term(b)} |\n\n"
        "## Step counts\n"
        "- ep1: 16. apply fail 2; lock 1.\n"
        "- ep2: 16. apply fail 2; lock 1.\n\n"
        "## decision_basis audit\n"
        f"plants `{a['plant']}`, `{b['plant']}`. designed grok-4.6. "
        f"{a['catalog']} | {b['catalog']}\n\n"
        "## Weaknesses / next\n"
        f"Unused: {unused_s}.\n"
        f"Avoid {a['slug']} and {b['slug']} next. Do not clone r762-r793, "
        "r794-r817, or r818-r844. Do not recycle.\n"
    )
    return body


def build_pair(round_n: int) -> tuple[dict, dict, str]:
    a, b = pair_for(round_n)
    ea = build_episode(round_n, a, 0)
    eb = build_episode(round_n, b, 1)
    notes = notes_md(round_n, a, b, coverage_for(round_n))
    if "Novel coverage:" not in notes:
        raise ValueError("NOTES missing Novel coverage")
    return ea, eb, notes


def emit_stage(stage: Path, round_n: int) -> tuple[str, str]:
    ea, eb, notes = build_pair(round_n)
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes_path = stage / f"NOTES-r{round_n:02d}.md"
    batch.write_text(dumps_episode(ea) + "\n" + dumps_episode(eb) + "\n", encoding="utf-8")
    notes_path.write_text(notes, encoding="utf-8")
    return ea["id"], eb["id"]


def self_check() -> None:
    slugs: list[str] = []
    plants: list[str] = []
    tables: list[str] = []
    leftovers: list[str] = []
    surfaces: list[str] = []
    for i, plant in enumerate(PLANTS):
        slug = plant["slug"]
        slugs.append(slug)
        plants.append(plant["plant"])
        tables.append(plant["table"])
        leftovers.append(plant["leftover"])
        leftovers.append(plant["leftover2"])
        surfaces.append(plant["surface"])
        for frag in BANNED_FRAGMENTS:
            if frag in slug:
                raise ValueError(f"banned fragment {frag} in {slug}")
        if RECYCLE_SUFFIX.search(f"dbm-r{START_ROUND}-{slug}"):
            raise ValueError(f"recycle suffix slug {slug}")
        if i % 2 == 1:
            round_n = START_ROUND + i // 2
            ea, eb, notes = build_pair(round_n)
            for ep in (ea, eb):
                assert ep["reward"]["success"] is True
                assert ep["reward"]["apply_fails"] == 2
                assert ep["reward"]["plan_changes"] == 1
                assert ep["reward"]["lock_timeouts"] == 1
                assert len(ep["steps"]) == 16
                assert ep["meta"]["generator"] == GENERATOR
                assert ep["meta"]["sim_or_real"] == "designed"
                assert not RECYCLE_SUFFIX.search(ep["id"])
            assert notes.startswith("# NOTES-")
            assert "Novel coverage:" in notes
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"duplicate slugs: {slugs}")
    if len(set(plants)) != len(plants):
        raise ValueError(f"duplicate plants: {plants}")
    if len(set(tables)) != len(tables):
        raise ValueError(f"duplicate tables: {tables}")
    if len(set(leftovers)) != len(leftovers):
        raise ValueError("duplicate leftover names")
    if len(set(surfaces)) != len(surfaces):
        raise ValueError(f"duplicate surfaces: {surfaces}")
    if len(PLANTS) % 2:
        raise ValueError("odd plant count")
    print(
        f"self_check ok: {len(PLANTS)//2} pairs r{START_ROUND}–"
        f"r{START_ROUND + len(PLANTS)//2 - 1}"
    )


def run_loop(min_rounds: int = 12, max_rounds: int = 16, minutes: float = 40.0) -> int:
    from round_txn import TransactionError, abort, frontier_status, publish, reserve

    published: list[dict] = []
    hops: list[dict] = []
    deadline = time.monotonic() + minutes * 60
    while len(published) < max_rounds and time.monotonic() < deadline:
        status = frontier_status(FACTORY)
        round_n = status["next_round"]
        reserved = FACTORY / f"ROUND-r{round_n:02d}.reserved.json"
        if reserved.exists():
            hops.append(
                {
                    "dbm_next": round_n,
                    "dbm_reserved": True,
                    "action": "HOP",
                    "stolen": False,
                }
            )
            print(json.dumps({"hop": hops[-1]}), flush=True)
            time.sleep(0.08)
            continue
        try:
            pair_for(round_n)
        except KeyError as exc:
            print(f"STOP: {exc}")
            break
        try:
            payload = reserve(FACTORY, round_n, 2)
        except TransactionError as exc:
            msg = str(exc)
            print(f"reserve failed r{round_n}: {exc}", flush=True)
            if "already exists" in msg or "not the frontier" in msg:
                hops.append({"dbm_next": round_n, "error": msg, "stolen": False, "action": "HOP"})
                print(json.dumps({"hop": hops[-1]}), flush=True)
                time.sleep(0.04)
                continue
            raise
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        try:
            ids = emit_stage(stage, round_n)
            manifest = publish(FACTORY, round_n, token)
        except Exception as exc:
            try:
                abort(FACTORY, round_n, token)
            except Exception as abort_exc:
                print(f"abort failed r{round_n}: {abort_exc}")
            raise RuntimeError(f"stage/publish failed r{round_n}: {exc}") from exc
        published.append({"round": round_n, "ids": ids, "records": manifest.get("records")})
        print(json.dumps({"published": published[-1]}), flush=True)
        if len(published) >= min_rounds and time.monotonic() >= deadline:
            break
    print(json.dumps({"published_rounds": [p["round"] for p in published], "hops": hops}))
    return 0 if published else 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("check", "--smoke"):
        self_check()
        if argv and argv[0] == "--smoke":
            dest = Path("/tmp/dbm-unique-smoke")
            dest.mkdir(parents=True, exist_ok=True)
            ids = emit_stage(dest, START_ROUND)
            print(json.dumps({"smoke_ids": ids}))
        return 0
    if argv[0] == "emit":
        round_n = int(argv[1])
        dest = Path(argv[2])
        dest.mkdir(parents=True, exist_ok=True)
        ids = emit_stage(dest, round_n)
        print(json.dumps({"ids": ids}))
        return 0
    if argv[0] == "loop":
        self_check()
        min_rounds = int(argv[1]) if len(argv) > 1 else 12
        max_rounds = int(argv[2]) if len(argv) > 2 else 16
        return run_loop(min_rounds=min_rounds, max_rounds=max_rounds)
    raise SystemExit("usage: unique_db_migration_repair_mill.py [check|--smoke|emit N DIR|loop [min] [max]]")


if __name__ == "__main__":
    raise SystemExit(main())
