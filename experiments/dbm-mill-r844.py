#!/usr/bin/env python3
"""Mill db-migration-repair-factory r844+ as NEW pg-catalog semantic plants.

BAN r1–r817 recycle / warehouse / ORM-CLI mills.
BAN r818–r843 catalog plants already published (see BANNED_NEEDLES).
BAN r843 tablespace-set-already-skip / amcheck-rootdescend-unique-dups.
Semantic mill: first-apply fail + plan change + lock retry + expand-contract.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FACTORY = "db-migration-repair-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 844
SURFACE = "pg-catalog-semantics"

BANNED_NEEDLES = (
    "tablespace-set-already-skip",
    "amcheck-rootdescend",
    "concurrent-unique",
    "fk-not-valid",
    "check-not-valid",
    "generated-set-expression",
    "partition-attach-fk",
    "replica-identity-full",
    "toast-rewrite",
    "repack-already",
    "unique-nulls-not-distinct",
    "not-null-not-valid",
    "publish-generated",
    "logical-failover",
    "detach-concurrent",
    "set-access-method",
    "lz4-compression",
    "cluster-using",
    "vacuum-full",
    "constraint-not-enforced",
    "split-default-partition",
    "subscription-disable",
    "event-trigger-table-rewrite",
    "collation-refresh",
    "identity-by-default",
    "matview-unique-index",
    "domain-not-valid",
    "exclusion-multirange",
    "rls-force-row",
    "replica-identity-using",
    "fk-match-full",
    "deferrable-unique",
    "generated-virtual",
    "merge-into",
    "jsonpath-exists",
    "hot-standby-feedback",
    "wal-compression",
    "old-snapshot",
    "pgoutput-row-filter",
    "security-invoker",
    "icu-locale",
    "nfc-normalization",
    "relfrozenxid",
    "multixact-freeze",
    "brin-desummarize",
    "gin-fastupdate",
    "spgist-text",
    "btree-dedup",
    "hash-index-bucket",
    "tid-range-scan",
    "xmltable",
    "fillfactor",
)


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, name: str, args: dict, obs: str) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }


def bash(n: int, basis: str, cmd: str, obs: str) -> dict:
    return step(n, basis, "bash", {"command": cmd}, obs)


def write_step(n: int, basis: str, path: str, contents: str, obs: str) -> dict:
    return step(n, basis, "write", {"path": path, "contents": contents}, obs)


def P(
    slug: str,
    plant: str,
    schema: str,
    table: str,
    old: str,
    new: str,
    seed: str,
    inspect: str,
    fail: str,
    catalog: str,
    tmp: str,
    leftover: str,
    abort: str,
    coltype: str = "text",
) -> dict:
    return {
        "slug": slug,
        "plant": plant,
        "schema": schema,
        "table": table,
        "old": old,
        "new": new,
        "seed": seed,
        "inspect": inspect,
        "fail": fail,
        "catalog": catalog,
        "tmp": tmp,
        "leftover": leftover,
        "abort": abort,
        "coltype": coltype,
        "qual": f"{schema}.{table}",
    }


# Each pair is (success-style ep A, success-style ep B). Indexed by round-844.
# Unique pg_catalog leftovers that force expand-contract. Not CLI clones.
PAIRS: list[tuple[dict, dict]] = [
    (
        P(
            "stats-ext-ndistinct-leftover",
            "stats-ext-ndistinct",
            "analytics",
            "sku_hist",
            "sku",
            "sku_norm",
            'CREATE STATISTICS sku_hist_nd (ndistinct) ON sku, region FROM analytics.sku_hist',
            "SELECT stxname, stxkind, stxstattarget FROM pg_statistic_ext WHERE stxrelid='analytics.sku_hist'::regclass",
            "ERROR: 42P17 extended stats sku_hist_nd leftover stxdinherit after aborted ALTER; cannot rewrite sku in place; leftover sku_hist_nd_tmp",
            "pg_statistic_ext ndistinct leftover; expand sku_norm",
            "sku_hist_nd_tmp",
            "INVALID sku_hist_nd + sku_hist_nd_tmp",
            "DROP STATISTICS IF EXISTS analytics.sku_hist_nd_tmp",
        ),
        P(
            "publication-via-partition-root",
            "pub-via-part-root",
            "sales",
            "order_part",
            "order_id",
            "order_uuid",
            "ALTER PUBLICATION sales_pub SET (publish_via_partition_root = true)",
            "SELECT pubname, pubviaroot, puballtables FROM pg_publication WHERE pubname='sales_pub'",
            "ERROR: 0A000 publication sales_pub already publish_via_partition_root; leftover order_part_pub_tmp; cannot rewrite order_id",
            "pg_publication pubviaroot leftover; expand order_uuid",
            "order_part_pub_tmp",
            "sales_pub pubviaroot + order_part_pub_tmp",
            "DROP TABLE IF EXISTS sales.order_part_pub_tmp",
            "uuid",
        ),
    ),
    (
        P(
            "toast-tuple-target-already-skip",
            "toast-tuple-target",
            "payload",
            "blob_row",
            "payload",
            "payload_v2",
            "ALTER TABLE payload.blob_row SET (toast_tuple_target = 128)",
            "SELECT relname, reloptions FROM pg_class WHERE oid='payload.blob_row'::regclass",
            "NOTICE: already skip: toast_tuple_target already 128; leftover blob_row_toast_tmp + toast pointer dual",
            "reloption toast_tuple_target already-skip leftover tmp; expand payload_v2",
            "blob_row_toast_tmp",
            "blob_row.payload + payload_v2; leftover blob_row_toast_tmp",
            "DROP TABLE IF EXISTS payload.blob_row_toast_tmp",
            "bytea",
        ),
        P(
            "vacuum-index-cleanup-off",
            "vac-idx-cleanup-off",
            "ops",
            "event_log",
            "payload",
            "payload_v2",
            "VACUUM (INDEX_CLEANUP OFF, VERBOSE) ops.event_log",
            "SELECT relname, relpages, reltuples FROM pg_class WHERE oid='ops.event_log'::regclass",
            "ERROR: 25001 VACUUM INDEX_CLEANUP OFF leftover after rewrite abort; cannot rewrite payload; leftover event_log_vac_tmp",
            "VACUUM INDEX_CLEANUP OFF leftover; expand payload_v2",
            "event_log_vac_tmp",
            "event_log.payload + payload_v2; leftover event_log_vac_tmp",
            "DROP TABLE IF EXISTS ops.event_log_vac_tmp",
            "bytea",
        ),
    ),
    (
        P(
            "enum-add-value-if-not-exists",
            "enum-add-value",
            "catalog",
            "item_kind",
            "kind",
            "kind_v2",
            "ALTER TYPE catalog.item_kind_t ADD VALUE IF NOT EXISTS 'archived' BEFORE 'active'",
            "SELECT enumlabel, enumsortorder FROM pg_enum e JOIN pg_type t ON t.oid=e.enumtypid WHERE t.typname='item_kind_t' ORDER BY enumsortorder",
            "ERROR: 55P04 unsafe to use new enum value 'archived' before commit; leftover item_kind_enum_tmp; cannot rewrite kind",
            "pg_enum ADD VALUE leftover before commit; expand kind_v2",
            "item_kind_enum_tmp",
            "item_kind.kind + kind_v2; leftover item_kind_enum_tmp",
            "DROP TABLE IF EXISTS catalog.item_kind_enum_tmp",
        ),
        P(
            "sequence-cycle-owned-none",
            "seq-cycle-owned-none",
            "billing",
            "invoice",
            "number",
            "number_v2",
            "ALTER SEQUENCE billing.invoice_number_seq CYCLE; ALTER SEQUENCE billing.invoice_number_seq OWNED BY NONE",
            "SELECT sequencename, cycle, owned_by FROM pg_sequences WHERE schemaname='billing' AND sequencename='invoice_number_seq'",
            "ERROR: 2BP01 sequence owned-by-none leftover after CYCLE; invoice.number rewrite refused; leftover invoice_seq_tmp",
            "pg_sequences cycle+owned_by NONE leftover; expand number_v2",
            "invoice_seq_tmp",
            "invoice.number + number_v2; leftover invoice_seq_tmp",
            "DROP TABLE IF EXISTS billing.invoice_seq_tmp",
            "bigint",
        ),
    ),
    (
        P(
            "policy-restrictive-vs-permissive",
            "policy-restrictive",
            "tenant",
            "row_acl",
            "tenant_id",
            "tenant_uuid",
            "CREATE POLICY p_restrict AS RESTRICTIVE ON tenant.row_acl FOR SELECT USING (tenant_id = current_setting('app.tid')::int)",
            "SELECT polname, polpermissive, polcmd FROM pg_policy WHERE polrelid='tenant.row_acl'::regclass",
            "ERROR: 42501 RESTRICTIVE policy p_restrict leftover after aborted SET; cannot rewrite tenant_id; leftover row_acl_pol_tmp",
            "pg_policy polpermissive=false leftover; expand tenant_uuid",
            "row_acl_pol_tmp",
            "row_acl.tenant_id + tenant_uuid; leftover row_acl_pol_tmp",
            "DROP POLICY IF EXISTS p_restrict ON tenant.row_acl; DROP TABLE IF EXISTS tenant.row_acl_pol_tmp",
            "uuid",
        ),
        P(
            "view-security-barrier-rewrite",
            "view-sec-barrier",
            "report",
            "v_sales",
            "amount",
            "amount_v2",
            "CREATE VIEW report.v_sales WITH (security_barrier=true) AS SELECT amount FROM report.sales_fact",
            "SELECT relname, relkind, reloptions FROM pg_class WHERE oid='report.v_sales'::regclass",
            "ERROR: 42P16 view rewrite with security_barrier leftover v_sales_tmp; cannot in-place replace amount",
            "view security_barrier leftover rewrite tmp; expand amount_v2",
            "v_sales_tmp",
            "v_sales.amount + amount_v2; leftover v_sales_tmp",
            "DROP VIEW IF EXISTS report.v_sales_tmp",
            "numeric",
        ),
    ),
    (
        P(
            "foreign-table-options-leftover",
            "ft-options",
            "fdw",
            "remote_sku",
            "sku",
            "sku_norm",
            "ALTER FOREIGN TABLE fdw.remote_sku OPTIONS (SET schema_name 'prod')",
            "SELECT ftrelid::regclass, ftoptions FROM pg_foreign_table WHERE ftrelid='fdw.remote_sku'::regclass",
            "ERROR: HV000 OPTIONS leftover schema_name=prod on fdw.remote_sku_tmp; cannot rewrite sku",
            "pg_foreign_table ftoptions leftover; expand sku_norm",
            "remote_sku_tmp",
            "remote_sku.sku + sku_norm; leftover remote_sku_tmp",
            "DROP FOREIGN TABLE IF EXISTS fdw.remote_sku_tmp",
        ),
        P(
            "partition-hash-modulus-mismatch",
            "hash-modulus",
            "shard",
            "item_h",
            "sku",
            "sku_norm",
            "ALTER TABLE shard.item_h ATTACH PARTITION shard.item_h_2 FOR VALUES WITH (modulus 4, remainder 2)",
            "SELECT c.relname, c.relpartbound FROM pg_class c WHERE c.relname LIKE 'item_h%' ORDER BY 1",
            "ERROR: 42P17 modulus 4 vs existing 8 leftover item_h_2_tmp; cannot rewrite sku",
            "hash partition modulus mismatch leftover; expand sku_norm",
            "item_h_2_tmp",
            "item_h.sku + sku_norm; leftover item_h_2_tmp",
            "DROP TABLE IF EXISTS shard.item_h_2_tmp",
        ),
    ),
    (
        P(
            "bloom-length-signature-leftover",
            "bloom-length",
            "kv",
            "bloom_map",
            "k",
            "k_hash",
            "CREATE INDEX CONCURRENTLY bloom_map_k_bloom ON kv.bloom_map USING bloom (k) WITH (length=80)",
            "SELECT indexrelid::regclass, indisvalid, reloptions FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE i.indrelid='kv.bloom_map'::regclass",
            "ERROR: 23505 bloom length=80 leftover INVALID bloom_map_k_bloom; leftover bloom_map_bloom_tmp",
            "bloom index length leftover INVALID; expand k_hash",
            "bloom_map_bloom_tmp",
            "INVALID bloom_map_k_bloom + bloom_map_bloom_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS kv.bloom_map_k_bloom; DROP TABLE IF EXISTS kv.bloom_map_bloom_tmp",
        ),
        P(
            "gist-buffering-build-leftover",
            "gist-buffering",
            "geo",
            "place",
            "geom",
            "geom_v2",
            "CREATE INDEX CONCURRENTLY place_geom_gix ON geo.place USING gist (geom) WITH (buffering=on)",
            "SELECT indexrelid::regclass, indisvalid FROM pg_index WHERE indrelid='geo.place'::regclass",
            "ERROR: 57014 gist buffering=on build leftover INVALID place_geom_gix; leftover place_gist_tmp",
            "GiST buffering build leftover INVALID; expand geom_v2",
            "place_gist_tmp",
            "INVALID place_geom_gix + place_gist_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS geo.place_geom_gix; DROP TABLE IF EXISTS geo.place_gist_tmp",
            "geometry",
        ),
    ),
    (
        P(
            "brin-minmax-multi-pages",
            "brin-minmax-multi",
            "iot",
            "sample",
            "ts",
            "ts_v2",
            "CREATE INDEX CONCURRENTLY sample_ts_brin ON iot.sample USING brin (ts minmax_multi_ops) WITH (pages_per_range=16, autosummarize=on)",
            "SELECT opcname, indexrelid::regclass, indisvalid FROM pg_index i JOIN pg_opclass o ON o.oid=i.indclass[0] WHERE i.indrelid='iot.sample'::regclass",
            "ERROR: 57014 brin minmax_multi leftover INVALID sample_ts_brin; leftover sample_brin_tmp",
            "BRIN minmax_multi pages_per_range leftover INVALID; expand ts_v2",
            "sample_brin_tmp",
            "INVALID sample_ts_brin + sample_brin_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS iot.sample_ts_brin; DROP TABLE IF EXISTS iot.sample_brin_tmp",
            "timestamptz",
        ),
        P(
            "pg-trgm-gin-pending-list",
            "trgm-gin-pending",
            "search",
            "token",
            "tok",
            "tok_norm",
            "CREATE INDEX CONCURRENTLY token_trgm ON search.token USING gin (tok gin_trgm_ops)",
            "SELECT indexrelid::regclass, indisvalid FROM pg_index WHERE indrelid='search.token'::regclass",
            "ERROR: 23505 gin_trgm pending list leftover INVALID token_trgm; leftover token_trgm_tmp",
            "gin_trgm_ops pending-list leftover INVALID; expand tok_norm",
            "token_trgm_tmp",
            "INVALID token_trgm + token_trgm_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS search.token_trgm; DROP TABLE IF EXISTS search.token_trgm_tmp",
        ),
    ),
    (
        P(
            "citext-unique-cast-leftover",
            "citext-unique-cast",
            "auth",
            "login",
            "email",
            "email_norm",
            "CREATE UNIQUE INDEX CONCURRENTLY login_email_citext ON auth.login ((email::citext))",
            "SELECT indexrelid::regclass, indisunique, indisvalid FROM pg_index WHERE indrelid='auth.login'::regclass",
            "ERROR: 23505 citext unique vs text unique leftover INVALID login_email_citext; leftover login_citext_tmp",
            "citext unique cast leftover INVALID; expand email_norm",
            "login_citext_tmp",
            "INVALID login_email_citext + login_citext_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS auth.login_email_citext; DROP TABLE IF EXISTS auth.login_citext_tmp",
        ),
        P(
            "ltree-gist-ops-rebuild",
            "ltree-gist-ops",
            "taxonomy",
            "path_node",
            "path",
            "path_v2",
            "CREATE INDEX CONCURRENTLY path_node_ltree ON taxonomy.path_node USING gist (path gist_ltree_ops)",
            "SELECT opcname, indexrelid::regclass, indisvalid FROM pg_index i JOIN pg_opclass o ON o.oid=i.indclass[0] WHERE i.indrelid='taxonomy.path_node'::regclass",
            "ERROR: 57014 gist_ltree_ops leftover INVALID path_node_ltree; leftover path_ltree_tmp",
            "gist_ltree_ops leftover INVALID; expand path_v2",
            "path_ltree_tmp",
            "INVALID path_node_ltree + path_ltree_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS taxonomy.path_node_ltree; DROP TABLE IF EXISTS taxonomy.path_ltree_tmp",
            "ltree",
        ),
    ),
    (
        P(
            "hstore-gin-pending-leftover",
            "hstore-gin-pending",
            "kv",
            "hstore_row",
            "extra",
            "extra_v2",
            "CREATE INDEX CONCURRENTLY hstore_row_gin ON kv.hstore_row USING gin (extra gin_hstore_ops)",
            "SELECT indexrelid::regclass, indisvalid FROM pg_index WHERE indrelid='kv.hstore_row'::regclass",
            "ERROR: 23505 gin_hstore pending leftover INVALID hstore_row_gin; leftover hstore_gin_tmp",
            "gin_hstore_ops pending leftover INVALID; expand extra_v2",
            "hstore_gin_tmp",
            "INVALID hstore_row_gin + hstore_gin_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS kv.hstore_row_gin; DROP TABLE IF EXISTS kv.hstore_gin_tmp",
            "hstore",
        ),
        P(
            "intarray-gist-ops-leftover",
            "intarray-gist-ops",
            "tag",
            "int_set",
            "ids",
            "ids_v2",
            "CREATE INDEX CONCURRENTLY int_set_gist ON tag.int_set USING gist (ids gist__int_ops)",
            "SELECT opcname, indexrelid::regclass, indisvalid FROM pg_index i JOIN pg_opclass o ON o.oid=i.indclass[0] WHERE i.indrelid='tag.int_set'::regclass",
            "ERROR: 57014 gist__int_ops leftover INVALID int_set_gist; leftover int_set_gist_tmp",
            "gist__int_ops leftover INVALID; expand ids_v2",
            "int_set_gist_tmp",
            "INVALID int_set_gist + int_set_gist_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS tag.int_set_gist; DROP TABLE IF EXISTS tag.int_set_gist_tmp",
            "integer[]",
        ),
    ),
    (
        P(
            "btree-gist-exclude-circle",
            "btree-gist-exclude",
            "booking",
            "slot",
            "when_range",
            "when_range_v2",
            "ALTER TABLE booking.slot ADD CONSTRAINT slot_excl EXCLUDE USING gist (when_range WITH &&)",
            "SELECT conname, contype, convalidated, condeferrable FROM pg_constraint WHERE conrelid='booking.slot'::regclass",
            "ERROR: 23P01 EXCLUDE gist leftover NOT VALID slot_excl; leftover slot_excl_tmp",
            "EXCLUDE USING gist leftover NOT VALID; expand when_range_v2",
            "slot_excl_tmp",
            "NOT VALID slot_excl + slot_excl_tmp",
            "ALTER TABLE booking.slot DROP CONSTRAINT IF EXISTS slot_excl; DROP TABLE IF EXISTS booking.slot_excl_tmp",
            "tstzrange",
        ),
        P(
            "range-canonical-fn-mismatch",
            "range-canonical",
            "sched",
            "win",
            "span",
            "span_v2",
            "ALTER TYPE sched.win_range SET (CANONICAL = sched.win_canonical)",
            "SELECT rngtypid::regtype, rngcanonical FROM pg_range WHERE rngtypid='sched.win_range'::regtype",
            "ERROR: 42809 canonical fn mismatch leftover win_range_tmp; cannot rewrite span",
            "pg_range rngcanonical leftover; expand span_v2",
            "win_range_tmp",
            "win.span + span_v2; leftover win_range_tmp",
            "DROP TABLE IF EXISTS sched.win_range_tmp",
            "sched.win_range",
        ),
    ),
    (
        P(
            "attislocal-inherited-column",
            "attislocal-inherit",
            "inherit",
            "child_row",
            "note",
            "note_v2",
            "ALTER TABLE inherit.child_row ADD COLUMN note text",
            "SELECT attname, attislocal, attinhcount FROM pg_attribute WHERE attrelid='inherit.child_row'::regclass AND attname='note'",
            "ERROR: 42P16 attislocal=false leftover on child_row.note (inherited); cannot rewrite; leftover child_row_inh_tmp",
            "pg_attribute attislocal leftover; expand note_v2",
            "child_row_inh_tmp",
            "child_row.note + note_v2; leftover child_row_inh_tmp",
            "DROP TABLE IF EXISTS inherit.child_row_inh_tmp",
        ),
        P(
            "extension-update-path-missing",
            "ext-update-path",
            "ext",
            "pkg_row",
            "ver",
            "ver_v2",
            "ALTER EXTENSION pkg UPDATE TO '2.0'",
            "SELECT extname, extversion FROM pg_extension WHERE extname='pkg'",
            "ERROR: 22023 no update path 1.4 -> 2.0 leftover pkg_ext_tmp; cannot rewrite ver",
            "pg_extension missing update path leftover; expand ver_v2",
            "pkg_ext_tmp",
            "pkg_row.ver + ver_v2; leftover pkg_ext_tmp",
            "DROP TABLE IF EXISTS ext.pkg_ext_tmp",
        ),
    ),
    (
        P(
            "fdw-user-mapping-options",
            "um-options",
            "fdw",
            "map_row",
            "ident",
            "ident_v2",
            "ALTER USER MAPPING FOR app SERVER src OPTIONS (SET password_required 'false')",
            "SELECT umuser::regrole, umoptions FROM pg_user_mapping u JOIN pg_foreign_server s ON s.oid=u.umserver WHERE s.srvname='src'",
            "ERROR: 28000 user mapping leftover password_required; leftover map_um_tmp; cannot rewrite ident",
            "pg_user_mapping umoptions leftover; expand ident_v2",
            "map_um_tmp",
            "map_row.ident + ident_v2; leftover map_um_tmp",
            "DROP TABLE IF EXISTS fdw.map_um_tmp",
        ),
        P(
            "postgres-fdw-remote-estimate",
            "fdw-remote-est",
            "fdw",
            "est_row",
            "cost_hint",
            "cost_hint_v2",
            "ALTER SERVER src OPTIONS (SET use_remote_estimate 'true')",
            "SELECT srvname, srvoptions FROM pg_foreign_server WHERE srvname='src'",
            "ERROR: HV00N use_remote_estimate leftover on server src; leftover est_fdw_tmp; cannot rewrite cost_hint",
            "postgres_fdw use_remote_estimate leftover; expand cost_hint_v2",
            "est_fdw_tmp",
            "est_row.cost_hint + cost_hint_v2; leftover est_fdw_tmp",
            "DROP TABLE IF EXISTS fdw.est_fdw_tmp",
            "numeric",
        ),
    ),
    (
        P(
            "matview-with-no-data-refresh",
            "mv-no-data",
            "report",
            "mv_sku",
            "sku",
            "sku_norm",
            "REFRESH MATERIALIZED VIEW report.mv_sku WITH NO DATA",
            "SELECT relname, relispopulated, relkind FROM pg_class WHERE oid='report.mv_sku'::regclass",
            "ERROR: 55000 mv_sku not populated leftover mv_sku_tmp; unique index INVALID; cannot rewrite sku",
            "matview WITH NO DATA leftover unpopulated; expand sku_norm",
            "mv_sku_tmp",
            "mv_sku.sku + sku_norm; leftover mv_sku_tmp + INVALID mv_sku_sku_uidx",
            "DROP MATERIALIZED VIEW IF EXISTS report.mv_sku_tmp",
        ),
        P(
            "vacuum-truncate-off-skip",
            "vac-truncate-off",
            "archive",
            "old_row",
            "body",
            "body_v2",
            "VACUUM (TRUNCATE OFF) archive.old_row",
            "SELECT relname, relpages, reltuples FROM pg_class WHERE oid='archive.old_row'::regclass",
            "NOTICE: already skip: vacuum truncate off (empty pages kept); leftover old_row_vac_tmp; cannot rewrite body",
            "VACUUM TRUNCATE OFF leftover empty pages; expand body_v2",
            "old_row_vac_tmp",
            "old_row.body + body_v2; leftover old_row_vac_tmp",
            "DROP TABLE IF EXISTS archive.old_row_vac_tmp",
            "bytea",
        ),
    ),
    (
        P(
            "on-conflict-arbiter-infer",
            "onconflict-arbiter",
            "shop",
            "upsert_sku",
            "sku",
            "sku_norm",
            "INSERT INTO shop.upsert_sku(sku) VALUES ('x') ON CONFLICT (sku) DO UPDATE SET sku = EXCLUDED.sku",
            "SELECT indexrelid::regclass, indisunique, indisvalid FROM pg_index WHERE indrelid='shop.upsert_sku'::regclass",
            "ERROR: 42P10 no unique or exclusion constraint matching ON CONFLICT specification; leftover INVALID upsert_sku_sku_key + upsert_arb_tmp",
            "ON CONFLICT arbiter inference leftover INVALID; expand sku_norm",
            "upsert_arb_tmp",
            "INVALID upsert_sku_sku_key + upsert_arb_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS shop.upsert_sku_sku_key; DROP TABLE IF EXISTS shop.upsert_arb_tmp",
        ),
        P(
            "pg-visibility-all-visible",
            "visimap-all-visible",
            "heap",
            "vis_row",
            "payload",
            "payload_v2",
            "SELECT * FROM pg_visibility('heap.vis_row'::regclass) WHERE NOT all_visible LIMIT 5",
            "SELECT relname, relpages FROM pg_class WHERE oid='heap.vis_row'::regclass",
            "ERROR: XX001 all-visible bit leftover vs heap tuple; leftover vis_row_vm_tmp; cannot rewrite payload",
            "visibility map all-visible leftover; expand payload_v2",
            "vis_row_vm_tmp",
            "vis_row.payload + payload_v2; leftover vis_row_vm_tmp",
            "DROP TABLE IF EXISTS heap.vis_row_vm_tmp",
            "bytea",
        ),
    ),
    (
        P(
            "incremental-backup-summary",
            "incr-backup-summary",
            "backup",
            "incr_row",
            "lsn",
            "lsn_v2",
            "SELECT pg_backup_start('incr', true)",
            "SELECT setting FROM pg_settings WHERE name='summarize_wal'",
            "ERROR: 58P01 incremental backup summary leftover incr_row_wal_tmp; cannot rewrite lsn",
            "incremental backup summary leftover; expand lsn_v2",
            "incr_row_wal_tmp",
            "incr_row.lsn + lsn_v2; leftover incr_row_wal_tmp",
            "DROP TABLE IF EXISTS backup.incr_row_wal_tmp",
            "pg_lsn",
        ),
        P(
            "logical-two-phase-decoding",
            "logical-two-phase",
            "repl",
            "tx_row",
            "xid",
            "xid_v2",
            "ALTER SUBSCRIPTION sales_sub SET (two_phase = true)",
            "SELECT subname, subenabled, subtwophasestate FROM pg_subscription WHERE subname='sales_sub'",
            "ERROR: 55000 two_phase leftover prepared xact; leftover tx_row_2pc_tmp; cannot rewrite xid",
            "pg_subscription two_phase leftover prepared xact; expand xid_v2",
            "tx_row_2pc_tmp",
            "tx_row.xid + xid_v2; leftover tx_row_2pc_tmp",
            "DROP TABLE IF EXISTS repl.tx_row_2pc_tmp",
            "xid",
        ),
    ),
    (
        P(
            "pg-prewarm-autoprewarm",
            "prewarm-autoprewarm",
            "cache",
            "hot_row",
            "k",
            "k_v2",
            "SELECT pg_prewarm('cache.hot_row'::regclass)",
            "SELECT relname, relpages FROM pg_class WHERE oid='cache.hot_row'::regclass",
            "ERROR: 58P01 autoprewarm dump leftover hot_row_prewarm_tmp; cannot rewrite k",
            "pg_prewarm autoprewarm dump leftover; expand k_v2",
            "hot_row_prewarm_tmp",
            "hot_row.k + k_v2; leftover hot_row_prewarm_tmp",
            "DROP TABLE IF EXISTS cache.hot_row_prewarm_tmp",
        ),
        P(
            "pageinspect-bt-meta",
            "pageinspect-btmeta",
            "idx",
            "bt_row",
            "k",
            "k_norm",
            "SELECT * FROM bt_metap('idx.bt_row_k_idx')",
            "SELECT indexrelid::regclass, indisvalid FROM pg_index WHERE indrelid='idx.bt_row'::regclass",
            "ERROR: XX002 bt_metap version leftover INVALID bt_row_k_idx; leftover bt_row_inspect_tmp",
            "pageinspect bt_metap leftover INVALID; expand k_norm",
            "bt_row_inspect_tmp",
            "INVALID bt_row_k_idx + bt_row_inspect_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS idx.bt_row_k_idx; DROP TABLE IF EXISTS idx.bt_row_inspect_tmp",
        ),
    ),
    (
        P(
            "subscription-binary-leftover",
            "sub-binary",
            "repl",
            "bin_row",
            "payload",
            "payload_v2",
            "ALTER SUBSCRIPTION sales_sub SET (binary = true)",
            "SELECT subname, subbinary, substream FROM pg_subscription WHERE subname='sales_sub'",
            "ERROR: 0A000 binary leftover on subscription sales_sub; leftover bin_row_sub_tmp; cannot rewrite payload",
            "pg_subscription subbinary leftover; expand payload_v2",
            "bin_row_sub_tmp",
            "bin_row.payload + payload_v2; leftover bin_row_sub_tmp",
            "DROP TABLE IF EXISTS repl.bin_row_sub_tmp",
            "bytea",
        ),
        P(
            "replorigin-advance-leftover",
            "replorigin-advance",
            "repl",
            "origin_row",
            "lsn",
            "lsn_v2",
            "SELECT pg_replication_origin_advance('sales_origin', '0/2A00000')",
            "SELECT roname, remote_lsn, local_lsn FROM pg_replication_origin_status s JOIN pg_replication_origin o ON o.roident=s.local_id",
            "ERROR: 55000 origin advance leftover past consistent lsn; leftover origin_row_tmp; cannot rewrite lsn",
            "pg_replication_origin_advance leftover; expand lsn_v2",
            "origin_row_tmp",
            "origin_row.lsn + lsn_v2; leftover origin_row_tmp",
            "DROP TABLE IF EXISTS repl.origin_row_tmp",
            "pg_lsn",
        ),
    ),
    (
        P(
            "subscription-slot-drop-leftover",
            "sub-slot-drop",
            "repl",
            "sub_row",
            "lsn",
            "lsn_v2",
            "DROP SUBSCRIPTION IF EXISTS sales_sub",
            "SELECT slot_name, plugin, active, wal_status FROM pg_replication_slots WHERE slot_name LIKE 'sales_%'",
            "ERROR: 2BP01 cannot drop subscription: slot sales_sub leftover; leftover sub_drop_tmp; cannot rewrite lsn",
            "DROP SUBSCRIPTION slot leftover; expand lsn_v2",
            "sub_drop_tmp",
            "sub_row.lsn + lsn_v2; leftover sales_sub slot + sub_drop_tmp",
            "DROP TABLE IF EXISTS repl.sub_drop_tmp",
            "pg_lsn",
        ),
        P(
            "default-partition-constraint",
            "default-part-cstr",
            "part",
            "item_d",
            "k",
            "k_norm",
            "ALTER TABLE part.item_d ATTACH PARTITION part.item_d_default DEFAULT",
            "SELECT conname, contype, convalidated FROM pg_constraint WHERE conrelid='part.item_d_default'::regclass",
            "ERROR: 23P01 default partition constraint leftover overlap; leftover item_d_def_tmp; cannot rewrite k",
            "default partition constraint leftover overlap; expand k_norm",
            "item_d_def_tmp",
            "item_d.k + k_norm; leftover item_d_def_tmp",
            "DROP TABLE IF EXISTS part.item_d_def_tmp",
        ),
    ),
    (
        P(
            "operator-class-default-swap",
            "opclass-default",
            "idx",
            "opc_row",
            "k",
            "k_norm",
            "ALTER OPERATOR CLASS text_ops USING btree SET DEFAULT FOR TYPE text",
            "SELECT opcname, opcdefault, opcmethod::regproc FROM pg_opclass WHERE opcname='text_ops'",
            "ERROR: 42710 default opclass leftover; leftover opc_row_tmp; cannot rewrite k",
            "pg_opclass opcdefault leftover swap; expand k_norm",
            "opc_row_tmp",
            "opc_row.k + k_norm; leftover opc_row_tmp",
            "DROP TABLE IF EXISTS idx.opc_row_tmp",
        ),
        P(
            "domain-collation-mismatch",
            "domain-collation",
            "types",
            "dom_row",
            "val",
            "val_v2",
            "ALTER DOMAIN types.sku_dom SET DEFAULT NULL; ALTER DOMAIN types.sku_dom COLLATE \"und-x-icu\"",
            "SELECT typname, typcollation::regcollation FROM pg_type WHERE typname='sku_dom'",
            "ERROR: 42P22 collation leftover on domain sku_dom; leftover dom_row_tmp; cannot rewrite val",
            "domain collation leftover; expand val_v2",
            "dom_row_tmp",
            "dom_row.val + val_v2; leftover dom_row_tmp",
            "DROP TABLE IF EXISTS types.dom_row_tmp",
        ),
    ),
    (
        P(
            "policy-with-check-leftover",
            "policy-with-check",
            "tenant",
            "chk_row",
            "tid",
            "tid_uuid",
            "CREATE POLICY p_chk ON tenant.chk_row FOR INSERT WITH CHECK (tid IS NOT NULL)",
            "SELECT polname, polwithcheck IS NOT NULL AS has_check FROM pg_policy WHERE polrelid='tenant.chk_row'::regclass",
            "ERROR: 42501 WITH CHECK leftover p_chk; leftover chk_row_pol_tmp; cannot rewrite tid",
            "pg_policy polwithcheck leftover; expand tid_uuid",
            "chk_row_pol_tmp",
            "chk_row.tid + tid_uuid; leftover chk_row_pol_tmp",
            "DROP POLICY IF EXISTS p_chk ON tenant.chk_row; DROP TABLE IF EXISTS tenant.chk_row_pol_tmp",
            "uuid",
        ),
        P(
            "import-foreign-schema-limit",
            "import-fdw-limit",
            "fdw",
            "imp_row",
            "src",
            "src_v2",
            "IMPORT FOREIGN SCHEMA prod LIMIT TO (imp_row) FROM SERVER src INTO fdw",
            "SELECT ftrelid::regclass, ftoptions FROM pg_foreign_table WHERE ftrelid::regclass::text LIKE 'fdw.imp%'",
            "ERROR: HV000 IMPORT FOREIGN SCHEMA leftover limit list; leftover imp_row_tmp; cannot rewrite src",
            "IMPORT FOREIGN SCHEMA LIMIT leftover; expand src_v2",
            "imp_row_tmp",
            "imp_row.src + src_v2; leftover imp_row_tmp",
            "DROP FOREIGN TABLE IF EXISTS fdw.imp_row_tmp",
        ),
    ),
    (
        P(
            "file-fdw-program-options",
            "file-fdw-program",
            "fdw",
            "file_row",
            "path",
            "path_v2",
            "ALTER FOREIGN TABLE fdw.file_row OPTIONS (SET program '/usr/bin/fetch-sku')",
            "SELECT ftrelid::regclass, ftoptions FROM pg_foreign_table WHERE ftrelid='fdw.file_row'::regclass",
            "ERROR: HV000 program option leftover /usr/bin/fetch-sku; leftover file_row_fdw_tmp; cannot rewrite path",
            "file_fdw program option leftover; expand path_v2",
            "file_row_fdw_tmp",
            "file_row.path + path_v2; leftover file_row_fdw_tmp",
            "DROP FOREIGN TABLE IF EXISTS fdw.file_row_fdw_tmp",
        ),
        P(
            "pg-cron-unschedule-leftover",
            "cron-unschedule",
            "cron",
            "job_row",
            "cmd",
            "cmd_v2",
            "SELECT cron.unschedule(jobid) FROM cron.job WHERE jobname='sku-roll'",
            "SELECT jobid, jobname, command FROM cron.job WHERE jobname='sku-roll'",
            "ERROR: P0001 unschedule leftover jobid 42 still in cron.job_run_details; leftover job_row_cron_tmp; cannot rewrite cmd",
            "cron.unschedule leftover job_run_details; expand cmd_v2",
            "job_row_cron_tmp",
            "job_row.cmd + cmd_v2; leftover job_row_cron_tmp",
            "DROP TABLE IF EXISTS cron.job_row_cron_tmp",
        ),
    ),
    (
        P(
            "pg-ivm-incremental-view",
            "ivm-immv",
            "ivm",
            "mv_row",
            "k",
            "k_norm",
            "CREATE INCREMENTAL MATERIALIZED VIEW ivm.mv_row AS SELECT k FROM ivm.src",
            "SELECT relname, relkind, relispopulated FROM pg_class WHERE relname LIKE 'mv_row%'",
            "ERROR: 55000 IVM leftover IMMV not populated; leftover mv_row_ivm_tmp; cannot rewrite k",
            "pg_ivm IMMV leftover unpopulated; expand k_norm",
            "mv_row_ivm_tmp",
            "mv_row.k + k_norm; leftover mv_row_ivm_tmp",
            "DROP INCREMENTAL MATERIALIZED VIEW IF EXISTS ivm.mv_row_ivm_tmp",
        ),
        P(
            "pg-rewrite-ctid-chain",
            "ctid-chain-rewrite",
            "heap",
            "ctid_row",
            "payload",
            "payload_v2",
            "CLUSTER heap.ctid_row USING ctid_row_payload_idx",
            "SELECT ctid, xmax FROM heap.ctid_row WHERE xmax <> 0 LIMIT 5",
            "ERROR: XX001 ctid chain leftover after aborted heap rewrite; leftover ctid_row_rewrite_tmp; cannot rewrite payload",
            "ctid chain leftover after aborted rewrite; expand payload_v2",
            "ctid_row_rewrite_tmp",
            "ctid_row.payload + payload_v2; leftover ctid_row_rewrite_tmp",
            "DROP TABLE IF EXISTS heap.ctid_row_rewrite_tmp",
            "bytea",
        ),
    ),
    (
        P(
            "proc-parallel-unsafe-leftover",
            "proc-parallel-unsafe",
            "catalog",
            "fn_row",
            "sig",
            "sig_v2",
            "ALTER FUNCTION catalog.sku_norm(text) PARALLEL UNSAFE",
            "SELECT proname, proparallel FROM pg_proc WHERE oid='catalog.sku_norm(text)'::regprocedure",
            "ERROR: 0A000 PARALLEL UNSAFE leftover on sku_norm; leftover fn_row_tmp; cannot rewrite sig",
            "pg_proc proparallel unsafe leftover; expand sig_v2",
            "fn_row_tmp",
            "fn_row.sig + sig_v2; leftover fn_row_tmp",
            "DROP TABLE IF EXISTS catalog.fn_row_tmp",
        ),
        P(
            "hash-agg-spill-work-mem",
            "hashagg-spill",
            "agg",
            "hash_row",
            "k",
            "k_norm",
            "SET work_mem='64kB'; SELECT k, count(*) FROM agg.hash_row GROUP BY k",
            "SELECT relname, relpages FROM pg_class WHERE oid='agg.hash_row'::regclass",
            "ERROR: 53100 hash agg spill leftover temp files; leftover hash_row_spill_tmp; cannot rewrite k",
            "hash agg spill leftover temp; expand k_norm",
            "hash_row_spill_tmp",
            "hash_row.k + k_norm; leftover hash_row_spill_tmp",
            "DROP TABLE IF EXISTS agg.hash_row_spill_tmp",
        ),
    ),
    (
        P(
            "partial-index-pred-leftover",
            "partial-indpred",
            "shop",
            "filt_row",
            "sku",
            "sku_norm",
            "CREATE INDEX CONCURRENTLY filt_row_sku_live ON shop.filt_row (sku) WHERE live",
            "SELECT indexrelid::regclass, indisvalid, pg_get_expr(indpred, indrelid) FROM pg_index WHERE indrelid='shop.filt_row'::regclass",
            "ERROR: 57014 partial index leftover INVALID filt_row_sku_live; leftover filt_row_pred_tmp",
            "pg_index indpred leftover INVALID; expand sku_norm",
            "filt_row_pred_tmp",
            "INVALID filt_row_sku_live + filt_row_pred_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS shop.filt_row_sku_live; DROP TABLE IF EXISTS shop.filt_row_pred_tmp",
        ),
        P(
            "stats-ext-expression-leftover",
            "stats-ext-expr",
            "analytics",
            "expr_row",
            "sku",
            "sku_norm",
            "CREATE STATISTICS expr_row_lower ON (lower(sku)) FROM analytics.expr_row",
            "SELECT stxname, stxexprs FROM pg_statistic_ext WHERE stxrelid='analytics.expr_row'::regclass",
            "ERROR: 42P17 expression stats leftover expr_row_stx_tmp; cannot rewrite sku",
            "pg_statistic_ext expression leftover; expand sku_norm",
            "expr_row_stx_tmp",
            "expr_row.sku + sku_norm; leftover expr_row_stx_tmp",
            "DROP STATISTICS IF EXISTS analytics.expr_row_stx_tmp",
        ),
    ),
    (
        P(
            "index-only-visimap-leftover",
            "ios-visimap",
            "idx",
            "ios_row",
            "k",
            "k_norm",
            "CREATE INDEX CONCURRENTLY ios_row_k_uidx ON idx.ios_row (k)",
            "SELECT indexrelid::regclass, indisvalid FROM pg_index WHERE indrelid='idx.ios_row'::regclass",
            "ERROR: XX001 visimap leftover vs index-only scan; leftover ios_row_vm_tmp; INVALID ios_row_k_uidx",
            "index-only visimap leftover INVALID; expand k_norm",
            "ios_row_vm_tmp",
            "INVALID ios_row_k_uidx + ios_row_vm_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS idx.ios_row_k_uidx; DROP TABLE IF EXISTS idx.ios_row_vm_tmp",
        ),
        P(
            "bitmap-lossy-pages-leftover",
            "bitmap-lossy",
            "idx",
            "bmp_row",
            "k",
            "k_norm",
            "CREATE INDEX CONCURRENTLY bmp_row_k_idx ON idx.bmp_row (k)",
            "SELECT indexrelid::regclass, indisvalid FROM pg_index WHERE indrelid='idx.bmp_row'::regclass",
            "ERROR: 53200 lossy bitmap leftover pages; leftover bmp_row_lossy_tmp; cannot rewrite k",
            "lossy bitmap pages leftover; expand k_norm",
            "bmp_row_lossy_tmp",
            "bmp_row.k + k_norm; leftover bmp_row_lossy_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS idx.bmp_row_k_idx; DROP TABLE IF EXISTS idx.bmp_row_lossy_tmp",
        ),
    ),
    (
        P(
            "pg-walinspect-lsn-gap",
            "walinspect-lsn-gap",
            "wal",
            "inspect_row",
            "lsn",
            "lsn_v2",
            "SELECT * FROM pg_get_wal_records_info('0/1A00000', '0/1B00000')",
            "SELECT slot_name, confirmed_flush_lsn FROM pg_replication_slots WHERE slot_name='inspect_slot'",
            "ERROR: 58P01 WAL record gap leftover; leftover inspect_row_wal_tmp; cannot rewrite lsn",
            "pg_walinspect LSN gap leftover; expand lsn_v2",
            "inspect_row_wal_tmp",
            "inspect_row.lsn + lsn_v2; leftover inspect_row_wal_tmp",
            "DROP TABLE IF EXISTS wal.inspect_row_wal_tmp",
            "pg_lsn",
        ),
        P(
            "pg-rewind-timeline-id",
            "rewind-timeline",
            "ha",
            "rewind_row",
            "tli",
            "tli_v2",
            "pg_rewind --target-pgdata=data --source-server='host=primary'",
            "SELECT timeline_id FROM pg_control_checkpoint()",
            "ERROR: 58P01 rewind timeline leftover; leftover rewind_row_tli_tmp; cannot rewrite tli",
            "pg_rewind timeline leftover; expand tli_v2",
            "rewind_row_tli_tmp",
            "rewind_row.tli + tli_v2; leftover rewind_row_tli_tmp",
            "DROP TABLE IF EXISTS ha.rewind_row_tli_tmp",
            "int",
        ),
    ),
    (
        P(
            "attach-for-values-from-to",
            "attach-from-to",
            "part",
            "range_row",
            "k",
            "k_norm",
            "ALTER TABLE part.range_row ATTACH PARTITION part.range_row_a FOR VALUES FROM ('a') TO ('m')",
            "SELECT relname, relpartbound FROM pg_class WHERE relname LIKE 'range_row%'",
            "ERROR: 42P17 bound overlap leftover range_row_p_tmp; cannot rewrite k",
            "ATTACH PARTITION FROM/TO leftover overlap; expand k_norm",
            "range_row_p_tmp",
            "range_row.k + k_norm; leftover range_row_p_tmp",
            "DROP TABLE IF EXISTS part.range_row_p_tmp",
        ),
        P(
            "amproc-support-fn-mismatch",
            "amproc-support",
            "idx",
            "amproc_row",
            "k",
            "k_norm",
            "ALTER OPERATOR FAMILY text_ops USING btree ADD FUNCTION 3 (text, text) pg_catalog.text_starts_with(text, text)",
            "SELECT amprocnum, amproc::regproc FROM pg_amproc WHERE amprocfamily = (SELECT oid FROM pg_opfamily WHERE opfname='text_ops')",
            "ERROR: 42809 amproc support fn leftover; leftover amproc_row_tmp; cannot rewrite k",
            "pg_amproc support function leftover; expand k_norm",
            "amproc_row_tmp",
            "amproc_row.k + k_norm; leftover amproc_row_tmp",
            "DROP TABLE IF EXISTS idx.amproc_row_tmp",
        ),
    ),
    (
        P(
            "pg-cast-binary-coercion",
            "cast-binary",
            "types",
            "cast_row",
            "val",
            "val_v2",
            "CREATE CAST (types.sku_dom AS text) WITHOUT FUNCTION AS IMPLICIT",
            "SELECT castsource::regtype, casttarget::regtype, castcontext, castmethod FROM pg_cast WHERE castsource='types.sku_dom'::regtype",
            "ERROR: 42710 cast leftover WITHOUT FUNCTION; leftover cast_row_tmp; cannot rewrite val",
            "pg_cast binary coercion leftover; expand val_v2",
            "cast_row_tmp",
            "cast_row.val + val_v2; leftover cast_row_tmp",
            "DROP CAST IF EXISTS (types.sku_dom AS text); DROP TABLE IF EXISTS types.cast_row_tmp",
        ),
        P(
            "pg-collation-provider-builtin",
            "collation-builtin",
            "types",
            "col_row",
            "name",
            "name_v2",
            "CREATE COLLATION types.C_utf8 (provider = builtin, locale = 'C.UTF-8')",
            "SELECT collname, colprovider, colcollate FROM pg_collation WHERE collname='C_utf8'",
            "ERROR: 22023 builtin collation leftover C_utf8; leftover col_row_tmp; cannot rewrite name",
            "pg_collation provider=builtin leftover; expand name_v2",
            "col_row_tmp",
            "col_row.name + name_v2; leftover col_row_tmp",
            "DROP COLLATION IF EXISTS types.C_utf8; DROP TABLE IF EXISTS types.col_row_tmp",
        ),
    ),
    (
        P(
            "hypopg-hypothetical-index",
            "hypopg-index",
            "idx",
            "hypo_row",
            "k",
            "k_norm",
            "SELECT * FROM hypopg_create_index('CREATE INDEX ON idx.hypo_row (k)')",
            "SELECT indexrelid, indexname FROM hypopg()",
            "ERROR: P0001 hypothetical index leftover; leftover hypo_row_tmp; cannot rewrite k",
            "hypopg hypothetical index leftover; expand k_norm",
            "hypo_row_tmp",
            "hypo_row.k + k_norm; leftover hypo_row_tmp",
            "SELECT hypopg_reset(); DROP TABLE IF EXISTS idx.hypo_row_tmp",
        ),
        P(
            "pg-hint-plan-comment",
            "hint-plan-comment",
            "plan",
            "hint_row",
            "q",
            "q_v2",
            "/*+ IndexScan(hint_row hint_row_q_idx) */ SELECT * FROM plan.hint_row WHERE q = 'x'",
            "SELECT relname FROM pg_class WHERE oid='plan.hint_row'::regclass",
            "ERROR: P0001 hint leftover IndexScan vs seqscan; leftover hint_row_tmp; cannot rewrite q",
            "pg_hint_plan comment leftover; expand q_v2",
            "hint_row_tmp",
            "hint_row.q + q_v2; leftover hint_row_tmp",
            "DROP TABLE IF EXISTS plan.hint_row_tmp",
        ),
    ),
    (
        P(
            "parallel-vacuum-nworkers-skip",
            "parallel-vacuum",
            "vac",
            "par_row",
            "body",
            "body_v2",
            "VACUUM (PARALLEL 4, VERBOSE) vac.par_row",
            "SELECT relname, relpages FROM pg_class WHERE oid='vac.par_row'::regclass",
            "ERROR: 25001 parallel vacuum leftover nworkers; leftover par_row_vac_tmp; cannot rewrite body",
            "VACUUM PARALLEL leftover nworkers; expand body_v2",
            "par_row_vac_tmp",
            "par_row.body + body_v2; leftover par_row_vac_tmp",
            "DROP TABLE IF EXISTS vac.par_row_vac_tmp",
            "bytea",
        ),
        P(
            "trigger-deferrable-leftover",
            "trig-deferrable",
            "ops",
            "trig_row",
            "payload",
            "payload_v2",
            "CREATE CONSTRAINT TRIGGER trg_defer AFTER INSERT ON ops.trig_row DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ops.trg_fn()",
            "SELECT tgname, tgdeferrable, tginitdeferred FROM pg_trigger WHERE tgrelid='ops.trig_row'::regclass",
            "ERROR: 0A000 deferrable constraint trigger leftover trg_defer; leftover trig_row_tmp; cannot rewrite payload",
            "pg_trigger tgdeferrable leftover; expand payload_v2",
            "trig_row_tmp",
            "trig_row.payload + payload_v2; leftover trig_row_tmp",
            "DROP TRIGGER IF EXISTS trg_defer ON ops.trig_row; DROP TABLE IF EXISTS ops.trig_row_tmp",
            "bytea",
        ),
    ),
    (
        P(
            "pg-buffercache-pin-leftover",
            "buffercache-pin",
            "cache",
            "pin_row",
            "k",
            "k_v2",
            "SELECT * FROM pg_buffercache WHERE relfilenode = (SELECT relfilenode FROM pg_class WHERE oid='cache.pin_row'::regclass) AND pinning_backends > 0",
            "SELECT relname, relpages FROM pg_class WHERE oid='cache.pin_row'::regclass",
            "ERROR: 55P03 buffer pin leftover pinning_backends>0; leftover pin_row_buf_tmp; cannot rewrite k",
            "pg_buffercache pin leftover; expand k_v2",
            "pin_row_buf_tmp",
            "pin_row.k + k_v2; leftover pin_row_buf_tmp",
            "DROP TABLE IF EXISTS cache.pin_row_buf_tmp",
        ),
        P(
            "pg-freespace-map-mismatch",
            "fsm-mismatch",
            "heap",
            "fsm_row",
            "payload",
            "payload_v2",
            "SELECT * FROM pg_freespace('heap.fsm_row'::regclass) LIMIT 5",
            "SELECT relname, relpages FROM pg_class WHERE oid='heap.fsm_row'::regclass",
            "ERROR: XX001 FSM leftover vs heap; leftover fsm_row_tmp; cannot rewrite payload",
            "pg_freespace map leftover vs heap; expand payload_v2",
            "fsm_row_tmp",
            "fsm_row.payload + payload_v2; leftover fsm_row_tmp",
            "DROP TABLE IF EXISTS heap.fsm_row_tmp",
            "bytea",
        ),
    ),
    (
        P(
            "pg-rowlocks-xmax-leftover",
            "rowlocks-xmax",
            "heap",
            "lock_row",
            "payload",
            "payload_v2",
            "SELECT * FROM pgrowlocks('heap.lock_row'::regclass)",
            "SELECT relname FROM pg_class WHERE oid='heap.lock_row'::regclass",
            "ERROR: 55P03 xmax MultiXact leftover; leftover lock_row_xmax_tmp; cannot rewrite payload",
            "pgrowlocks xmax MultiXact leftover; expand payload_v2",
            "lock_row_xmax_tmp",
            "lock_row.payload + payload_v2; leftover lock_row_xmax_tmp",
            "DROP TABLE IF EXISTS heap.lock_row_xmax_tmp",
            "bytea",
        ),
        P(
            "pg-surgery-heap-rewrite",
            "surgery-heap",
            "heap",
            "surg_row",
            "payload",
            "payload_v2",
            "SELECT heap_force_kill('heap.surg_row'::regclass, ARRAY['(0,1)']::tid[])",
            "SELECT relname, relpages FROM pg_class WHERE oid='heap.surg_row'::regclass",
            "ERROR: XX001 surgery leftover lp; leftover surg_row_tmp; cannot rewrite payload",
            "pg_surgery heap_force_kill leftover lp; expand payload_v2",
            "surg_row_tmp",
            "surg_row.payload + payload_v2; leftover surg_row_tmp",
            "DROP TABLE IF EXISTS heap.surg_row_tmp",
            "bytea",
        ),
    ),
    (
        P(
            "copy-on-error-ignore-leftover",
            "copy-on-error",
            "ingest",
            "copy_row",
            "raw",
            "raw_v2",
            "COPY ingest.copy_row(raw) FROM STDIN WITH (FORMAT csv, ON_ERROR ignore)",
            "SELECT relname, reltuples FROM pg_class WHERE oid='ingest.copy_row'::regclass",
            "ERROR: 22P04 COPY ON_ERROR leftover skipped rows; leftover copy_row_tmp; cannot rewrite raw",
            "COPY ON_ERROR ignore leftover skipped; expand raw_v2",
            "copy_row_tmp",
            "copy_row.raw + raw_v2; leftover copy_row_tmp",
            "DROP TABLE IF EXISTS ingest.copy_row_tmp",
        ),
        P(
            "returning-old-new-rewrite",
            "returning-old-new",
            "mut",
            "ret_row",
            "val",
            "val_v2",
            "UPDATE mut.ret_row SET val = val WHERE true RETURNING old.val, new.val",
            "SELECT relname FROM pg_class WHERE oid='mut.ret_row'::regclass",
            "ERROR: 0A000 RETURNING old leftover rewrite tmp; leftover ret_row_tmp; cannot rewrite val",
            "RETURNING old/new leftover rewrite; expand val_v2",
            "ret_row_tmp",
            "ret_row.val + val_v2; leftover ret_row_tmp",
            "DROP TABLE IF EXISTS mut.ret_row_tmp",
        ),
    ),
    (
        P(
            "jsonb-subscript-unique",
            "jsonb-subscript",
            "doc",
            "jsub_row",
            "j",
            "j_v2",
            "CREATE UNIQUE INDEX CONCURRENTLY jsub_row_sku ON doc.jsub_row ((j['sku']))",
            "SELECT indexrelid::regclass, indisunique, indisvalid FROM pg_index WHERE indrelid='doc.jsub_row'::regclass",
            "ERROR: 23505 jsonb subscript unique leftover INVALID jsub_row_sku; leftover jsub_row_tmp",
            "jsonb subscript unique leftover INVALID; expand j_v2",
            "jsub_row_tmp",
            "INVALID jsub_row_sku + jsub_row_tmp",
            "DROP INDEX CONCURRENTLY IF EXISTS doc.jsub_row_sku; DROP TABLE IF EXISTS doc.jsub_row_tmp",
            "jsonb",
        ),
        P(
            "convert-using-leftover",
            "convert-using",
            "types",
            "conv_row",
            "val",
            "val_v2",
            "ALTER TABLE types.conv_row ALTER COLUMN val TYPE bigint USING val::bigint",
            "SELECT attname, atttypid::regtype FROM pg_attribute WHERE attrelid='types.conv_row'::regclass AND attname='val'",
            "ERROR: 42804 USING leftover type mismatch; leftover conv_row_tmp; cannot rewrite val in place",
            "ALTER TYPE USING leftover; expand val_v2",
            "conv_row_tmp",
            "conv_row.val + val_v2; leftover conv_row_tmp",
            "DROP TABLE IF EXISTS types.conv_row_tmp",
        ),
    ),
    (
        P(
            "sequence-set-logged-leftover",
            "seq-set-logged",
            "catalog",
            "seq_row",
            "n",
            "n_v2",
            "ALTER SEQUENCE catalog.seq_row_n_seq SET LOGGED",
            "SELECT relname, relpersistence FROM pg_class WHERE relname='seq_row_n_seq'",
            "ERROR: 0A000 sequence SET LOGGED leftover vs unlogged table; leftover seq_row_tmp; cannot rewrite n",
            "sequence SET LOGGED leftover; expand n_v2",
            "seq_row_tmp",
            "seq_row.n + n_v2; leftover seq_row_tmp",
            "DROP TABLE IF EXISTS catalog.seq_row_tmp",
            "bigint",
        ),
        P(
            "temp-toast-leftover",
            "temp-toast",
            "tmp",
            "toast_row",
            "body",
            "body_v2",
            "CREATE TEMP TABLE toast_row (body text); INSERT INTO toast_row SELECT repeat('x', 8000)",
            "SELECT relname, reltoastrelid FROM pg_class WHERE relname='toast_row'",
            "ERROR: 3F000 temp toast leftover after session; leftover toast_row_tmp; cannot rewrite body",
            "temp toast leftover; expand body_v2",
            "toast_row_tmp",
            "toast_row.body + body_v2; leftover toast_row_tmp",
            "DROP TABLE IF EXISTS tmp.toast_row_tmp",
            "text",
        ),
    ),
    (
        P(
            "subscription-origin-none",
            "sub-origin-none",
            "repl",
            "orig_row",
            "lsn",
            "lsn_v2",
            "ALTER SUBSCRIPTION sales_sub SET (origin = none)",
            "SELECT subname, subenabled FROM pg_subscription WHERE subname='sales_sub'",
            "ERROR: 55000 origin=none leftover; leftover orig_row_origin_tmp; cannot rewrite lsn",
            "subscription origin=none leftover; expand lsn_v2",
            "orig_row_origin_tmp",
            "orig_row.lsn + lsn_v2; leftover orig_row_origin_tmp",
            "DROP TABLE IF EXISTS repl.orig_row_origin_tmp",
            "pg_lsn",
        ),
        P(
            "repl-slot-invalidated",
            "slot-invalidated",
            "repl",
            "slot_row",
            "lsn",
            "lsn_v2",
            "SELECT pg_drop_replication_slot('sales_slot')",
            "SELECT slot_name, wal_status, conflict_reason FROM pg_replication_slots WHERE slot_name='sales_slot'",
            "ERROR: 55000 slot invalidated leftover wal_status=lost; leftover slot_row_tmp; cannot rewrite lsn",
            "replication slot invalidated leftover; expand lsn_v2",
            "slot_row_tmp",
            "slot_row.lsn + lsn_v2; leftover slot_row_tmp",
            "DROP TABLE IF EXISTS repl.slot_row_tmp",
            "pg_lsn",
        ),
    ),
    (
        P(
            "constraint-conislocal-leftover",
            "conislocal",
            "inherit",
            "con_row",
            "k",
            "k_norm",
            "ALTER TABLE inherit.con_row ADD CONSTRAINT con_row_k_chk CHECK (k <> '') NO INHERIT",
            "SELECT conname, conislocal, coninhcount, connoinherit FROM pg_constraint WHERE conrelid='inherit.con_row'::regclass",
            "ERROR: 42P16 conislocal leftover on child; leftover con_row_tmp; cannot rewrite k",
            "pg_constraint conislocal leftover; expand k_norm",
            "con_row_tmp",
            "con_row.k + k_norm; leftover con_row_tmp",
            "ALTER TABLE inherit.con_row DROP CONSTRAINT IF EXISTS con_row_k_chk; DROP TABLE IF EXISTS inherit.con_row_tmp",
        ),
        P(
            "rule-instead-leftover",
            "rule-instead",
            "rewrite",
            "rule_row",
            "payload",
            "payload_v2",
            "CREATE RULE rule_row_ins AS ON INSERT TO rewrite.rule_row DO INSTEAD INSERT INTO rewrite.rule_row_audit VALUES (NEW.*)",
            "SELECT rulename, ev_type, is_instead FROM pg_rewrite WHERE ev_class='rewrite.rule_row'::regclass",
            "ERROR: 42P16 INSTEAD rule leftover rule_row_ins; leftover rule_row_tmp; cannot rewrite payload",
            "pg_rewrite INSTEAD rule leftover; expand payload_v2",
            "rule_row_tmp",
            "rule_row.payload + payload_v2; leftover rule_row_tmp",
            "DROP RULE IF EXISTS rule_row_ins ON rewrite.rule_row; DROP TABLE IF EXISTS rewrite.rule_row_tmp",
            "bytea",
        ),
    ),
    (
        P(
            "opfamily-sortsupport-leftover",
            "opfamily-sortsupport",
            "idx",
            "sortop_row",
            "k",
            "k_norm",
            "ALTER OPERATOR FAMILY text_ops USING btree ADD FUNCTION 2 (text) pg_catalog.bttextsortsupport(internal)",
            "SELECT amprocnum, amproc::regproc FROM pg_amproc WHERE amprocnum=2 AND amprocfamily = (SELECT oid FROM pg_opfamily WHERE opfname='text_ops')",
            "ERROR: 42809 sortsupport leftover; leftover sortop_row_tmp; cannot rewrite k",
            "pg_amproc sortsupport leftover; expand k_norm",
            "sortop_row_tmp",
            "sortop_row.k + k_norm; leftover sortop_row_tmp",
            "DROP TABLE IF EXISTS idx.sortop_row_tmp",
        ),
        P(
            "am-handler-mismatch",
            "am-handler",
            "idx",
            "amh_row",
            "k",
            "k_norm",
            "CREATE ACCESS METHOD dummy TYPE INDEX HANDLER dummy_handler",
            "SELECT amname, amhandler::regproc FROM pg_am WHERE amname='dummy'",
            "ERROR: 42809 amhandler leftover dummy; leftover amh_row_tmp; cannot rewrite k",
            "pg_am amhandler leftover; expand k_norm",
            "amh_row_tmp",
            "amh_row.k + k_norm; leftover amh_row_tmp",
            "DROP ACCESS METHOD IF EXISTS dummy; DROP TABLE IF EXISTS idx.amh_row_tmp",
        ),
    ),
    (
        P(
            "event-trigger-sql-drop",
            "evt-sql-drop",
            "ddl",
            "drop_row",
            "name",
            "name_v2",
            "CREATE EVENT TRIGGER trg_sql_drop ON sql_drop EXECUTE FUNCTION ddl.audit_drop()",
            "SELECT evtname, evtevent, evtenabled FROM pg_event_trigger WHERE evtname='trg_sql_drop'",
            "ERROR: 0A000 sql_drop event trigger leftover trg_sql_drop; leftover drop_row_evt_tmp; cannot rewrite name",
            "pg_event_trigger sql_drop leftover; expand name_v2",
            "drop_row_evt_tmp",
            "drop_row.name + name_v2; leftover drop_row_evt_tmp",
            "DROP EVENT TRIGGER IF EXISTS trg_sql_drop; DROP TABLE IF EXISTS ddl.drop_row_evt_tmp",
        ),
        P(
            "ts-config-map-leftover",
            "ts-config-map",
            "search",
            "ts_row",
            "q",
            "q_v2",
            "ALTER TEXT SEARCH CONFIGURATION search.sku_cfg ALTER MAPPING FOR asciiword WITH english_stem",
            "SELECT mapcfg::regconfig, maptokentype, mapdict::regdictionary FROM pg_ts_config_map WHERE mapcfg='search.sku_cfg'::regconfig",
            "ERROR: 42704 ts config map leftover english_stem; leftover ts_row_tmp; cannot rewrite q",
            "pg_ts_config_map leftover; expand q_v2",
            "ts_row_tmp",
            "ts_row.q + q_v2; leftover ts_row_tmp",
            "DROP TABLE IF EXISTS search.ts_row_tmp",
        ),
    ),
    (
        P(
            "largeobject-metadata-leftover",
            "lo-metadata",
            "blob",
            "lo_row",
            "oid",
            "oid_v2",
            "SELECT lo_unlink(oid) FROM pg_largeobject_metadata",
            "SELECT oid, lomowner::regrole FROM pg_largeobject_metadata LIMIT 5",
            "ERROR: 42704 large object leftover metadata; leftover lo_row_tmp; cannot rewrite oid",
            "pg_largeobject_metadata leftover; expand oid_v2",
            "lo_row_tmp",
            "lo_row.oid + oid_v2; leftover lo_row_tmp",
            "DROP TABLE IF EXISTS blob.lo_row_tmp",
            "oid",
        ),
        P(
            "foreign-server-validator",
            "fdw-validator",
            "fdw",
            "srv_row",
            "opt",
            "opt_v2",
            "ALTER SERVER src OPTIONS (SET fetch_size '5000')",
            "SELECT srvname, srvoptions FROM pg_foreign_server WHERE srvname='src'",
            "ERROR: HV000 fdw validator leftover fetch_size; leftover srv_row_tmp; cannot rewrite opt",
            "pg_foreign_server validator leftover; expand opt_v2",
            "srv_row_tmp",
            "srv_row.opt + opt_v2; leftover srv_row_tmp",
            "DROP TABLE IF EXISTS fdw.srv_row_tmp",
        ),
    ),
    (
        P(
            "pg-stat-io-reset-leftover",
            "stat-io-reset",
            "obs",
            "io_row",
            "q",
            "q_v2",
            "SELECT pg_stat_reset_shared('io')",
            "SELECT backend_type, object, reads FROM pg_stat_io WHERE reads > 0 LIMIT 5",
            "ERROR: 55000 pg_stat_io reset leftover counters; leftover io_row_tmp; cannot rewrite q",
            "pg_stat_io reset leftover; expand q_v2",
            "io_row_tmp",
            "io_row.q + q_v2; leftover io_row_tmp",
            "DROP TABLE IF EXISTS obs.io_row_tmp",
        ),
        P(
            "pg-wait-events-lwlock",
            "wait-lwlock",
            "obs",
            "wait_row",
            "q",
            "q_v2",
            "SELECT wait_event_type, wait_event FROM pg_stat_activity WHERE wait_event_type='LWLock'",
            "SELECT relname FROM pg_class WHERE oid='obs.wait_row'::regclass",
            "ERROR: 55P03 LWLock leftover on wait_row; leftover wait_row_tmp; cannot rewrite q",
            "LWLock wait leftover; expand q_v2",
            "wait_row_tmp",
            "wait_row.q + q_v2; leftover wait_row_tmp",
            "DROP TABLE IF EXISTS obs.wait_row_tmp",
        ),
    ),
]


def _assert_catalog() -> None:
    slugs = []
    plants = []
    quals = []
    for a, b in PAIRS:
        for p in (a, b):
            blob = " ".join(
                [
                    p["slug"],
                    p["plant"],
                    p["seed"],
                    p["fail"],
                    p["catalog"],
                ]
            ).lower()
            for needle in BANNED_NEEDLES:
                if needle in blob:
                    raise SystemExit(f"banned needle {needle!r} in {p['slug']}")
            slugs.append(p["slug"])
            plants.append(p["plant"])
            quals.append(p["qual"])
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs")
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plant names")
    if len(quals) != len(set(quals)):
        raise SystemExit("duplicate schema.table")


_assert_catalog()


def pair_for(round_number: int) -> tuple[dict, dict]:
    idx = round_number - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {round_number} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}")
    return PAIRS[idx]


def ver_for(round_number: int) -> int:
    return round_number + 1168  # r843 used 2011


def residual(p: dict) -> str:
    return f"{p['table']}.{p['old']} + {p['new']}; leftover {p['leftover']}"


def episode(round_number: int, p: dict) -> dict:
    ver = ver_for(round_number)
    slug = p["slug"]
    mig = f"migrations/{ver}_{slug.replace('-', '_')}.sql"
    down = f"migrations/{ver}_{slug.replace('-', '_')}.down.sql"
    test = f"tests/test_{slug.replace('-', '_')}.py"
    runbook = f"docs/{slug}.md"
    backfill = f"jobs/backfill_{slug.replace('-', '_')}.py"
    checksum = f"jobs/checksum_{slug.replace('-', '_')}.py"
    res = residual(p)
    fail_short = clip(p["fail"], 90)
    steps = [
        bash(
            1,
            f"Plan: inspect pg_catalog for {p['qual']} before apply {ver} ({slug}).",
            f"psql -X -c \"{p['inspect']}\"",
            f"{p['qual']} present\npending: {p['fail']}\nshape now: {res}\ncatalog: {p['catalog']}\nlocks/mutations: 1 active; dual leftover objects",
        ),
        bash(
            2,
            f"Plan: apply naive catalog change on {p['qual']}.{p['old']}.",
            f"psql -X -c \"{p['seed']}\"",
            p["fail"],
        ),
        bash(
            3,
            f"Observation: first apply failed ({fail_short}). Plan change: abort in-place rewrite; expand {p['new']} + backfill; leave {p['old']} residual.",
            f"psql -X -c \"{p['abort']}\"",
            "leftovers dropped or cancelled; naive rewrite aborted; dual objects still planned",
        ),
        write_step(
            4,
            f"Plan: write expand-only migration {ver} adding {p['new']} (keep {p['old']}).",
            mig,
            (
                f"-- {ver} expand {p['qual']} {p['new']}\n"
                f"ALTER TABLE {p['qual']} ADD COLUMN {p['new']} {p['coltype']};\n"
                f"-- never drop {p['old']}; keep dual residual\n"
                f"-- {p['catalog']}\n"
            ),
            "expand-only written",
        ),
        bash(
            5,
            f"Plan: apply expand {ver} with short lock timeout.",
            f"psql -X -c \"SET lock_timeout='8s'; ALTER TABLE {p['qual']} ADD COLUMN IF NOT EXISTS {p['new']} {p['coltype']}\"",
            f"ERROR: 55P03 lock_not_available ADD {p['new']} on {p['qual']}",
        ),
        bash(
            6,
            "Observation: lock timeout on expand. Plan: retry SET lock_timeout=8s off-peak; ACCESS EXCLUSIVE avoided.",
            f"psql -X -c \"SET lock_timeout='8s'; ALTER TABLE {p['qual']} ADD COLUMN IF NOT EXISTS {p['new']} {p['coltype']}\"",
            f"ok retry expand {p['new']}",
        ),
        bash(
            7,
            f"Plan: batched backfill {p['new']} from {p['old']} without validating leftover constraints.",
            f"python {backfill} --batch 8000 --from {p['old']} --to {p['new']}",
            f"copied batch ok; remaining 0 on {p['qual']}; dual residual {res}",
        ),
        bash(
            8,
            f"Plan: tests {test} (catalog residual must remain).",
            f"pytest -q {test}",
            "3 passed",
        ),
        write_step(
            9,
            f"Plan: down {ver} must refuse lossy drop of {p['new']}.",
            down,
            f"SELECT raise_error('lossy {p['new']} drop; dual residual {p['table']} must remain');\n",
            "down v2 guard",
        ),
        bash(
            10,
            f"Observation: dual residual {res}.",
            f"psql -X -c \"{p['inspect']}\"",
            res,
        ),
        write_step(
            11,
            f"Plan: runbook never in-place rewrite {p['old']} via naive catalog DDL.",
            runbook,
            (
                f"Never psql -X -c \"{p['seed']}\". Expand {p['new']}, backfill, dual-read. "
                f"Residual: {res}. Restore leftovers before retry. {p['catalog']}"
            ),
            "runbook",
        ),
        bash(
            12,
            f"Plan: extra tests {test} + tests/test_schema.py.",
            f"pytest -q {test} tests/test_schema.py",
            "4 passed",
        ),
        bash(
            13,
            "Tool call: leftover catalog objects after abort.",
            f"rg '{p['tmp']}|{p['new']}|{p['old']}' || echo none-in-rewrite-path",
            "none in rewrite path; dual objects remain as residual",
        ),
        bash(
            14,
            f"Plan: checksum {p['old']} vs {p['new']}; confirm leftover catalog objects still dual.",
            f"python {checksum}",
            f"mismatch 0 on backfilled rows; dual residual {res}",
        ),
        bash(
            15,
            f"Plan: confirm no active locks/mutations on {p['table']}.",
            f"psql -X -c \"{p['inspect']}\"",
            "0 blockers; dual objects still present",
        ),
        bash(
            16,
            f"Plan: stamp schema version {ver}.",
            f"echo {ver}",
            str(ver),
        ),
    ]
    if len(steps) != 16:
        raise SystemExit("need 16 steps")
    goal = (
        f"{p['plant']}: psql {p['seed']} on {p['qual']}.{p['old']} failed ({clip(p['fail'], 140)}). "
        f"Expand {p['new']}, backfill, residual {res}."
    )
    return {
        "id": f"dbm-r{round_number}-{slug}",
        "goal": goal,
        "plan": (
            f"Abort in-place rewrite; expand-contract via ALTER TABLE {p['qual']} "
            f"ADD COLUMN {p['new']} {p['coltype']}; keep {p['old']}; dual leftover objects."
        ),
        "steps": steps,
        "outcome": (
            f"Naive catalog apply failed. Plan change: expand {p['new']} + backfill. "
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
            "factory": FACTORY,
            "round": round_number,
            "generator": GEN,
            "kind": "episode",
            "plant": p["plant"],
            "sim_or_real": "designed",
            "surface": SURFACE,
        },
    }


def notes_text(round_number: int, a: dict, b: dict) -> str:
    novelty = max(70, 80 - (round_number - CATALOG_FIRST) // 2)
    ver = ver_for(round_number)
    lines = [
        f"# NOTES-r{round_number} {FACTORY}",
        "",
        f"Novel coverage: {novelty}%",
        "",
        "Two designed episodes (quota 2). Unique vs r1-r105 first-cycle, r106-r239 engines, "
        "r240-r761 recycle mill, r762-r793 warehouse mill, and r794-r817 ORM-CLI grid. "
        f"Surfaces: pg-catalog {a['slug']}; pg-catalog {b['slug']}. "
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
        "Avoid the two slugs in this round next. Do not clone r762-r793 or r794-r817. Do not recycle.",
        f"schema version {ver}.",
        "",
    ]
    return "\n".join(lines)


FORBIDDEN_KEY_RE = re.compile(r"(thought|chain_of_thought|scratch|inner_monologue|spike_events)")


def _walk_forbidden(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if FORBIDDEN_KEY_RE.fullmatch(k):
                raise SystemExit(f"forbidden key {k} at {path}")
            _walk_forbidden(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _walk_forbidden(item, f"{path}[{i}]")


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
    batch = staging / f"batch-r{round_number:02d}.jsonl"
    notes = staging / f"NOTES-r{round_number:02d}.md"
    batch.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs))
    notes.write_text(notes_text(round_number, a, b))


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
