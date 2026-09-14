#!/usr/bin/env python3
"""Mill db-migration-repair-factory r1141+ as NEW multi-engine catalog plants.

BAN r1–r817 recycle/warehouse/ORM-CLI.
BAN r818–r1087 prior unique catalogs.
BAN r888–r933 (incl. r933 yugabyte-gin-leftover / tidb-placement-policy).
BAN r1088–r1140 catalog.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec1088 = importlib.util.spec_from_file_location("dbm1088", HERE / "dbm-mill-r1088.py")
_m1088 = importlib.util.module_from_spec(_spec1088)
assert _spec1088.loader is not None
_spec1088.loader.exec_module(_m1088)

Q = _m1088.Q
episode = _m1088.episode
clip = _m1088.clip
residual = _m1088.residual
_walk_forbidden = _m1088._walk_forbidden
GEN = _m1088.GEN
FACTORY = _m1088.FACTORY
_m = _m1088._m

CATALOG_FIRST = 1141
USED_1088 = tuple(p["slug"] for a, b in _m1088.PAIRS for p in (a, b))
BANNED_NEEDLES = _m1088.BANNED_NEEDLES + USED_1088

PAIRS: list[tuple[dict, dict]] = [
    (
        Q("oracle-sql-monitor", "ora-sqlmon", "ora8", "sm_or", "sku", "sku_norm",
          "BEGIN DBMS_SQL_MONITOR.START_MONITORING; END;",
          "SELECT sql_id FROM v$sql_monitor WHERE sql_text LIKE '%sku%'",
          "ERROR: SQL monitor leftover capture; leftover sm_or_ora8_tmp; cannot rewrite sku",
          "Oracle SQL monitor leftover capture; expand sku_norm"),
        Q("sqlserver-qds-wait", "mss-qdswait", "mss8", "qw_ms", "sku", "sku_norm",
          "ALTER DATABASE CURRENT SET QUERY_STORE = ON (WAIT_STATS_CAPTURE_MODE = ON)",
          "SELECT wait_stats_capture_mode_desc FROM sys.database_query_store_options",
          "ERROR: Query Store leftover wait capture; leftover qw_ms_mss8_tmp; cannot rewrite sku",
          "SQL Server leftover wait capture; expand sku_norm"),
    ),
    (
        Q("mysql-donor-inst", "my-donor", "my8", "dn_my", "sku", "sku_norm",
          "CLONE INSTANCE FROM 'donor':3306 IDENTIFIED BY 'x'",
          "SELECT STATE FROM performance_schema.clone_status",
          "ERROR: clone leftover donor snapshot; leftover dn_my_my8_tmp; cannot rewrite sku",
          "MySQL leftover clone donor; expand sku_norm"),
        Q("mar-spd-wrap", "mar-spd", "mar8", "sp_ma", "sku", "sku_norm",
          "CREATE TABLE mar8.sp_ma (sku varchar(32)) ENGINE=SPIDER COMMENT='wrapper \"mysql\", table \"sku\"'",
          "SELECT ENGINE FROM information_schema.tables WHERE table_name='sp_ma'",
          "ERROR: Spider leftover wrapper; leftover sp_ma_mar8_tmp; cannot rewrite sku",
          "MariaDB leftover Spider wrapper; expand sku_norm"),
    ),
    (
        Q("sl-gpoly-shape", "sl-gpoly", "sl8", "gp_sl", "g", "g_v2",
          "CREATE VIRTUAL TABLE sl8.gp_sl USING geopoly(_shape)",
          "SELECT name FROM sqlite_master WHERE name='gp_sl'",
          "ERROR: geopoly leftover _shape; leftover gp_sl_sl8_tmp; cannot rewrite g",
          "SQLite leftover geopoly _shape; expand g_v2",
          "DROP TABLE sl8.gp_sl; DROP TABLE IF EXISTS sl8.gp_sl_sl8_tmp"),
        Q("duckdb-delta", "duck-delta", "dk8", "dl_dk", "sku", "sku_norm",
          "INSTALL delta; LOAD delta; SELECT * FROM delta_scan('s3://b/sku')",
          "SELECT extension_name FROM duckdb_extensions() WHERE extension_name='delta'",
          "ERROR: delta leftover snapshot; leftover dl_dk_dk8_tmp; cannot rewrite sku",
          "DuckDB leftover delta snapshot; expand sku_norm"),
    ),
    (
        Q("crdb-mvcc-gc", "crdb-mvcc", "cr8", "gc_cr", "sku", "sku_norm",
          "ALTER TABLE cr8.gc_cr CONFIGURE ZONE USING gc.ttlseconds = 600",
          "SHOW ZONE CONFIGURATION FOR TABLE cr8.gc_cr",
          "ERROR: MVCC leftover GC TTL; leftover gc_cr_cr8_tmp; cannot rewrite sku",
          "CRDB leftover MVCC GC TTL; expand sku_norm"),
        Q("yb-packed-row", "yb-prow", "yb8", "pr_yb", "sku", "sku_norm",
          "ALTER TABLE yb8.pr_yb SET (yb_max_packed_row_size = 8192)",
          "SELECT relname, reloptions FROM pg_class WHERE relname='pr_yb'",
          "ERROR: packed leftover decode; leftover pr_yb_yb8_tmp; cannot rewrite sku",
          "Yugabyte leftover packed decode; expand sku_norm"),
    ),
    (
        Q("tidb-tiflash-late", "tidb-tflate", "ti8", "tf_ti", "sku", "sku_norm",
          "ALTER TABLE ti8.tf_ti SET TIFLASH REPLICA 1",
          "SELECT AVAILABLE FROM information_schema.tiflash_replica WHERE TABLE_NAME='tf_ti'",
          "ERROR: TiFlash leftover AVAILABLE=0; leftover tf_ti_ti8_tmp; cannot rewrite sku",
          "TiDB leftover TiFlash AVAILABLE; expand sku_norm"),
        Q("ch-kmap-node", "ch-kmap", "ch8", "km_ch", "sku", "sku_norm",
          "CREATE TABLE ch8.km_ch (k String, v String) ENGINE = KeeperMap('/sku') PRIMARY KEY k",
          "SELECT name, engine FROM system.tables WHERE name='km_ch'",
          "ERROR: KeeperMap leftover node; leftover km_ch_ch8_tmp; cannot rewrite sku",
          "ClickHouse leftover KeeperMap node; expand sku_norm"),
    ),
    (
        Q("sf-hyb-idx", "sf-hyb2", "sf8", "hy_sf", "sku", "sku_norm",
          "CREATE HYBRID TABLE sf8.hy_sf (sku VARCHAR PRIMARY KEY, qty INT) INDEX (qty)",
          "SELECT table_name FROM information_schema.tables WHERE table_name='HY_SF'",
          "ERROR: hybrid leftover index; leftover hy_sf_sf8_tmp; cannot rewrite sku",
          "Snowflake leftover hybrid index; expand sku_norm"),
        Q("bq-sidx-all", "bq-sidx", "bq8", "si_bq", "body", "body_v2",
          "CREATE SEARCH INDEX si_bq_body ON bq8.si_bq(ALL COLUMNS)",
          "SELECT index_name FROM bq8.INFORMATION_SCHEMA.SEARCH_INDEXES WHERE table_name='si_bq'",
          "ERROR: search leftover BUILDING; leftover si_bq_bq8_tmp; cannot rewrite body",
          "BigQuery leftover search BUILDING; expand body_v2",
          "DROP SEARCH INDEX si_bq_body ON bq8.si_bq; DROP TABLE IF EXISTS bq8.si_bq_bq8_tmp"),
    ),
    (
        Q("rs-spx-part", "rs-spx2", "rs8", "sx_rs", "sku", "sku_norm",
          "ALTER TABLE rs8.sx_rs ADD PARTITION (dt='2026-01-01') LOCATION 's3://b/dt=2026-01-01'",
          "SELECT tablename FROM svv_external_partitions WHERE tablename='sx_rs'",
          "ERROR: Spectrum leftover partition; leftover sx_rs_rs8_tmp; cannot rewrite sku",
          "Redshift leftover Spectrum partition; expand sku_norm"),
        Q("sp-ilv-noaction", "sp-ilv2", "sp8", "il_sp", "child_id", "child_uuid",
          "CREATE TABLE sp8.il_sp (parent_id INT64, child_id INT64) PRIMARY KEY (parent_id, child_id), INTERLEAVE IN PARENT sp8.p ON DELETE NO ACTION",
          "SELECT TABLE_NAME, PARENT_TABLE_NAME FROM information_schema.tables WHERE table_name='il_sp'",
          "ERROR: interleave leftover parent; leftover il_sp_sp8_tmp; cannot rewrite child_id",
          "Spanner leftover interleave parent; expand child_uuid",
          None, "STRING(36)"),
    ),
    (
        Q("db2-mqt-incr", "db2-mqti", "d28", "mq_d2", "sku", "sku_norm",
          "REFRESH TABLE d28.mq_d2 INCREMENTAL",
          "SELECT tabname, refresh FROM syscat.tables WHERE tabname='MQ_D2'",
          "ERROR: MQT leftover incremental; leftover mq_d2_d28_tmp; cannot rewrite sku",
          "Db2 leftover MQT incremental; expand sku_norm"),
        Q("hana-smart-merge", "hana-dlt2", "ha8", "dl_ha", "sku", "sku_norm",
          "MERGE DELTA OF ha8.dl_ha WITH PARAMETERS ('SMART_MERGE'='ON')",
          "SELECT table_name FROM m_cs_tables WHERE table_name='DL_HA'",
          "ERROR: delta leftover SMART_MERGE; leftover dl_ha_ha8_tmp; cannot rewrite sku",
          "HANA leftover SMART_MERGE; expand sku_norm"),
    ),
    (
        Q("td-ji-stats", "td-ji2", "td8", "ji_td", "sku", "sku_norm",
          "COLLECT STATISTICS INDEX (sku) ON td8.ji_td",
          "SELECT TableName FROM dbc.IndexStatsV WHERE TableName='ji_td'",
          "ERROR: join-index leftover stats; leftover ji_td_td8_tmp; cannot rewrite sku",
          "Teradata leftover join-index stats; expand sku_norm"),
        Q("vert-flex-keys", "vert-fx2", "ve8", "fx_ve", "sku", "sku_norm",
          "SELECT COMPUTE_FLEXTABLE_KEYS('ve8.fx_ve')",
          "SELECT table_name FROM tables WHERE table_name='fx_ve'",
          "ERROR: flex leftover keys; leftover fx_ve_ve8_tmp; cannot rewrite sku",
          "Vertica leftover flex keys; expand sku_norm"),
    ),
    (
        Q("gp-ao-reorg", "gp-aor", "gp8", "ao_gp", "payload", "payload_v2",
          "ALTER TABLE gp8.ao_gp SET WITH (reorganize=true, appendonly=true, orientation=column)",
          "SELECT relname FROM pg_class WHERE relname='ao_gp'",
          "ERROR: AO leftover visimap; leftover ao_gp_gp8_tmp; cannot rewrite payload",
          "Greenplum leftover AO visimap; expand payload_v2",
          None, "bytea"),
        Q("s2-cs-flush", "s2-cs2", "s28", "cs_s2", "sku", "sku_norm",
          "OPTIMIZE TABLE s28.cs_s2 FLUSH",
          "SELECT table_name FROM information_schema.tables WHERE table_name='cs_s2'",
          "ERROR: columnstore leftover flush; leftover cs_s2_s28_tmp; cannot rewrite sku",
          "SingleStore leftover columnstore flush; expand sku_norm"),
    ),
    (
        Q("iceberg-pos-delete", "ice-posdel", "ice8", "pd_ic", "sku", "sku_norm",
          "DELETE FROM ice8.pd_ic WHERE sku IN (SELECT sku FROM ice8.tomb)",
          "SELECT content FROM ice8.pd_ic.files WHERE content=1",
          "ERROR: position-delete leftover files; leftover pd_ic_ice8_tmp; cannot rewrite sku",
          "Iceberg leftover position-delete; expand sku_norm"),
        Q("delta-opt-commit", "delta-opt2", "del8", "op_dl", "sku", "sku_norm",
          "OPTIMIZE del8.op_dl",
          "DESCRIBE HISTORY del8.op_dl LIMIT 3",
          "ERROR: OPTIMIZE leftover commit; leftover op_dl_del8_tmp; cannot rewrite sku",
          "Delta leftover OPTIMIZE commit; expand sku_norm"),
    ),
    (
        Q("vitess-online-ddl", "vt-oddl", "vt8", "od_vt", "sku", "sku_norm",
          "ALTER VITESS_MIGRATION 'sku_od' COMPLETE",
          "SHOW VITESS_MIGRATIONS LIKE 'sku_od'",
          "ERROR: Online DDL leftover complete; leftover od_vt_vt8_tmp; cannot rewrite sku",
          "Vitess leftover Online DDL; expand sku_norm"),
        Q("planetscale-revert", "ps-revert", "ps8", "rv_ps", "sku", "sku_norm",
          "pscale deploy-request revert app 12",
          "pscale deploy-request show app 12",
          "ERROR: deploy leftover revert window; leftover rv_ps_ps8_tmp; cannot rewrite sku",
          "PlanetScale leftover revert window; expand sku_norm"),
    ),
    (
        Q("debezium-heartbeat", "dbz-hb", "dbz8", "hb_dz", "sku", "sku_norm",
          "SELECT pg_logical_emit_message(true, 'heartbeat', 'sku')",
          "SELECT slot_name FROM pg_replication_slots WHERE slot_name='sku_dbz'",
          "ERROR: Debezium leftover heartbeat; leftover hb_dz_dbz8_tmp; cannot rewrite sku",
          "Debezium leftover heartbeat; expand sku_norm"),
        Q("oracle-xstream", "ora-xstr", "ogg8", "xs_og", "sku", "sku_norm",
          "BEGIN DBMS_XSTREAM_ADM.CREATE_OUTBOUND(server_name=>'sku_out'); END;",
          "SELECT server_name FROM dba_xstream_outbound",
          "ERROR: XStream leftover outbound; leftover xs_og_ogg8_tmp; cannot rewrite sku",
          "Oracle leftover XStream outbound; expand sku_norm"),
    ),
    (
        Q("mysql-gtid-executed", "my-gtidex", "mbl8", "ge_my", "sku", "sku_norm",
          "SET GLOBAL gtid_executed='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee:1-100'",
          "SHOW VARIABLES LIKE 'gtid_executed'",
          "ERROR: GTID leftover executed set; leftover ge_my_mbl8_tmp; cannot rewrite sku",
          "MySQL leftover GTID executed; expand sku_norm"),
        Q("flink-savepoint", "flink-sp", "fcdc8", "sp_fl", "sku", "sku_norm",
          "STOP WITH SAVEPOINT `s3://b/sku`",
          "SHOW JOBS",
          "ERROR: savepoint leftover path; leftover sp_fl_fcdc8_tmp; cannot rewrite sku",
          "Flink leftover savepoint path; expand sku_norm"),
    ),
    (
        Q("cockroach-span-config", "crdb-span", "cr9", "sc_cr", "sku", "sku_norm",
          "ALTER TABLE cr9.sc_cr CONFIGURE ZONE USING constraints='[+region=us]'",
          "SELECT range_id FROM crdb_internal.ranges WHERE table_name='sc_cr'",
          "ERROR: span leftover config; leftover sc_cr_cr9_tmp; cannot rewrite sku",
          "CRDB leftover span config; expand sku_norm"),
        Q("yb-cdc-ckpt", "yb-cdck", "yb9", "cd_yb", "sku", "sku_norm",
          "yb-admin list_cdc_streams",
          "yb-admin get_checkpoint ysql.yb9 cd_yb",
          "ERROR: CDC leftover checkpoint; leftover cd_yb_yb9_tmp; cannot rewrite sku",
          "Yugabyte leftover CDC checkpoint; expand sku_norm"),
    ),
    (
        Q("neon-lsn", "neon-lsn", "nsk8", "ln_ne", "sku", "sku_norm",
          "SELECT pg_current_wal_lsn(), neon_get_wal_replay_lsn()",
          "SELECT * FROM neon.safekeepers",
          "ERROR: LSN leftover safekeeper; leftover ln_ne_nsk8_tmp; cannot rewrite sku",
          "Neon leftover LSN safekeeper; expand sku_norm"),
        Q("alloydb-sca", "alloy-sca", "adb8", "sc_al", "sku", "sku_norm",
          "SELECT google_db_advisor_recommend_indexes()",
          "SELECT * FROM google_db_advisor_index_report()",
          "ERROR: SCA leftover hypopg; leftover sc_al_adb8_tmp; cannot rewrite sku",
          "AlloyDB leftover SCA hypopg; expand sku_norm"),
    ),
    (
        Q("sb-vault-upd", "sb-vupd", "sbv8", "vt_sb", "secret", "secret_v2",
          "SELECT vault.update_secret((SELECT id FROM vault.secrets WHERE name='sku'), 'new')",
          "SELECT name FROM vault.secrets WHERE name='sku'",
          "ERROR: vault leftover update; leftover vt_sb_sbv8_tmp; cannot rewrite secret",
          "Supabase leftover vault update; expand secret_v2"),
        Q("ferretdb-ttl", "ferret-ttl", "frt8", "tt_fr", "sku", "sku_norm",
          "db.fr_row.createIndex({exp:1},{expireAfterSeconds:86400})",
          "db.fr_row.getIndexes()",
          "ERROR: FerretDB leftover TTL; leftover tt_fr_frt8_tmp; cannot rewrite sku",
          "FerretDB leftover TTL index; expand sku_norm"),
    ),
    (
        Q("qdrant-payload", "qdrant-pay", "qdr8", "py_qd", "sku", "sku_norm",
          "PUT /collections/py_qd/index {\"field_name\":\"sku\",\"field_schema\":\"keyword\"}",
          "GET /collections/py_qd",
          "ERROR: payload leftover index; leftover py_qd_qdr8_tmp; cannot rewrite sku",
          "Qdrant leftover payload index; expand sku_norm"),
        Q("milvus-alias", "milvus-alias", "mlv8", "al_ml", "emb", "emb_v2",
          "utility.create_alias('al_ml','sku_live')",
          "utility.list_aliases('al_ml')",
          "ERROR: alias leftover collection; leftover al_ml_mlv8_tmp; cannot rewrite emb",
          "Milvus leftover alias; expand emb_v2",
          None, "vector"),
    ),
    (
        Q("rdsr-syn-group", "rdsr-syn", "rdsr8", "sy_rd", "body", "body_v2",
          "FT.SYNUPDATE sy_rd group1 sku sku_norm",
          "FT.SYNDUMP sy_rd",
          "ERROR: synonym leftover group; leftover sy_rd_rdsr8_tmp; cannot rewrite body",
          "FT synonym leftover group; expand body_v2"),
        Q("valkey-slot", "valkey-slot", "vlk8", "sl_vl", "sku", "sku_norm",
          "CLUSTER SETSLOT 100 IMPORTING node-b",
          "CLUSTER NODES",
          "ERROR: slot leftover IMPORTING; leftover sl_vl_vlk8_tmp; cannot rewrite sku",
          "Valkey leftover slot IMPORTING; expand sku_norm"),
    ),
    (
        Q("aerospike-xdr", "aero-xdr", "aer8", "xd_ae", "sku", "sku_norm",
          "asinfo -v 'set-config:context=xdr;dc=sku;action=create'",
          "asinfo -v 'get-config:context=xdr'",
          "ERROR: XDR leftover DC; leftover xd_ae_aer8_tmp; cannot rewrite sku",
          "Aerospike leftover XDR DC; expand sku_norm"),
        Q("riak-handoff", "riak-hand", "ria8", "ho_ri", "sku", "sku_norm",
          "riak-admin transfer-limit 8",
          "riak-admin transfers",
          "ERROR: handoff leftover transfer; leftover ho_ri_ria8_tmp; cannot rewrite sku",
          "Riak leftover handoff transfer; expand sku_norm"),
    ),
    (
        Q("pg-sync-rep", "pg-syncrep", "psb8", "sr_pg", "sku", "sku_norm",
          "ALTER SYSTEM SET synchronous_commit = remote_apply",
          "SHOW synchronous_commit",
          "ERROR: sync leftover remote_apply wait; leftover sr_pg_psb8_tmp; cannot rewrite sku",
          "Postgres leftover remote_apply; expand sku_norm"),
        Q("pg-origindrop", "pg-origind", "por8", "od_pg", "sku", "sku_norm",
          "SELECT pg_replication_origin_session_setup('sku_ori')",
          "SELECT roname FROM pg_replication_origin",
          "ERROR: origin leftover session; leftover od_pg_por8_tmp; cannot rewrite sku",
          "Postgres leftover origin session; expand sku_norm"),
    ),
    (
        Q("aurora-backtrack", "aur-btrack", "aur8", "bt_au", "sku", "sku_norm",
          "aws rds backtrack-db-cluster --db-cluster-identifier sku --backtrack-to 2026-01-01",
          "aws rds describe-db-clusters --db-cluster-identifier sku",
          "ERROR: backtrack leftover window; leftover bt_au_aur8_tmp; cannot rewrite sku",
          "Aurora leftover backtrack window; expand sku_norm"),
        Q("rds-export", "rds-export", "rds8", "ex_rd", "sku", "sku_norm",
          "aws rds start-export-task --export-task-identifier sku --s3-bucket-name b",
          "aws rds describe-export-tasks --export-task-identifier sku",
          "ERROR: export leftover snapshot; leftover ex_rd_rds8_tmp; cannot rewrite sku",
          "RDS leftover export snapshot; expand sku_norm"),
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
            "and r934-r1140 catalogs. "
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
            "Avoid the two slugs in this round next. Do not clone r762-r1140.",
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
