#!/usr/bin/env python3
"""Mill db-migration-repair-factory r1088+ as NEW multi-engine catalog plants.

BAN r1–r817 recycle/warehouse/ORM-CLI.
BAN r818–r865 pg-catalog/AM grid.
BAN r866–r887 engine mill.
BAN r888–r933 (incl. r933 yugabyte-gin-leftover / tidb-placement-policy).
BAN r934–r1087 catalogs.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec1014 = importlib.util.spec_from_file_location("dbm1014", HERE / "dbm-mill-r1014.py")
_m1014 = importlib.util.module_from_spec(_spec1014)
assert _spec1014.loader is not None
_spec1014.loader.exec_module(_m1014)

P = _m1014.P
Q = _m1014.Q
episode = _m1014.episode
clip = _m1014.clip
residual = _m1014.residual
_walk_forbidden = _m1014._walk_forbidden
GEN = _m1014.GEN
FACTORY = _m1014.FACTORY
_m = _m1014._m

CATALOG_FIRST = 1088
USED_1014 = tuple(p["slug"] for a, b in _m1014.PAIRS for p in (a, b))
BANNED_NEEDLES = _m1014.BANNED_NEEDLES + USED_1014

PAIRS: list[tuple[dict, dict]] = [
    (
        Q("oracle-sql-quarantine", "ora-quar", "ora6", "qr_row", "sku", "sku_norm",
          "BEGIN DBMS_SQLQ.CREATE_QUARANTINE_BY_SQL_ID(sql_id=>'sku1'); END;",
          "SELECT sql_text FROM dba_sql_quarantine",
          "ERROR: SQL quarantine leftover capture; leftover qr_row_ora6_tmp; cannot rewrite sku",
          "Oracle SQL quarantine leftover capture; expand sku_norm"),
        Q("sqlserver-autotune", "mss-autotune", "mss6", "at_row", "sku", "sku_norm",
          "ALTER DATABASE CURRENT SET AUTOMATIC_TUNING (FORCE_LAST_GOOD_PLAN = ON)",
          "SELECT name, desired_state_desc FROM sys.database_automatic_tuning_options",
          "ERROR: automatic tuning leftover forced plan; leftover at_row_mss6_tmp; cannot rewrite sku",
          "SQL Server automatic tuning leftover plan; expand sku_norm"),
    ),
    (
        Q("oracle-sql-directive", "ora-spdir", "ora6", "sd_row", "sku", "sku_norm",
          "BEGIN DBMS_SPD.FLUSH_SQL_PLAN_DIRECTIVE; END;",
          "SELECT directive_id FROM dba_sql_plan_directives",
          "ERROR: SQL plan directive leftover stale; leftover sd_row_ora6_tmp; cannot rewrite sku",
          "Oracle SQL plan directive leftover; expand sku_norm"),
        Q("mysql-undo-trunc", "my-undo", "my6", "un_row", "sku", "sku_norm",
          "SET GLOBAL innodb_undo_log_truncate=ON",
          "SHOW VARIABLES LIKE 'innodb_undo_log_truncate'",
          "ERROR: undo leftover truncate; leftover un_row_my6_tmp; cannot rewrite sku",
          "MySQL undo leftover truncate; expand sku_norm"),
    ),
    (
        Q("oracle-im-expression", "ora-imexpr", "ora6", "im_row", "sku", "sku_norm",
          "ALTER TABLE ora6.im_row INMEMORY MEMCOMPRESS FOR QUERY LOW",
          "SELECT table_name, inmemory FROM user_tables WHERE table_name='IM_ROW'",
          "ERROR: in-memory leftover expression unit; leftover im_row_ora6_tmp; cannot rewrite sku",
          "Oracle in-memory leftover expression; expand sku_norm"),
        Q("mariadb-binlog-annot", "mar-annot", "mar6", "an_row", "sku", "sku_norm",
          "SET GLOBAL binlog_annotate_row_events=ON",
          "SHOW VARIABLES LIKE 'binlog_annotate_row_events'",
          "ERROR: annotate leftover row event; leftover an_row_mar6_tmp; cannot rewrite sku",
          "MariaDB binlog annotate leftover; expand sku_norm"),
    ),
    (
        Q("cratedb-blob", "crate-blob", "crt", "bl_cr", "sku", "sku_norm",
          "CREATE BLOB TABLE crt.bl_cr CLUSTERED INTO 4 SHARDS",
          "SELECT table_name FROM information_schema.tables WHERE table_name='bl_cr'",
          "ERROR: blob leftover shard; leftover bl_cr_crt_tmp; cannot rewrite sku",
          "CrateDB blob leftover shard; expand sku_norm"),
        Q("monetdb-imprints", "monet-imp", "mnt", "im_mn", "sku", "sku_norm",
          "CREATE IMPRINTS INDEX im_mn_sku ON mnt.im_mn(sku)",
          "SELECT name FROM sys.idxs WHERE name='im_mn_sku'",
          "ERROR: imprints leftover build; leftover im_mn_mnt_tmp; cannot rewrite sku",
          "MonetDB imprints leftover build; expand sku_norm",
          "DROP INDEX im_mn_sku; DROP TABLE IF EXISTS mnt.im_mn_mnt_tmp"),
    ),
    (
        Q("actian-x100", "actian-x100", "act", "x1_row", "sku", "sku_norm",
          "MODIFY act.x1_row TO X100",
          "SELECT table_name FROM iitables WHERE table_name='x1_row'",
          "ERROR: X100 leftover rewrite; leftover x1_row_act_tmp; cannot rewrite sku",
          "Actian X100 leftover rewrite; expand sku_norm"),
        Q("iris-bitmap", "iris-bitmap", "irs", "bm_ir", "sku", "sku_norm",
          "CREATE INDEX bm_ir_sku ON irs.bm_ir(sku) BITMAP",
          "SELECT INDEX_NAME FROM INFORMATION_SCHEMA.INDEXES WHERE TABLE_NAME='bm_ir'",
          "ERROR: IRIS leftover bitmap; leftover bm_ir_irs_tmp; cannot rewrite sku",
          "InterSystems IRIS leftover bitmap; expand sku_norm",
          "DROP INDEX bm_ir_sku; DROP TABLE IF EXISTS irs.bm_ir_irs_tmp"),
    ),
    (
        Q("azure-hyperscale", "az-hyper", "azh", "hy_az", "sku", "sku_norm",
          "ALTER DATABASE azh SET (SERVICE_OBJECTIVE = 'HS_Gen5_4')",
          "SELECT database_name, service_objective FROM sys.database_service_objectives",
          "ERROR: Hyperscale leftover page server; leftover hy_az_azh_tmp; cannot rewrite sku",
          "Azure SQL Hyperscale leftover page server; expand sku_norm"),
        Q("azure-elastic-pool", "az-epool", "azp", "ep_az", "sku", "sku_norm",
          "ALTER DATABASE azp MODIFY (SERVICE_OBJECTIVE = ELASTIC_POOL (name = sku_pool))",
          "SELECT name FROM sys.elastic_pool_resource_stats",
          "ERROR: elastic pool leftover move; leftover ep_az_azp_tmp; cannot rewrite sku",
          "Azure SQL elastic pool leftover move; expand sku_norm"),
    ),
    (
        Q("crdb-serverless", "crdb-sls", "cr6", "sl_cr", "sku", "sku_norm",
          "ALTER DATABASE cr6 CONFIGURE ZONE USING num_replicas = 5",
          "SHOW ZONE CONFIGURATION FOR DATABASE cr6",
          "ERROR: serverless leftover tenant pod; leftover sl_cr_cr6_tmp; cannot rewrite sku",
          "CRDB serverless leftover tenant pod; expand sku_norm"),
        Q("yb-ycql-index", "yb-ycql", "yb6", "yc_row", "sku", "sku_norm",
          "CREATE INDEX yc_row_sku ON yb6.yc_row (sku)",
          "SELECT index_name FROM system_schema.indexes WHERE table_name='yc_row'",
          "ERROR: YCQL leftover backfill; leftover yc_row_yb6_tmp; cannot rewrite sku",
          "Yugabyte YCQL leftover backfill; expand sku_norm",
          "DROP INDEX yc_row_sku; DROP TABLE IF EXISTS yb6.yc_row_yb6_tmp"),
    ),
    (
        Q("tidb-lightload", "tidb-lload", "ti6", "ld_ti", "sku", "sku_norm",
          "lightning -d /data/ld --backend tidb",
          "SELECT table_name FROM information_schema.tables WHERE table_name='ld_ti'",
          "ERROR: lightning leftover checksum; leftover ld_ti_ti6_tmp; cannot rewrite sku",
          "TiDB lightning leftover checksum; expand sku_norm"),
        Q("clickhouse-s3queue", "ch-s3q", "ch6", "s3_ch", "sku", "sku_norm",
          "CREATE TABLE ch6.s3_ch (sku String) ENGINE = S3Queue('s3://b/sku/*.parquet')",
          "SELECT name, engine FROM system.tables WHERE name='s3_ch'",
          "ERROR: S3Queue leftover processed file; leftover s3_ch_ch6_tmp; cannot rewrite sku",
          "ClickHouse S3Queue leftover file; expand sku_norm"),
    ),
    (
        Q("snowflake-iceberg", "sf-iceberg", "sf6", "ic_sf", "sku", "sku_norm",
          "CREATE ICEBERG TABLE sf6.ic_sf (sku STRING) CATALOG = 'SNOWFLAKE' EXTERNAL_VOLUME = 'vol'",
          "SHOW ICEBERG TABLES LIKE 'ic_sf'",
          "ERROR: Iceberg leftover catalog sync; leftover ic_sf_sf6_tmp; cannot rewrite sku",
          "Snowflake Iceberg leftover catalog; expand sku_norm"),
        Q("bq-biglake", "bq-biglake", "bq6", "bl_bq", "sku", "sku_norm",
          "CREATE OR REPLACE EXTERNAL TABLE bq6.bl_bq WITH CONNECTION `us.bl` OPTIONS(format='ICEBERG', uris=['gs://b/sku'])",
          "SELECT table_name FROM bq6.INFORMATION_SCHEMA.TABLES WHERE table_name='bl_bq'",
          "ERROR: BigLake leftover connection; leftover bl_bq_bq6_tmp; cannot rewrite sku",
          "BigQuery BigLake leftover connection; expand sku_norm"),
    ),
    (
        Q("redshift-ra3", "rs-ra3", "rs6", "ra_rs", "sku", "sku_norm",
          "ALTER TABLE rs6.ra_rs ALTER DISTSTYLE AUTO",
          "SELECT \"column\" FROM pg_table_def WHERE tablename='ra_rs'",
          "ERROR: RA3 leftover RMS; leftover ra_rs_rs6_tmp; cannot rewrite sku",
          "Redshift RA3 leftover RMS; expand sku_norm"),
        Q("spanner-search", "sp-search", "sp6", "sr_sp", "body", "body_v2",
          "CREATE SEARCH INDEX sr_sp_body ON sp6.sr_sp(body)",
          "SELECT INDEX_NAME FROM information_schema.indexes WHERE table_name='sr_sp'",
          "ERROR: search leftover TOKENLIST; leftover sr_sp_sp6_tmp; cannot rewrite body",
          "Spanner search leftover TOKENLIST; expand body_v2",
          "DROP INDEX sr_sp_body; DROP TABLE IF EXISTS sp6.sr_sp_sp6_tmp"),
    ),
    (
        Q("ducklake-snapshot", "ducklake", "dlk", "sn_dl", "sku", "sku_norm",
          "ATTACH 'ducklake:s3://b/sku.ducklake' AS dlk",
          "SELECT snapshot_id FROM dlk.snapshots",
          "ERROR: DuckLake leftover snapshot; leftover sn_dl_dlk_tmp; cannot rewrite sku",
          "DuckLake leftover snapshot; expand sku_norm"),
        Q("lancedb-index", "lance-idx", "lnc", "ix_ln", "emb", "emb_v2",
          "tbl.create_index(metric='l2', num_partitions=64)",
          "tbl.list_indices()",
          "ERROR: Lance leftover IVF; leftover ix_ln_lnc_tmp; cannot rewrite emb",
          "LanceDB leftover IVF; expand emb_v2",
          None, "vector"),
    ),
    (
        Q("qdrant-hnsw", "qdrant-hnsw", "qdr", "hn_qd", "emb", "emb_v2",
          "PUT /collections/hn_qd {\"vectors\":{\"size\":768,\"distance\":\"Cosine\"}}",
          "GET /collections/hn_qd",
          "ERROR: Qdrant leftover HNSW optimizer; leftover hn_qd_qdr_tmp; cannot rewrite emb",
          "Qdrant leftover HNSW optimizer; expand emb_v2",
          None, "vector"),
        Q("weaviate-shard", "weav-shard", "wev", "sh_wv", "emb", "emb_v2",
          "POST /v1/schema {\"class\":\"Sku\",\"vectorizer\":\"none\"}",
          "GET /v1/schema/Sku/shards",
          "ERROR: Weaviate leftover shard; leftover sh_wv_wev_tmp; cannot rewrite emb",
          "Weaviate leftover shard; expand emb_v2",
          None, "vector"),
    ),
    (
        Q("milvus-collection", "milvus-coll", "mlv", "cl_ml", "emb", "emb_v2",
          "collection.create_index(field_name='emb', index_params={'index_type':'IVF_FLAT'})",
          "utility.list_collections()",
          "ERROR: Milvus leftover index build; leftover cl_ml_mlv_tmp; cannot rewrite emb",
          "Milvus leftover index build; expand emb_v2",
          None, "vector"),
        Q("vespa-docsum", "vespa-docsum", "vsp", "ds_vs", "body", "body_v2",
          "vespa deploy --wait 300",
          "vespa status",
          "ERROR: Vespa leftover proton; leftover ds_vs_vsp_tmp; cannot rewrite body",
          "Vespa leftover proton; expand body_v2"),
    ),
    (
        Q("redisearch", "redis-search", "rdsr", "sr_rd", "body", "body_v2",
          "FT.CREATE sr_rd ON HASH PREFIX 1 sku: SCHEMA body TEXT",
          "FT.INFO sr_rd",
          "ERROR: RediSearch leftover indexing; leftover sr_rd_rdsr_tmp; cannot rewrite body",
          "RediSearch leftover indexing; expand body_v2"),
        Q("redisjson", "redis-json", "rdsj", "js_rd", "doc", "doc_v2",
          "JSON.SET js_rd $ '{\"sku\":\"x\"}'",
          "JSON.GET js_rd",
          "ERROR: RedisJSON leftover key; leftover js_rd_rdsj_tmp; cannot rewrite doc",
          "RedisJSON leftover key; expand doc_v2",
          None, "jsonb"),
    ),
    (
        Q("redistimeseries", "redis-ts", "rdst", "ts_rd", "val", "val_v2",
          "TS.CREATE ts_rd RETENTION 86400000",
          "TS.INFO ts_rd",
          "ERROR: RedisTimeSeries leftover chunk; leftover ts_rd_rdst_tmp; cannot rewrite val",
          "RedisTimeSeries leftover chunk; expand val_v2",
          None, "double precision"),
        Q("valkey-cluster", "valkey-cl", "vlk", "cl_vl", "sku", "sku_norm",
          "CLUSTER ADDSLOTS 0-5461",
          "CLUSTER INFO",
          "ERROR: Valkey leftover slot migrate; leftover cl_vl_vlk_tmp; cannot rewrite sku",
          "Valkey leftover slot migrate; expand sku_norm"),
    ),
    (
        Q("dragonfly-snapshot", "dfly-snap", "dfl", "sn_df", "sku", "sku_norm",
          "BGSAVE",
          "INFO persistence",
          "ERROR: Dragonfly leftover snapshot; leftover sn_df_dfl_tmp; cannot rewrite sku",
          "Dragonfly leftover snapshot; expand sku_norm"),
        Q("garnet-aof", "garnet-aof", "grn", "af_gr", "sku", "sku_norm",
          "CONFIG SET appendonly yes",
          "INFO persistence",
          "ERROR: Garnet leftover AOF rewrite; leftover af_gr_grn_tmp; cannot rewrite sku",
          "Garnet leftover AOF rewrite; expand sku_norm"),
    ),
    (
        Q("aerospike-sindex", "aero-sidx", "aer", "si_ae", "sku", "sku_norm",
          "CREATE INDEX si_ae_sku ON aer.si_ae (sku) STRING",
          "SHOW INDEXES aer",
          "ERROR: Aerospike leftover secondary index; leftover si_ae_aer_tmp; cannot rewrite sku",
          "Aerospike leftover secondary index; expand sku_norm",
          "DROP INDEX aer.si_ae_sku; DROP TABLE IF EXISTS aer.si_ae_aer_tmp"),
        Q("riak-yz", "riak-yz", "ria", "yz_ri", "sku", "sku_norm",
          "riak-admin yokozuna schema put sku",
          "riak-admin yokozuna index list",
          "ERROR: Riak leftover Yokozuna; leftover yz_ri_ria_tmp; cannot rewrite sku",
          "Riak leftover Yokozuna; expand sku_norm"),
    ),
    (
        Q("pg-failover-slots", "pg-foslots", "pfs", "fs_pg", "sku", "sku_norm",
          "ALTER SYSTEM SET failover_slot_names = 'sku_slot'",
          "SELECT slot_name, failover FROM pg_replication_slots",
          "ERROR: failover slots leftover synced; leftover fs_pg_pfs_tmp; cannot rewrite sku",
          "pg_failover_slots leftover synced; expand sku_norm"),
        Q("pg-overexplain", "pg-overex", "pox", "ox_pg", "sku", "sku_norm",
          "EXPLAIN (GENERIC_PLAN) SELECT * FROM pox.ox_pg WHERE sku=$1",
          "SELECT relname FROM pg_class WHERE relname='ox_pg'",
          "ERROR: overexplain leftover generic plan; leftover ox_pg_pox_tmp; cannot rewrite sku",
          "pg_overexplain leftover generic plan; expand sku_norm"),
    ),
    (
        Q("pg-logical-origin", "pg-origin", "por", "or_pg", "sku", "sku_norm",
          "SELECT pg_replication_origin_create('sku_ori')",
          "SELECT roname FROM pg_replication_origin",
          "ERROR: replication origin leftover progress; leftover or_pg_por_tmp; cannot rewrite sku",
          "pg replication origin leftover; expand sku_norm",
          "SELECT pg_replication_origin_drop('sku_ori'); DROP TABLE IF EXISTS por.or_pg_por_tmp"),
        Q("pg-sync-standby", "pg-syncsb", "psb", "sb_pg", "sku", "sku_norm",
          "ALTER SYSTEM SET synchronous_standby_names = 'FIRST 1 (sku_sb)'",
          "SHOW synchronous_standby_names",
          "ERROR: sync standby leftover wait; leftover sb_pg_psb_tmp; cannot rewrite sku",
          "sync standby leftover wait; expand sku_norm"),
    ),
    (
        Q("oracle-atp-autoidx", "ora-atpidx", "ora7", "ai_or", "sku", "sku_norm",
          "BEGIN DBMS_AUTO_INDEX.CONFIGURE('AUTO_INDEX_MODE','IMPLEMENT'); END;",
          "SELECT parameter_name, parameter_value FROM dba_auto_index_config",
          "ERROR: ATP leftover auto index; leftover ai_or_ora7_tmp; cannot rewrite sku",
          "Oracle ATP leftover auto index; expand sku_norm"),
        Q("mysql-replica-preserve", "my-preserve", "my7", "pv_my", "sku", "sku_norm",
          "CHANGE REPLICATION SOURCE TO PRESERVE_COMMIT_ORDER=1",
          "SHOW REPLICA STATUS",
          "ERROR: replica leftover preserve order; leftover pv_my_my7_tmp; cannot rewrite sku",
          "MySQL replica leftover preserve order; expand sku_norm"),
    ),
    (
        Q("sqlserver-intelligent", "mss-iqp", "mss7", "iq_ms", "sku", "sku_norm",
          "ALTER DATABASE SCOPED CONFIGURATION SET BATCH_MODE_ON_ROWSTORE = ON",
          "SELECT name, value FROM sys.database_scoped_configurations WHERE name='BATCH_MODE_ON_ROWSTORE'",
          "ERROR: IQP leftover batch mode; leftover iq_ms_mss7_tmp; cannot rewrite sku",
          "SQL Server IQP leftover batch mode; expand sku_norm"),
        Q("sqlite-session-hook", "sl-hook", "sl6", "hk_sl", "sku", "sku_norm",
          "SELECT sqlite3session_create('main','sku')",
          "SELECT name FROM sqlite_master WHERE name='hk_sl'",
          "ERROR: session leftover changeset; leftover hk_sl_sl6_tmp; cannot rewrite sku",
          "SQLite session leftover changeset; expand sku_norm"),
    ),
    (
        Q("firebird-monitoring", "fb-mon", "fb6", "mn_fb", "sku", "sku_norm",
          "SELECT mon$attachment_id FROM mon$attachments",
          "SELECT mon$relation_name FROM mon$io_stats",
          "ERROR: monitoring leftover snapshot; leftover mn_fb_fb6_tmp; cannot rewrite sku",
          "Firebird monitoring leftover snapshot; expand sku_norm"),
        Q("informix-onbar", "ifx-onbar", "ifx6", "ob_if", "sku", "sku_norm",
          "onbar -b -L 0",
          "onstat -d",
          "ERROR: ON-Bar leftover archive; leftover ob_if_ifx6_tmp; cannot rewrite sku",
          "Informix ON-Bar leftover archive; expand sku_norm"),
    ),
    (
        Q("sybase-qpmetrics", "syb-qp", "syb6", "qp_sy", "sku", "sku_norm",
          "sp_configure 'enable metrics capture', 1",
          "SELECT * FROM monSysStatement",
          "ERROR: QP metrics leftover capture; leftover qp_sy_syb6_tmp; cannot rewrite sku",
          "Sybase QP metrics leftover capture; expand sku_norm"),
        Q("netezza-zone", "nz-zone", "nz6", "zn_nz", "sku", "sku_norm",
          "GENERATE STATISTICS ON nz6.zn_nz",
          "SELECT tablename FROM _v_table WHERE tablename='ZN_NZ'",
          "ERROR: zone map leftover generate; leftover zn_nz_nz6_tmp; cannot rewrite sku",
          "Netezza zone leftover generate; expand sku_norm"),
    ),
    (
        Q("exasol-virtual-script", "exa-vs", "exa6", "vs_ex", "sku", "sku_norm",
          "CREATE PYTHON3 SCALAR SCRIPT exa6.vs_ex(...) EMITS (...) AS",
          "SELECT script_name FROM exa_all_scripts WHERE script_name='VS_EX'",
          "ERROR: virtual script leftover UDF; leftover vs_ex_exa6_tmp; cannot rewrite sku",
          "Exasol virtual script leftover UDF; expand sku_norm",
          "DROP SCRIPT exa6.vs_ex; DROP TABLE IF EXISTS exa6.vs_ex_exa6_tmp"),
        Q("questdb-ilp", "qdb-ilp", "qdb6", "il_qd", "ts", "ts_v2",
          "ALTER TABLE qdb6.il_qd SET PARAM o3MaxLag = 60s",
          "tables() WHERE name='il_qd'",
          "ERROR: ILP leftover O3 lag; leftover il_qd_qdb6_tmp; cannot rewrite ts",
          "QuestDB ILP leftover O3 lag; expand ts_v2",
          None, "timestamp"),
    ),
    (
        Q("materialize-webhook", "mz-hook", "mz6", "wh_mz", "sku", "sku_norm",
          "CREATE SOURCE mz6.wh_mz FROM WEBHOOK BODY FORMAT JSON",
          "SHOW SOURCES",
          "ERROR: webhook leftover source; leftover wh_mz_mz6_tmp; cannot rewrite sku",
          "Materialize webhook leftover source; expand sku_norm",
          "DROP SOURCE mz6.wh_mz; DROP TABLE IF EXISTS mz6.wh_mz_mz6_tmp"),
        Q("risingwave-iceberg", "rw-ice", "rw6", "ic_rw", "sku", "sku_norm",
          "CREATE SINK rw6.ic_rw FROM rw6.src WITH (connector='iceberg', warehouse.path='s3://b')",
          "SHOW SINKS",
          "ERROR: Iceberg sink leftover commit; leftover ic_rw_rw6_tmp; cannot rewrite sku",
          "RisingWave Iceberg leftover commit; expand sku_norm",
          "DROP SINK rw6.ic_rw; DROP TABLE IF EXISTS rw6.ic_rw_rw6_tmp"),
    ),
    (
        Q("databricks-liquid-off", "dbx-liqoff", "dbx6", "lq_db", "sku", "sku_norm",
          "ALTER TABLE dbx6.lq_db CLUSTER BY NONE",
          "DESCRIBE DETAIL dbx6.lq_db",
          "ERROR: liquid leftover clustering; leftover lq_db_dbx6_tmp; cannot rewrite sku",
          "Databricks liquid leftover clustering; expand sku_norm"),
        Q("paimon-postpone", "paimon-post", "pm6", "po_pm", "sku", "sku_norm",
          "ALTER TABLE pm6.po_pm SET TBLPROPERTIES ('compaction.max-file-num'='50')",
          "SHOW TBLPROPERTIES pm6.po_pm",
          "ERROR: postpone leftover compact; leftover po_pm_pm6_tmp; cannot rewrite sku",
          "Paimon postpone leftover compact; expand sku_norm"),
    ),
    (
        Q("kudu-auto-rebalancer", "kudu-rebal", "ku6", "rb_ku", "sku", "sku_norm",
          "kudu cluster rebalance",
          "kudu table describe ku6.rb_ku",
          "ERROR: rebalancer leftover move; leftover rb_ku_ku6_tmp; cannot rewrite sku",
          "Kudu leftover rebalancer move; expand sku_norm"),
        Q("phoenix-salt", "phx-salt2", "phx6", "st_ph", "sku", "sku_norm",
          "CREATE TABLE phx6.st_ph (sku VARCHAR PRIMARY KEY) SALT_BUCKETS=16",
          "SELECT table_name FROM system.catalog WHERE table_name='ST_PH'",
          "ERROR: salt leftover split; leftover st_ph_phx6_tmp; cannot rewrite sku",
          "Phoenix leftover salt split; expand sku_norm"),
    ),
    (
        Q("impala-admissions", "impala-adm", "im6", "ad_im", "sku", "sku_norm",
          "SET REQUEST_POOL=sku_pool",
          "SHOW POOLS",
          "ERROR: admission leftover queue; leftover ad_im_im6_tmp; cannot rewrite sku",
          "Impala leftover admission queue; expand sku_norm"),
        Q("kylin-query", "kylin-query", "ky6", "qy_ky", "sku", "sku_norm",
          "POST /kylin/api/query {\"sql\":\"select sku from qy_ky\"}",
          "GET /kylin/api/query",
          "ERROR: query leftover cache; leftover qy_ky_ky6_tmp; cannot rewrite sku",
          "Kylin leftover query cache; expand sku_norm"),
    ),
    (
        Q("drill-zk", "drill-zk", "drl6", "zk_dr", "sku", "sku_norm",
          "ALTER SYSTEM SET `drill.exec.zk.connect` = 'zk:2181'",
          "SELECT * FROM sys.version",
          "ERROR: Drill leftover ZK ephemeral; leftover zk_dr_drl6_tmp; cannot rewrite sku",
          "Drill leftover ZK ephemeral; expand sku_norm"),
        Q("synapse-dwu", "syn-dwu", "syn6", "dw_sy", "sku", "sku_norm",
          "ALTER DATABASE syn6 MODIFY (SERVICE_OBJECTIVE = 'DW300c')",
          "SELECT database_id, slo_name FROM sys.dm_operation_status",
          "ERROR: DWU leftover scale; leftover dw_sy_syn6_tmp; cannot rewrite sku",
          "Synapse leftover DWU scale; expand sku_norm"),
    ),
    (
        Q("fabric-eventhouse", "fab-eh", "fab6", "eh_fa", "sku", "sku_norm",
          "CREATE TABLE fab6.eh_fa (sku:string) WITH (folder='sku')",
          "SHOW TABLES",
          "ERROR: Eventhouse leftover extent; leftover eh_fa_fab6_tmp; cannot rewrite sku",
          "Fabric Eventhouse leftover extent; expand sku_norm"),
        Q("cosmos-autoscale", "cosmos-auto", "cos6", "as_cs", "sku", "sku_norm",
          "ALTER CONTAINER cos6.as_cs SET AUTOSCALE 4000",
          "SELECT * FROM cos6.as_cs",
          "ERROR: autoscale leftover RU; leftover as_cs_cos6_tmp; cannot rewrite sku",
          "Cosmos leftover autoscale RU; expand sku_norm"),
    ),
    (
        Q("dynamodb-ondemand", "ddb-ondemand", "ddb6", "od_dd", "sku", "sku_norm",
          "UpdateTable od_dd BillingMode=PAY_PER_REQUEST",
          "DescribeTable od_dd",
          "ERROR: on-demand leftover UPDATING; leftover od_dd_ddb6_tmp; cannot rewrite sku",
          "DynamoDB leftover on-demand UPDATING; expand sku_norm"),
        Q("presto-dynamic-filter", "presto-df", "pr6", "df_pr", "sku", "sku_norm",
          "SET SESSION enable_dynamic_filtering = true",
          "SHOW SESSION LIKE 'enable_dynamic_filtering'",
          "ERROR: dynamic filter leftover collection; leftover df_pr_pr6_tmp; cannot rewrite sku",
          "Presto leftover dynamic filter; expand sku_norm"),
    ),
    (
        Q("hive-llap", "hive-llap", "hv6", "ll_hv", "sku", "sku_norm",
          "SET hive.llap.execution.mode=all",
          "SET hive.llap.execution.mode",
          "ERROR: LLAP leftover daemon; leftover ll_hv_hv6_tmp; cannot rewrite sku",
          "Hive leftover LLAP daemon; expand sku_norm"),
        Q("spark-skewjoin", "spark-skew", "spk6", "sk_sp", "sku", "sku_norm",
          "SET spark.sql.adaptive.skewJoin.enabled=true",
          "SHOW TBLPROPERTIES spk6.sk_sp",
          "ERROR: AQE leftover skew split; leftover sk_sp_spk6_tmp; cannot rewrite sku",
          "Spark leftover AQE skew split; expand sku_norm"),
    ),
    (
        Q("hbase-snapshot", "hbase-snap", "hb6", "sn_hb", "sku", "sku_norm",
          "snapshot 'sn_hb', 'sn_hb_s'",
          "list_snapshots",
          "ERROR: snapshot leftover clone; leftover sn_hb_hb6_tmp; cannot rewrite sku",
          "HBase leftover snapshot clone; expand sku_norm"),
        Q("accumulo-summary", "acc-sum", "acc6", "sm_ac", "sku", "sku_norm",
          "summaries -t sm_ac",
          "listsummaries",
          "ERROR: summary leftover file; leftover sm_ac_acc6_tmp; cannot rewrite sku",
          "Accumulo leftover summary file; expand sku_norm"),
    ),
    (
        Q("geode-lucene", "geode-lucene", "geo6", "lc_ge", "body", "body_v2",
          "create lucene-index --name=lc_ge --region=sku --field=body",
          "list lucene-indexes",
          "ERROR: Lucene leftover index; leftover lc_ge_geo6_tmp; cannot rewrite body",
          "Geode leftover Lucene index; expand body_v2"),
        Q("hazelcast-sql-imap", "hz-imap", "hz6", "im_hz", "sku", "sku_norm",
          "CREATE MAPPING im_hz TYPE IMap OPTIONS ('keyFormat'='varchar','valueFormat'='json-flat')",
          "SHOW MAPPINGS",
          "ERROR: IMap leftover mapping; leftover im_hz_hz6_tmp; cannot rewrite sku",
          "Hazelcast leftover IMap mapping; expand sku_norm",
          "DROP MAPPING im_hz; DROP TABLE IF EXISTS hz6.im_hz_hz6_tmp"),
    ),
    (
        Q("infinispan-resp", "ispn-resp", "isp6", "rp_is", "sku", "sku_norm",
          "CREATE CACHE rp_is WITH encoding=application/x-protostream",
          "DESCRIBE CACHE rp_is",
          "ERROR: RESP leftover cache; leftover rp_is_isp6_tmp; cannot rewrite sku",
          "Infinispan leftover RESP cache; expand sku_norm"),
        Q("timesten-imdb", "tt-imdb", "tt6", "im_tt", "sku", "sku_norm",
          "ttIsql -e 'call ttOptSetFlag(''RowLock'',1)'",
          "SELECT tblname FROM sys.tables WHERE tblname='IM_TT'",
          "ERROR: IMDB leftover rowlock; leftover im_tt_tt6_tmp; cannot rewrite sku",
          "TimesTen leftover IMDB rowlock; expand sku_norm"),
    ),
    (
        Q("ndb-disk", "ndb-disk", "ndb6", "dk_nd", "sku", "sku_norm",
          "CREATE TABLESPACE ts_sku ADD DATAFILE 'sku.dat' USE LOGFILE GROUP lg1 ENGINE=NDB",
          "SELECT TABLESPACE_NAME FROM information_schema.files WHERE FILE_NAME='sku.dat'",
          "ERROR: NDB leftover tablespace; leftover dk_nd_ndb6_tmp; cannot rewrite sku",
          "MySQL NDB leftover tablespace; expand sku_norm"),
        Q("citus-mx", "citus-mx", "ci6", "mx_ci", "sku", "sku_norm",
          "SELECT citus_set_coordinator_host('coord')",
          "SELECT * FROM citus_get_active_worker_nodes()",
          "ERROR: MX leftover metadata sync; leftover mx_ci_ci6_tmp; cannot rewrite sku",
          "Citus leftover MX metadata sync; expand sku_norm"),
    ),
    (
        Q("cassandra-sai-ann", "cas-ann", "cas6", "an_ca", "emb", "emb_v2",
          "CREATE CUSTOM INDEX an_ca_emb ON cas6.an_ca (emb) USING 'StorageAttachedIndex'",
          "SELECT index_name FROM system_schema.indexes WHERE table_name='an_ca'",
          "ERROR: SAI leftover ANN build; leftover an_ca_cas6_tmp; cannot rewrite emb",
          "Cassandra leftover SAI ANN; expand emb_v2",
          None, "vector"),
        Q("scylla-alternator", "scylla-alt", "scy6", "al_sc", "sku", "sku_norm",
          "CreateTable Alternator al_sc",
          "ListTables",
          "ERROR: Alternator leftover GSI; leftover al_sc_scy6_tmp; cannot rewrite sku",
          "Scylla leftover Alternator GSI; expand sku_norm"),
    ),
    (
        Q("neo4j-fabric", "neo-fabric", "neo6", "fb_ne", "sku", "sku_norm",
          "CREATE DATABASE fb_ne",
          "SHOW DATABASES",
          "ERROR: Fabric leftover composite; leftover fb_ne_neo6_tmp; cannot rewrite sku",
          "Neo4j leftover Fabric composite; expand sku_norm"),
        Q("arango-smart", "arango-smart", "ara6", "sm_ar", "sku", "sku_norm",
          "db._create('sm_ar', {numberOfShards:6, shardKeys:['sku'], smartGraphAttribute:'sku'})",
          "db._collections()",
          "ERROR: SmartGraph leftover shard; leftover sm_ar_ara6_tmp; cannot rewrite sku",
          "ArangoDB leftover SmartGraph shard; expand sku_norm"),
    ),
    (
        Q("couchbase-eventing", "cb-event", "cb6", "ev_cb", "sku", "sku_norm",
          "POST /api/v1/functions/sku_fn",
          "GET /api/v1/status",
          "ERROR: Eventing leftover undeployed; leftover ev_cb_cb6_tmp; cannot rewrite sku",
          "Couchbase leftover Eventing undeployed; expand sku_norm"),
        Q("mongo-timeseries", "mongo-ts", "mo6", "ts_mo", "ts", "ts_v2",
          "db.createCollection('ts_mo',{timeseries:{timeField:'ts',metaField:'sku'}})",
          "db.getCollectionInfos({name:'ts_mo'})",
          "ERROR: timeseries leftover bucket; leftover ts_mo_mo6_tmp; cannot rewrite ts",
          "Mongo leftover timeseries bucket; expand ts_v2",
          None, "timestamp"),
    ),
    (
        Q("timeplus-external", "tp-ext", "tp6", "ex_tp", "sku", "sku_norm",
          "CREATE EXTERNAL STREAM tp6.ex_tp (sku string) SETTINGS type='kafka'",
          "SHOW STREAMS",
          "ERROR: external leftover offset; leftover ex_tp_tp6_tmp; cannot rewrite sku",
          "Timeplus leftover external offset; expand sku_norm",
          "DROP STREAM tp6.ex_tp; DROP TABLE IF EXISTS tp6.ex_tp_tp6_tmp"),
        Q("clickhouse-refreshable2", "ch-rmv2", "ch7", "rv_ch", "sku", "sku_norm",
          "CREATE MATERIALIZED VIEW ch7.rv_ch REFRESH EVERY 5 MINUTE APPEND AS SELECT sku FROM ch7.src",
          "SELECT name FROM system.view_refreshes WHERE view='rv_ch'",
          "ERROR: refresh leftover APPEND; leftover rv_ch_ch7_tmp; cannot rewrite sku",
          "ClickHouse leftover refresh APPEND; expand sku_norm",
          "DROP VIEW ch7.rv_ch; DROP TABLE IF EXISTS ch7.rv_ch_ch7_tmp"),
    ),
    (
        Q("gauss-mot", "gauss-mot", "gs6", "mt_gs", "sku", "sku_norm",
          "ALTER TABLE gs6.mt_gs SET (orientation=mot)",
          "SELECT relname, reloptions FROM pg_class WHERE relname='mt_gs'",
          "ERROR: MOT leftover memory; leftover mt_gs_gs6_tmp; cannot rewrite sku",
          "GaussDB leftover MOT memory; expand sku_norm"),
        Q("kingbase-sysaudit2", "kb-audit2", "kb6", "au_kb", "evt", "evt_v2",
          "ALTER SYSTEM SET sysaudit.enable = on",
          "SHOW sysaudit.enable",
          "ERROR: sysaudit leftover WAL; leftover au_kb_kb6_tmp; cannot rewrite evt",
          "Kingbase leftover sysaudit WAL; expand evt_v2"),
    ),
    (
        Q("opengauss-sms", "og-sms", "og6", "sm_og", "sku", "sku_norm",
          "ALTER TABLE og6.sm_og SET (compression=yes)",
          "SELECT relname, reloptions FROM pg_class WHERE relname='sm_og'",
          "ERROR: SMS leftover compression; leftover sm_og_og6_tmp; cannot rewrite sku",
          "openGauss leftover SMS compression; expand sku_norm"),
        Q("vastbase-imcs2", "vb-imcs2", "vb6", "im_vb", "sku", "sku_norm",
          "ALTER TABLE vb6.im_vb SET (imcs_enable=on, imcs_cols='sku')",
          "SELECT relname, reloptions FROM pg_class WHERE relname='im_vb'",
          "ERROR: IMCS leftover column group; leftover im_vb_vb6_tmp; cannot rewrite sku",
          "Vastbase leftover IMCS column group; expand sku_norm"),
    ),
    (
        Q("tdsql-cdc", "tdsql-cdc", "td6", "cd_td", "sku", "sku_norm",
          "CALL mysql.tdsql_start_cdc('sku')",
          "SELECT * FROM mysql.tdsql_cdc_status",
          "ERROR: TDSQL leftover CDC; leftover cd_td_td6_tmp; cannot rewrite sku",
          "TDSQL leftover CDC; expand sku_norm"),
        Q("sequoiadb-split", "sdb-split", "sdb6", "sp_sd", "sku", "sku_norm",
          "db.sp_sd.split('group1','group2',50)",
          "db.sp_sd.getIndexes()",
          "ERROR: split leftover task; leftover sp_sd_sdb6_tmp; cannot rewrite sku",
          "SequoiaDB leftover split task; expand sku_norm"),
    ),
    (
        Q("oceanbase-standby", "ob-standby", "ob6", "sb_ob", "sku", "sku_norm",
          "ALTER SYSTEM SWITCH TO PHYSICAL STANDBY",
          "SELECT tenant_name, status FROM oceanbase.DBA_OB_TENANTS",
          "ERROR: standby leftover redo apply; leftover sb_ob_ob6_tmp; cannot rewrite sku",
          "OceanBase leftover standby apply; expand sku_norm"),
        Q("polar-global-index2", "polar-gidx2", "po6", "gi_po", "sku", "sku_norm",
          "CREATE GLOBAL INDEX gi_po_sku ON po6.gi_po(sku) PARALLEL 4",
          "SELECT index_name FROM information_schema.statistics WHERE table_name='gi_po'",
          "ERROR: global leftover parallel build; leftover gi_po_po6_tmp; cannot rewrite sku",
          "PolarDB leftover global parallel; expand sku_norm",
          "DROP INDEX gi_po_sku ON po6.gi_po; DROP TABLE IF EXISTS po6.gi_po_po6_tmp"),
    ),
    (
        Q("doris-mtmv", "doris-mtmv", "do6", "mv_do", "sku", "sku_norm",
          "CREATE MATERIALIZED VIEW do6.mv_do BUILD IMMEDIATE REFRESH COMPLETE AS SELECT sku, count(*) FROM do6.src GROUP BY sku",
          "SHOW MATERIALIZED VIEW FROM do6",
          "ERROR: MTMV leftover BUILD; leftover mv_do_do6_tmp; cannot rewrite sku",
          "Doris leftover MTMV BUILD; expand sku_norm",
          "DROP MATERIALIZED VIEW do6.mv_do; DROP TABLE IF EXISTS do6.mv_do_do6_tmp"),
        Q("starrocks-spill", "sr-spill", "sr6", "sp_sr", "sku", "sku_norm",
          "SET enable_spill=true",
          "SHOW VARIABLES LIKE 'enable_spill'",
          "ERROR: spill leftover tmp; leftover sp_sr_sr6_tmp; cannot rewrite sku",
          "StarRocks leftover spill tmp; expand sku_norm"),
    ),
    (
        Q("trino-fault-spool", "trino-spool", "tr6", "sp_tr", "sku", "sku_norm",
          "SET SESSION exchange_compression = true",
          "SHOW SESSION LIKE 'exchange_compression'",
          "ERROR: spool leftover exchange; leftover sp_tr_tr6_tmp; cannot rewrite sku",
          "Trino leftover spool exchange; expand sku_norm"),
        Q("hudi-mdt", "hudi-mdt", "hu6", "md_hu", "sku", "sku_norm",
          "CALL hudi.system.init_metadata_table(table => 'hu6.md_hu')",
          "SHOW TBLPROPERTIES hu6.md_hu",
          "ERROR: MDT leftover bootstrap; leftover md_hu_hu6_tmp; cannot rewrite sku",
          "Hudi leftover MDT bootstrap; expand sku_norm"),
    ),
    (
        Q("pinot-tier", "pinot-tier", "pi6", "tr_pi", "sku", "sku_norm",
          "SET pinot.tierConfigs = '[{\"name\":\"cold\",\"segmentSelectorType\":\"TIME\"}]'",
          "SELECT tableName FROM pinot.tables WHERE tableName='tr_pi'",
          "ERROR: tier leftover move; leftover tr_pi_pi6_tmp; cannot rewrite sku",
          "Pinot leftover tier move; expand sku_norm"),
        Q("druid-msq", "druid-msq", "dr6", "mq_dr", "sku", "sku_norm",
          "POST /druid/v2/sql/task {\"query\":\"INSERT INTO mq_dr SELECT * FROM src\"}",
          "SELECT id, status FROM sys.tasks WHERE datasource='mq_dr'",
          "ERROR: MSQ leftover task; leftover mq_dr_dr6_tmp; cannot rewrite sku",
          "Druid leftover MSQ task; expand sku_norm"),
    ),
    (
        Q("ydb-topic", "ydb-topic", "yd6", "tp_yd", "sku", "sku_norm",
          "CREATE TOPIC yd6.tp_yd",
          "SELECT Name FROM `.sys/partition_stats` WHERE Path LIKE '%tp_yd%'",
          "ERROR: topic leftover consumer; leftover tp_yd_yd6_tmp; cannot rewrite sku",
          "YDB leftover topic consumer; expand sku_norm",
          "DROP TOPIC yd6.tp_yd; DROP TABLE IF EXISTS yd6.tp_yd_yd6_tmp"),
        Q("timescale-osm", "ts-osm", "ts6", "os_ts", "ts_col", "ts_col_v2",
          "SELECT add_tiering_policy('ts6.os_ts', INTERVAL '30 days')",
          "SELECT hypertable_name FROM timescaledb_information.hypertables WHERE hypertable_name='os_ts'",
          "ERROR: OSM leftover tier; leftover os_ts_ts6_tmp; cannot rewrite ts_col",
          "Timescale leftover OSM tier; expand ts_col_v2",
          None, "timestamptz"),
    ),
    (
        Q("citus-schema-move", "citus-smove", "ci7", "sm_ci", "sku", "sku_norm",
          "SELECT citus_move_shard_placement(1001,'src','dst')",
          "SELECT shardid FROM pg_dist_placement LIMIT 1",
          "ERROR: shard leftover move; leftover sm_ci_ci7_tmp; cannot rewrite sku",
          "Citus leftover shard move; expand sku_norm"),
        Q("pgvector-halfvec", "pgv-half", "pv6", "hv_pv", "emb", "emb_v2",
          "CREATE INDEX hv_pv_emb ON pv6.hv_pv USING hnsw ((emb::halfvec(768)) halfvec_l2_ops)",
          "SELECT indexname FROM pg_indexes WHERE tablename='hv_pv'",
          "ERROR: halfvec leftover hnsw; leftover hv_pv_pv6_tmp; cannot rewrite emb",
          "pgvector leftover halfvec hnsw; expand emb_v2",
          "DROP INDEX pv6.hv_pv_emb; DROP TABLE IF EXISTS pv6.hv_pv_pv6_tmp",
          "vector(768)"),
    ),
    (
        Q("postgis-sfcgal", "pgis-sfcgal", "pgis6", "sf_pg", "geom", "geom_v2",
          "SELECT ST_3DIntersection(geom, geom) FROM pgis6.sf_pg",
          "SELECT postgis_sfcgal_version()",
          "ERROR: SFCGAL leftover 3D; leftover sf_pg_pgis6_tmp; cannot rewrite geom",
          "PostGIS leftover SFCGAL 3D; expand geom_v2",
          None, "geometry"),
        Q("partman-epoch", "ppm-epoch", "ppm6", "ep_pm", "ts_col", "ts_col_v2",
          "SELECT partman.create_parent('ppm6.ep_pm','ts_col','native','hourly', p_epoch := 'seconds')",
          "SELECT parent_table FROM partman.part_config WHERE parent_table='ppm6.ep_pm'",
          "ERROR: partman leftover epoch; leftover ep_pm_ppm6_tmp; cannot rewrite ts_col",
          "pg_partman leftover epoch; expand ts_col_v2",
          None, "bigint"),
    ),
    (
        Q("pg-cron-run", "pg-cronrun", "pcr6", "cr_pc", "sku", "sku_norm",
          "SELECT cron.alter_job((SELECT jobid FROM cron.job WHERE jobname='sku_maint'), active := false)",
          "SELECT jobid, active FROM cron.job WHERE jobname='sku_maint'",
          "ERROR: pg_cron leftover alter; leftover cr_pc_pcr6_tmp; cannot rewrite sku",
          "pg_cron leftover alter; expand sku_norm"),
        Q("pglogical-sync", "pgl-sync", "pgl6", "sy_pg", "sku", "sku_norm",
          "SELECT pglogical.alter_subscription_synchronize('sku_sub')",
          "SELECT sub_name, sub_enabled FROM pglogical.subscription",
          "ERROR: pglogical leftover synchronize; leftover sy_pg_pgl6_tmp; cannot rewrite sku",
          "pglogical leftover synchronize; expand sku_norm"),
    ),
    (
        Q("pgfdw-batch", "pg-fbatch", "pfdw6", "bt_pf", "sku", "sku_norm",
          "ALTER SERVER remote OPTIONS (ADD batch_size '100')",
          "SELECT srvoptions FROM pg_foreign_server WHERE srvname='remote'",
          "ERROR: postgres_fdw leftover batch; leftover bt_pf_pfdw6_tmp; cannot rewrite sku",
          "postgres_fdw leftover batch; expand sku_norm"),
        Q("ffdw-program", "file-prog", "ffdw6", "pr_ff", "sku", "sku_norm",
          "CREATE FOREIGN TABLE ffdw6.pr_ff (sku text) SERVER file_srv OPTIONS (program 'cat /data/sku.csv', format 'csv')",
          "SELECT relname FROM pg_class WHERE relname='pr_ff'",
          "ERROR: file_fdw leftover program; leftover pr_ff_ffdw6_tmp; cannot rewrite sku",
          "file_fdw leftover program; expand sku_norm",
          "DROP FOREIGN TABLE ffdw6.pr_ff; DROP TABLE IF EXISTS ffdw6.pr_ff_ffdw6_tmp"),
    ),
    (
        Q("orafdw-prefetch", "ora-fpre", "ofdw6", "pf_of", "sku", "sku_norm",
          "ALTER SERVER ora_srv OPTIONS (ADD prefetch '200')",
          "SELECT srvoptions FROM pg_foreign_server WHERE srvname='ora_srv'",
          "ERROR: oracle_fdw leftover prefetch; leftover pf_of_ofdw6_tmp; cannot rewrite sku",
          "oracle_fdw leftover prefetch; expand sku_norm"),
        Q("myfdw-fetch", "my-ffetch", "mfdw6", "ft_mf", "sku", "sku_norm",
          "ALTER SERVER my_srv OPTIONS (ADD fetch_size '500')",
          "SELECT srvoptions FROM pg_foreign_server WHERE srvname='my_srv'",
          "ERROR: mysql_fdw leftover fetch; leftover ft_mf_mfdw6_tmp; cannot rewrite sku",
          "mysql_fdw leftover fetch; expand sku_norm"),
    ),
]


def _assert_catalog() -> None:
    slugs = []
    quals = []
    plants = []
    for a, b in PAIRS:
        for p in (a, b):
            blob = " ".join([p["slug"], p["plant"], p["seed"], p["fail"], p["catalog"]]).lower()
            for needle in BANNED_NEEDLES:
                if needle.lower() in blob:
                    raise SystemExit(f"banned needle {needle!r} in {p['slug']}")
            slugs.append(p["slug"])
            quals.append(p["qual"])
            plants.append(p["plant"])
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs")
    if len(quals) != len(set(quals)):
        raise SystemExit("duplicate schema.table")
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plant names")


_assert_catalog()


def pair_for(round_number: int) -> tuple[dict, dict]:
    idx = round_number - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"round {round_number} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}"
        )
    return PAIRS[idx]


def notes_text(round_number: int, a: dict, b: dict) -> str:
    novelty = max(48, 72 - (round_number - CATALOG_FIRST) // 2)
    ver = _m.ver_for(round_number)
    return "\n".join(
        [
            f"# NOTES-r{round_number} {FACTORY}",
            "",
            f"Novel coverage: {novelty}%",
            "",
            "Two designed episodes (quota 2). Unique vs r1-r105 first-cycle, r106-r239 engines, "
            "r240-r761 recycle mill, r762-r793 warehouse mill, r794-r817 ORM-CLI grid, "
            "r818-r865 pg-catalog/AM grid, r866-r887 engine mill, r888-r933 multi-engine mill, "
            "and r934-r1087 catalogs. "
            f"Surfaces: {a['slug']}; {b['slug']}. "
            f"IDs `dbm-r{round_number}-<slug>` without `-rNN` recycle suffix. Dual-object residual. "
            "First-apply fail + plan change + lock retry. Semantic mill (not CLI clone).",
            "",
            "| id | seed | first apply | plan change | terminal |",
            "|---|---|---|---|---|",
            f"| dbm-r{round_number}-{a['slug']} | {clip(a['seed'], 52)} | first apply fail | expand {a['new']} | 4/4 {residual(a)} |",
            f"| dbm-r{round_number}-{b['slug']} | {clip(b['seed'], 52)} | first apply fail | expand {b['new']} | 4/4 {residual(b)} |",
            "",
            "## Step counts",
            "- ep1: 16. apply fail 2; lock 1.",
            "- ep2: 16. apply fail 2; lock 1.",
            "",
            "## decision_basis audit",
            f"plants `{a['plant']}`, `{b['plant']}`. designed {GEN}. {a['catalog']} | {b['catalog']}",
            "",
            "## Weaknesses / next",
            "Avoid the two slugs in this round next. Do not clone r762-r1087.",
            f"schema version {ver}.",
            "",
        ]
    )


def write_round(round_number: int, staging: Path) -> None:
    a, b = pair_for(round_number)
    recs = [episode(round_number, a), episode(round_number, b)]
    for rec in recs:
        _walk_forbidden(rec)
        if rec["meta"]["sim_or_real"] != "designed":
            raise SystemExit("sim_or_real must be designed")
        if rec["meta"]["generator"] != GEN:
            raise SystemExit("generator")
        if len(rec["steps"]) != 16:
            raise SystemExit("steps")
    (staging / f"batch-r{round_number:02d}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs)
    )
    (staging / f"NOTES-r{round_number:02d}.md").write_text(notes_text(round_number, a, b))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int)
    parser.add_argument("--staging", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(argv)
    if args.smoke:
        import tempfile

        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
        from check_records import check_jsonl

        with tempfile.TemporaryDirectory() as td:
            stage = Path(td)
            write_round(CATALOG_FIRST, stage)
            errs, warns, kinds, n = check_jsonl(
                stage / f"batch-r{CATALOG_FIRST:02d}.jsonl", "smoke.jsonl"
            )
            if errs or warns or n != 2:
                print({"errors": errs, "warnings": warns, "n": n, "kinds": kinds})
                return 1
            print(
                json.dumps(
                    {
                        "ok": True,
                        "records": n,
                        "kinds": kinds,
                        "pairs": len(PAIRS),
                        "last": CATALOG_FIRST + len(PAIRS) - 1,
                    }
                )
            )
        return 0
    if args.round is None or args.staging is None:
        print("need --round and --staging (or --smoke)", file=sys.stderr)
        return 2
    write_round(args.round, args.staging)
    print(json.dumps({"wrote": args.round, "staging": str(args.staging)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
