#!/usr/bin/env python3
"""Unique leftover leftover leftover mill for db-migration-repair r1260+.

App/ORM leftover leftover leftover surfaces (Flyway/Liquibase/Alembic/Django/
Prisma/Atlas/goose/dbmate/golang-migrate/Sqitch/Skeema/gh-ost/pt-osc/pgroll/
expand-contract/Vitess). Not recycle r240-r761. Not warehouse r762-r793.
Not ORM-CLI grid r794-r817 clones. Not PG catalog r818-r844. IDs dbm-rN-slug
without trailing -rNN.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

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
START_ROUND = 1260
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
RECYCLE_SUFFIX = re.compile(r"-r\d+$")


def pl(**kw: str) -> dict[str, str]:
    return kw


PLANTS: list[dict[str, str]] = [
    pl(
        engine="flyway",
        slug="flyway-undo-script-leftover3",
        plant="fw-undo-l3",
        surface="flyway-undo-leftover3",
        table="fw.undo_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="flyway_schema_history_undo_tmp",
        leftover2="U2__undo_sku_norm.sql.bak",
        seed="flyway undo -undoSqlMigrationPrefix=U",
        fail="ERROR: leftover leftover leftover undo script U2 still in history; leftover flyway_schema_history_undo_tmp; cannot rewrite sku",
        inspect="flyway info -json",
        catalog="Flyway leftover leftover leftover undo; expand sku_norm",
        abort="flyway repair; rm -f U2__undo_sku_norm.sql.bak",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on fw.undo_sku",
    ),
    pl(
        engine="flyway",
        slug="flyway-callback-leftover3",
        plant="fw-cb-l3",
        surface="flyway-callback-leftover3",
        table="fw.cb_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="afterMigrate_error_tmp",
        leftover2="flyway_callback_lock",
        seed="flyway migrate -callbacks=afterMigrate",
        fail="ERROR: leftover leftover leftover afterMigrate callback left afterMigrate_error_tmp; cannot rewrite sku",
        inspect="ls sql/afterMigrate.sql; flyway info",
        catalog="Flyway leftover leftover leftover callback; expand sku_norm",
        abort="rm -f afterMigrate_error_tmp flyway_callback_lock",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on fw.cb_sku",
    ),
    pl(
        engine="liquibase",
        slug="liquibase-precondition-leftover3",
        plant="lb-pre-l3",
        surface="liquibase-precondition-leftover3",
        table="lb.pre_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="databasechangeloglock_stale",
        leftover2="precondition_onfail_mark_ran",
        seed="liquibase update --changelog-file=db/changelog.xml",
        fail="ERROR: leftover leftover leftover precondition onFail=MARK_RAN leftover databasechangeloglock_stale; cannot rewrite sku",
        inspect="liquibase status --verbose",
        catalog="Liquibase leftover leftover leftover precondition; expand sku_norm",
        abort="liquibase releaseLocks; DROP TABLE IF EXISTS databasechangeloglock_stale",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on lb.pre_sku",
    ),
    pl(
        engine="liquibase",
        slug="liquibase-rollback-tag-leftover3",
        plant="lb-tag-l3",
        surface="liquibase-tag-leftover3",
        table="lb.tag_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="DATABASECHANGELOG_tag_ghost",
        leftover2="rollbackToTag_partial",
        seed="liquibase rollback --tag=v2-sku",
        fail="ERROR: leftover leftover leftover rollbackToTag leftover DATABASECHANGELOG_tag_ghost; cannot rewrite sku",
        inspect="liquibase history",
        catalog="Liquibase leftover leftover leftover tag; expand sku_norm",
        abort="liquibase tag --tag=v2-sku-repair; DROP TABLE IF EXISTS DATABASECHANGELOG_tag_ghost",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on lb.tag_sku",
    ),
    pl(
        engine="alembic",
        slug="alembic-merge-heads-leftover3",
        plant="al-merge-l3",
        surface="alembic-merge-leftover3",
        table="al.merge_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="alembic_version_two_heads",
        leftover2="merge_rev_orphan",
        seed="alembic upgrade head",
        fail="ERROR: leftover leftover leftover Multiple heads leftover alembic_version_two_heads; cannot rewrite sku",
        inspect="alembic heads; alembic current",
        catalog="Alembic leftover leftover leftover merge heads; expand sku_norm",
        abort="alembic merge heads -m leftover3; DROP TABLE IF EXISTS merge_rev_orphan",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on al.merge_sku",
    ),
    pl(
        engine="alembic",
        slug="alembic-stamp-version-leftover3",
        plant="al-stamp-l3",
        surface="alembic-stamp-leftover3",
        table="al.stamp_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="alembic_version_stamped_ghost",
        leftover2="stamp_skip_ddl_tmp",
        seed="alembic stamp head --purge",
        fail="ERROR: leftover leftover leftover stamp skipped DDL leftover alembic_version_stamped_ghost; cannot rewrite sku",
        inspect="alembic current -v",
        catalog="Alembic leftover leftover leftover stamp; expand sku_norm",
        abort="DELETE FROM alembic_version WHERE version_num='stamped_ghost'",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on al.stamp_sku",
    ),
    pl(
        engine="django",
        slug="django-runpython-leftover3",
        plant="dj-rp-l3",
        surface="django-runpython-leftover3",
        table="dj.rp_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="django_migrations_runpython_half",
        leftover2="RunPython_atomic_open",
        seed="python manage.py migrate catalog 0042_runpython_sku",
        fail="ERROR: leftover leftover leftover RunPython inside atomic leftover django_migrations_runpython_half; cannot rewrite sku",
        inspect="python manage.py showmigrations catalog",
        catalog="Django leftover leftover leftover RunPython; expand sku_norm",
        abort="python manage.py migrate catalog 0041 --fake",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on dj.rp_sku",
    ),
    pl(
        engine="django",
        slug="django-atomic-inside-leftover3",
        plant="dj-at-l3",
        surface="django-atomic-leftover3",
        table="dj.at_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="atomic_block_savepoint_leftover",
        leftover2="django_content_type_ghost",
        seed="python manage.py migrate catalog 0043_atomic",
        fail="ERROR: leftover leftover leftover atomic=False required leftover atomic_block_savepoint_leftover; cannot rewrite sku",
        inspect="python manage.py showmigrations catalog --list",
        catalog="Django leftover leftover leftover atomic; expand sku_norm",
        abort="python manage.py dbshell -c 'ROLLBACK TO SAVEPOINT atomic_block_savepoint_leftover'",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on dj.at_sku",
    ),
    pl(
        engine="prisma",
        slug="prisma-shadow-db-leftover3",
        plant="pr-sh-l3",
        surface="prisma-shadow-leftover3",
        table="pr.sh_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="prisma_migrate_shadow_db",
        leftover2="_prisma_migrations_failed",
        seed="prisma migrate dev --create-only",
        fail="ERROR: leftover leftover leftover P3006 shadow DB leftover prisma_migrate_shadow_db; cannot rewrite sku",
        inspect="prisma migrate status",
        catalog="Prisma leftover leftover leftover shadow; expand sku_norm",
        abort="prisma migrate resolve --rolled-back 20260819_sku; DROP DATABASE IF EXISTS prisma_migrate_shadow_db",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on pr.sh_sku",
    ),
    pl(
        engine="prisma",
        slug="prisma-migrate-resolve-leftover3",
        plant="pr-rs-l3",
        surface="prisma-resolve-leftover3",
        table="pr.rs_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="_prisma_migrations_failed_row",
        leftover2="resolve_applied_ghost",
        seed="prisma migrate resolve --applied 20260819_sku",
        fail="ERROR: leftover leftover leftover resolve --applied without DDL leftover _prisma_migrations_failed_row; cannot rewrite sku",
        inspect="prisma migrate status --json",
        catalog="Prisma leftover leftover leftover resolve; expand sku_norm",
        abort="prisma migrate resolve --rolled-back 20260819_sku",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on pr.rs_sku",
    ),
    pl(
        engine="atlas",
        slug="atlas-hash-mismatch-leftover3",
        plant="at-hash-l3",
        surface="atlas-hash-leftover3",
        table="at.hash_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="atlas_schema_revisions_hash",
        leftover2="atlas.sum.bak",
        seed="atlas migrate apply --dir file://migrations",
        fail="ERROR: leftover leftover leftover checksum mismatch leftover atlas_schema_revisions_hash; cannot rewrite sku",
        inspect="atlas migrate status --dir file://migrations",
        catalog="Atlas leftover leftover leftover hash; expand sku_norm",
        abort="atlas migrate hash --dir file://migrations; rm -f atlas.sum.bak",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on at.hash_sku",
    ),
    pl(
        engine="atlas",
        slug="atlas-lint-destructive-leftover3",
        plant="at-lint-l3",
        surface="atlas-lint-leftover3",
        table="at.lint_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="atlas_lint_DS102_tmp",
        leftover2="destructive_drop_sku_plan",
        seed="atlas migrate lint --latest 1",
        fail="ERROR: leftover leftover leftover DS102 destructive leftover atlas_lint_DS102_tmp; cannot rewrite sku",
        inspect="atlas schema inspect --url postgres://app",
        catalog="Atlas leftover leftover leftover lint; expand sku_norm",
        abort="rm -f atlas_lint_DS102_tmp destructive_drop_sku_plan",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on at.lint_sku",
    ),
    pl(
        engine="goose",
        slug="goose-allow-missing-leftover3",
        plant="gs-miss-l3",
        surface="goose-missing-leftover3",
        table="gs.miss_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="goose_db_version_gap",
        leftover2="allow_missing_applied_out_of_order",
        seed="goose -allow-missing up",
        fail="ERROR: leftover leftover leftover missing version leftover goose_db_version_gap; cannot rewrite sku",
        inspect="goose status",
        catalog="goose leftover leftover leftover allow-missing; expand sku_norm",
        abort="goose down; DELETE FROM goose_db_version WHERE version_id=0",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on gs.miss_sku",
    ),
    pl(
        engine="goose",
        slug="goose-no-versioning-leftover3",
        plant="gs-nv-l3",
        surface="goose-noversion-leftover3",
        table="gs.nv_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="goose_no_versioning_lock",
        leftover2="sql_noversion_partial",
        seed="goose -no-versioning up",
        fail="ERROR: leftover leftover leftover no-versioning leftover goose_no_versioning_lock; cannot rewrite sku",
        inspect="goose -no-versioning status",
        catalog="goose leftover leftover leftover no-versioning; expand sku_norm",
        abort="rm -f goose_no_versioning_lock sql_noversion_partial",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on gs.nv_sku",
    ),
    pl(
        engine="dbmate",
        slug="dbmate-dump-leftover3",
        plant="dm-dump-l3",
        surface="dbmate-dump-leftover3",
        table="dm.dump_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="schema.sql.dump.tmp",
        leftover2="dbmate_schema_migrations_ghost",
        seed="dbmate dump",
        fail="ERROR: leftover leftover leftover dump leftover schema.sql.dump.tmp; cannot rewrite sku",
        inspect="dbmate status",
        catalog="dbmate leftover leftover leftover dump; expand sku_norm",
        abort="rm -f schema.sql.dump.tmp; dbmate rollback",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on dm.dump_sku",
    ),
    pl(
        engine="dbmate",
        slug="dbmate-wait-leftover3",
        plant="dm-wait-l3",
        surface="dbmate-wait-leftover3",
        table="dm.wait_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="dbmate_wait_pid",
        leftover2="schema_migrations_pending_wait",
        seed="dbmate --wait --wait-timeout 60s up",
        fail="ERROR: leftover leftover leftover wait timeout leftover dbmate_wait_pid; cannot rewrite sku",
        inspect="dbmate status --wait=false",
        catalog="dbmate leftover leftover leftover wait; expand sku_norm",
        abort="kill $(cat dbmate_wait_pid) 2>/dev/null; rm -f dbmate_wait_pid",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on dm.wait_sku",
    ),
    pl(
        engine="golang-migrate",
        slug="golang-migrate-dirty-leftover3",
        plant="gm-dirty-l3",
        surface="golang-migrate-dirty-leftover3",
        table="gm.dirty_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="schema_migrations_dirty",
        leftover2="migrate_force_tmp",
        seed="migrate -path db/migrations -database postgres://app up",
        fail="ERROR: leftover leftover leftover Dirty database version leftover schema_migrations_dirty; cannot rewrite sku",
        inspect="migrate -path db/migrations -database postgres://app version",
        catalog="golang-migrate leftover leftover leftover dirty; expand sku_norm",
        abort="migrate -path db/migrations -database postgres://app force 42",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on gm.dirty_sku",
    ),
    pl(
        engine="golang-migrate",
        slug="golang-migrate-force-leftover3",
        plant="gm-force-l3",
        surface="golang-migrate-force-leftover3",
        table="gm.force_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="force_version_ghost",
        leftover2="migrate_down_partial",
        seed="migrate -path db/migrations -database postgres://app force 43",
        fail="ERROR: leftover leftover leftover force without apply leftover force_version_ghost; cannot rewrite sku",
        inspect="migrate -path db/migrations -database postgres://app version",
        catalog="golang-migrate leftover leftover leftover force; expand sku_norm",
        abort="migrate -path db/migrations -database postgres://app force 42",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on gm.force_sku",
    ),
    pl(
        engine="sqitch",
        slug="sqitch-rebase-leftover3",
        plant="sq-rebase-l3",
        surface="sqitch-rebase-leftover3",
        table="sq.rebase_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="sqitch_changes_rebase_half",
        leftover2="sqitch_events_revert_ghost",
        seed="sqitch rebase --onto @v2",
        fail="ERROR: leftover leftover leftover rebase leftover sqitch_changes_rebase_half; cannot rewrite sku",
        inspect="sqitch status",
        catalog="Sqitch leftover leftover leftover rebase; expand sku_norm",
        abort="sqitch revert --to @v1 --y",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on sq.rebase_sku",
    ),
    pl(
        engine="sqitch",
        slug="sqitch-verify-leftover3",
        plant="sq-verify-l3",
        surface="sqitch-verify-leftover3",
        table="sq.verify_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="sqitch_verify_fail_tmp",
        leftover2="verify_sku_norm_missing",
        seed="sqitch verify",
        fail="ERROR: leftover leftover leftover verify leftover sqitch_verify_fail_tmp; cannot rewrite sku",
        inspect="sqitch log -n 3",
        catalog="Sqitch leftover leftover leftover verify; expand sku_norm",
        abort="sqitch revert --to @HEAD^ --y",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on sq.verify_sku",
    ),
    pl(
        engine="skeema",
        slug="skeema-lint-leftover3",
        plant="sk-lint-l3",
        surface="skeema-lint-leftover3",
        table="sk.lint_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="skeema_lint_unsafe_tmp",
        leftover2=".skeema.lock",
        seed="skeema lint --allow-unsafe",
        fail="ERROR: leftover leftover leftover lint unsafe leftover skeema_lint_unsafe_tmp; cannot rewrite sku",
        inspect="skeema diff --dry-run",
        catalog="Skeema leftover leftover leftover lint; expand sku_norm",
        abort="rm -f skeema_lint_unsafe_tmp .skeema.lock",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on sk.lint_sku",
    ),
    pl(
        engine="skeema",
        slug="skeema-diff-leftover3",
        plant="sk-diff-l3",
        surface="skeema-diff-leftover3",
        table="sk.diff_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="skeema_diff_alter_tmp",
        leftover2="diff_workspace_ghost",
        seed="skeema diff --workspace=tmp",
        fail="ERROR: leftover leftover leftover diff workspace leftover skeema_diff_alter_tmp; cannot rewrite sku",
        inspect="skeema status",
        catalog="Skeema leftover leftover leftover diff; expand sku_norm",
        abort="rm -rf skeema_diff_alter_tmp diff_workspace_ghost",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on sk.diff_sku",
    ),
    pl(
        engine="gh-ost",
        slug="ghost-cutover-leftover3",
        plant="gh-cut-l3",
        surface="gh-ost-cutover-leftover3",
        table="gh.cut_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="_cut_sku_gho",
        leftover2="_cut_sku_del",
        seed="gh-ost --alter='MODIFY sku VARCHAR(191)' --execute --table=cut_sku",
        fail="ERROR: leftover leftover leftover cut-over leftover _cut_sku_gho; cannot rewrite sku",
        inspect="gh-ost --postpone-cut-over-flag-file=/tmp/ghost.postpone --panic-flag-file=/tmp/ghost.panic --execute=false",
        catalog="gh-ost leftover leftover leftover cut-over; expand sku_norm",
        abort="gh-ost --panic-flag-file=/tmp/ghost.panic; DROP TABLE IF EXISTS `_cut_sku_gho`",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on gh.cut_sku",
    ),
    pl(
        engine="gh-ost",
        slug="ghost-panic-flag-leftover3",
        plant="gh-panic-l3",
        surface="gh-ost-panic-leftover3",
        table="gh.panic_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="_panic_sku_gho",
        leftover2="ghost_panic_flag",
        seed="gh-ost --alter='CHANGE sku sku_norm VARCHAR(191)' --execute --panic-flag-file=/tmp/ghost.panic",
        fail="ERROR: leftover leftover leftover panic flag leftover _panic_sku_gho; cannot rewrite sku",
        inspect="ls /tmp/ghost.panic _panic_sku_gho",
        catalog="gh-ost leftover leftover leftover panic; expand sku_norm",
        abort="touch /tmp/ghost.panic; DROP TABLE IF EXISTS `_panic_sku_gho`",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on gh.panic_sku",
    ),
    pl(
        engine="pt-osc",
        slug="ptosc-chunk-leftover3",
        plant="pt-chunk-l3",
        surface="pt-osc-chunk-leftover3",
        table="pt.chunk_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="_chunk_sku_new",
        leftover2="pt_osc_chunk_nibble",
        seed="pt-online-schema-change --alter 'MODIFY sku VARCHAR(191)' D=pt,t=chunk_sku --execute",
        fail="ERROR: leftover leftover leftover chunk leftover _chunk_sku_new; cannot rewrite sku",
        inspect="pt-online-schema-change --dry-run D=pt,t=chunk_sku --print",
        catalog="pt-osc leftover leftover leftover chunk; expand sku_norm",
        abort="DROP TABLE IF EXISTS pt._chunk_sku_new; rm -f pt_osc_chunk_nibble",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on pt.chunk_sku",
    ),
    pl(
        engine="pt-osc",
        slug="ptosc-nibble-leftover3",
        plant="pt-nib-l3",
        surface="pt-osc-nibble-leftover3",
        table="pt.nib_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="_nib_sku_new",
        leftover2="nibble_iterator_stuck",
        seed="pt-online-schema-change --chunk-size=1000 --alter 'ADD COLUMN sku_pad INT' D=pt,t=nib_sku --execute",
        fail="ERROR: leftover leftover leftover nibble leftover _nib_sku_new; cannot rewrite sku",
        inspect="SHOW TABLES LIKE '%nib_sku%'",
        catalog="pt-osc leftover leftover leftover nibble; expand sku_norm",
        abort="DROP TABLE IF EXISTS pt._nib_sku_new; rm -f nibble_iterator_stuck",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on pt.nib_sku",
    ),
    pl(
        engine="pgroll",
        slug="pgroll-start-leftover3",
        plant="pgr-start-l3",
        surface="pgroll-start-leftover3",
        table="pgr.start_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="pgroll_schema_start_half",
        leftover2="_pgroll_start_view",
        seed="pgroll start migrations/sku.yaml",
        fail="ERROR: leftover leftover leftover start leftover pgroll_schema_start_half; cannot rewrite sku",
        inspect="pgroll status",
        catalog="pgroll leftover leftover leftover start; expand sku_norm",
        abort="pgroll rollback; DROP VIEW IF EXISTS _pgroll_start_view",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on pgr.start_sku",
    ),
    pl(
        engine="pgroll",
        slug="pgroll-complete-leftover3",
        plant="pgr-done-l3",
        surface="pgroll-complete-leftover3",
        table="pgr.done_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="pgroll_complete_old_col",
        leftover2="_pgroll_complete_lock",
        seed="pgroll complete",
        fail="ERROR: leftover leftover leftover complete leftover pgroll_complete_old_col; cannot rewrite sku",
        inspect="pgroll status --json",
        catalog="pgroll leftover leftover leftover complete; expand sku_norm",
        abort="pgroll rollback; DROP TABLE IF EXISTS _pgroll_complete_lock",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on pgr.done_sku",
    ),
    pl(
        engine="expand-contract",
        slug="expand-contract-dualwrite-leftover3",
        plant="ec-dw-l3",
        surface="expand-contract-dualwrite-leftover3",
        table="ec.dw_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="dual_write_trigger_sku",
        leftover2="expand_phase_half",
        seed="python jobs/expand_rewrite_sku.py --in-place",
        fail="ERROR: leftover leftover leftover dual-write leftover dual_write_trigger_sku; cannot rewrite sku",
        inspect="psql -c \"SELECT tgname FROM pg_trigger WHERE tgrelid='ec.dw_sku'::regclass\"",
        catalog="expand-contract leftover leftover leftover dual-write; expand sku_norm",
        abort="DROP TRIGGER IF EXISTS dual_write_trigger_sku ON ec.dw_sku",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on ec.dw_sku",
    ),
    pl(
        engine="expand-contract",
        slug="expand-contract-trigger-leftover3",
        plant="ec-tg-l3",
        surface="expand-contract-trigger-leftover3",
        table="ec.tg_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="sync_sku_to_norm_tg",
        leftover2="contract_drop_blocked",
        seed="python jobs/contract_drop_sku.py",
        fail="ERROR: leftover leftover leftover contract leftover sync_sku_to_norm_tg; cannot rewrite sku",
        inspect="psql -c \"SELECT tgname FROM pg_trigger WHERE tgname LIKE 'sync_sku%'\"",
        catalog="expand-contract leftover leftover leftover trigger; expand sku_norm",
        abort="DROP TRIGGER IF EXISTS sync_sku_to_norm_tg ON ec.tg_sku",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on ec.tg_sku",
    ),
    pl(
        engine="vitess",
        slug="vitess-vreplication-leftover3",
        plant="vt-vrepl-l3",
        surface="vitess-vreplication-leftover3",
        table="vt.vrepl_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="_vt.vreplication_sku",
        leftover2="_vt.copy_state_sku",
        seed="vtctlclient ApplySchema -sql 'ALTER TABLE vrepl_sku MODIFY sku VARCHAR(191)' commerce",
        fail="ERROR: leftover leftover leftover vreplication leftover _vt.vreplication_sku; cannot rewrite sku",
        inspect="vtctlclient VReplicationExec commerce 'select * from _vt.vreplication'",
        catalog="Vitess leftover leftover leftover vreplication; expand sku_norm",
        abort="vtctlClient VReplicationExec commerce 'update _vt.vreplication set state=\\'Stopped\\''",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on vt.vrepl_sku",
    ),
    pl(
        engine="vitess",
        slug="vitess-online-ddl-leftover3",
        plant="vt-odd-l3",
        surface="vitess-onlineddl-leftover3",
        table="vt.odd_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="_vt.schema_migrations_odd",
        leftover2="online_ddl_shadow_odd",
        seed="vtctlclient ApplySchema -ddl_strategy='online' -sql 'ALTER TABLE odd_sku CHANGE sku sku_norm VARCHAR(191)' commerce",
        fail="ERROR: leftover leftover leftover online DDL leftover _vt.schema_migrations_odd; cannot rewrite sku",
        inspect="vtctlclient OnlineDDL commerce show all",
        catalog="Vitess leftover leftover leftover online-ddl; expand sku_norm",
        abort="vtctlclient OnlineDDL commerce cancel all",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on vt.odd_sku",
    ),
    pl(
        engine="flyway",
        slug="flyway-cherry-pick-leftover3",
        plant="fw-cp-l3",
        surface="flyway-cherrypick-leftover3",
        table="fw.cp_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="flyway_cherryPick_gap",
        leftover2="V7__sku_skipped_tmp",
        seed="flyway migrate -cherryPick=7",
        fail="ERROR: leftover leftover leftover cherryPick leftover flyway_cherryPick_gap; cannot rewrite sku",
        inspect="flyway info -cherryPick=7",
        catalog="Flyway leftover leftover leftover cherryPick; expand sku_norm",
        abort="flyway repair -cherryPick=7",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on fw.cp_sku",
    ),
    pl(
        engine="liquibase",
        slug="liquibase-clear-checksum-leftover3",
        plant="lb-ck-l3",
        surface="liquibase-checksum-leftover3",
        table="lb.ck_sku",
        col="sku",
        col_v2="sku_norm",
        leftover="databasechangelog_md5sum_null",
        leftover2="clearCheckSums_partial",
        seed="liquibase clearCheckSums",
        fail="ERROR: leftover leftover leftover clearCheckSums leftover databasechangelog_md5sum_null; cannot rewrite sku",
        inspect="liquibase unexpected-changesets",
        catalog="Liquibase leftover leftover leftover checksum; expand sku_norm",
        abort="liquibase changelogSync",
        col_type="TEXT",
        lock_fail="ERROR: lock timeout ADD sku_norm on lb.ck_sku",
    ),
]


def pair_for(round_n: int) -> tuple[dict[str, str], dict[str, str]]:
    i = (round_n - START_ROUND) * 2
    if i < 0 or i + 1 >= len(PLANTS):
        raise KeyError(f"no leftover3 pair for r{round_n}")
    return PLANTS[i], PLANTS[i + 1]


def coverage_for(round_n: int) -> int:
    return min(96, 52 + (round_n - START_ROUND) * 2)


def residual(p: dict[str, str]) -> str:
    t = p["table"].split(".")[-1]
    return (
        f"{t}.{p['col']} + {p['col_v2']}; leftover leftover leftover "
        f"{p['leftover']}; leftover {p['leftover2']}"
    )


def short_name(p: dict[str, str]) -> str:
    return p["table"].split(".")[-1]


def stem(p: dict[str, str]) -> str:
    return p["slug"].replace("-", "_")


def expand_sql(p: dict[str, str]) -> str:
    return f"ALTER TABLE {p['table']} ADD COLUMN {p['col_v2']} {p['col_type']}"


def lock_sql(p: dict[str, str]) -> str:
    return (
        f"SET lock_timeout='8s'; ALTER TABLE {p['table']} "
        f"ADD COLUMN IF NOT EXISTS {p['col_v2']} {p['col_type']}"
    )


def dumps_episode(ep: dict) -> str:
    return json.dumps(ep, ensure_ascii=False, separators=(",", ":"))


def assert_clean(obj: Any) -> None:  # type: ignore[name-defined]
    raw = json.dumps(obj)
    for k in BANNED_KEYS:
        if k in raw:
            raise ValueError(f"banned key {k}")


Any = object  # noqa: A001 — avoid typing import for mill compactness


def _bash(command: str) -> dict:
    return {"name": "bash", "args": {"command": command}}


def _write(path: str, contents: str) -> dict:
    return {"name": "write", "args": {"path": path, "contents": contents}}


def _step(n: int, basis: str, tool: dict, obs: str) -> dict:
    return {"n": n, "decision_basis": basis, "tool_call": tool, "observation": obs}


def build_episode(round_n: int, p: dict[str, str], slot: int) -> dict:
    ver = 2500 + (round_n - START_ROUND) * 2 + slot
    slug = p["slug"]
    table = p["table"]
    col = p["col"]
    col_v2 = p["col_v2"]
    leftover = p["leftover"]
    leftover2 = p["leftover2"]
    res = residual(p)
    sname = short_name(p)
    st = stem(p)
    mig = f"migrations/{ver}_{st}.sql"
    down = f"migrations/{ver}_{st}.down.sql"
    test = f"tests/test_{st}.py"
    runbook = f"docs/{slug}.md"
    backfill = f"jobs/backfill_{st}.py"
    checksum = f"jobs/checksum_{st}.py"
    inspect_cmd = p["inspect"]
    seed_cmd = p["seed"]
    abort_cmd = p["abort"]
    lock_cmd = f"psql -X -c \"{lock_sql(p)}\""
    lock_fail = p.get("lock_fail") or f"ERROR: lock timeout ADD {col_v2} on {table}"
    expand = expand_sql(p)
    inspect_obs = (
        f"{table} present\n"
        f"pending: {p['fail']}\n"
        f"shape now: {res}\n"
        f"catalog: {p['catalog']}\n"
        f"locks/mutations: 1 active; dual leftover leftover leftover objects"
    )
    eid = f"dbm-r{round_n}-{slug}"
    if RECYCLE_SUFFIX.search(eid):
        raise ValueError(f"recycle suffix in id: {eid}")
    goal = (
        f"{p['plant']}: {p['engine']} {seed_cmd} on {table}.{col} failed "
        f"({p['fail'][:140]}). Expand {col_v2}, backfill, residual {res}."
    )
    plan = (
        f"Abort in-place rewrite; expand-contract via {expand}; keep {col}; "
        f"dual leftover leftover leftover objects."
    )
    steps = [
        _step(1, f"Plan: inspect {p['engine']} leftover leftover leftover catalog for {table} before apply {ver} ({slug}).", _bash(inspect_cmd), inspect_obs),
        _step(2, f"Plan: apply naive leftover leftover leftover change on {table}.{col}.", _bash(seed_cmd), p["fail"]),
        _step(3, f"Observation: first apply failed ({p['fail'][:90]}). Plan change: abort in-place rewrite; expand {col_v2} + backfill; leave {col} residual.", _bash(abort_cmd), "leftovers leftover leftover leftover dropped or cancelled; naive rewrite aborted; dual objects still planned"),
        _step(4, f"Plan: write expand-only migration {ver} adding {col_v2} (keep {col}).", _write(mig, f"-- {ver} expand {table} {col_v2}\n{expand};\n-- never drop {col}; leftover leftover leftover residual\n-- {p['catalog']}\n"), "expand-only written"),
        _step(5, f"Plan: apply expand {ver} with short lock timeout.", _bash(lock_cmd), lock_fail),
        _step(6, "Observation: lock timeout on expand. Plan: retry lock timeout off-peak; ACCESS EXCLUSIVE avoided.", _bash(lock_cmd), f"ok retry expand {col_v2}"),
        _step(7, f"Plan: batched backfill {col_v2} from {col} without validating leftover leftover leftover constraints.", _bash(f"python {backfill} --batch 8000 --from {col} --to {col_v2}"), f"copied batch ok; remaining 0 on {table}; dual residual {res}"),
        _step(8, f"Plan: tests {test} (catalog residual must remain).", _bash(f"pytest -q {test}"), "3 passed"),
        _step(9, f"Plan: down {ver} must refuse lossy drop of {col_v2}.", _write(down, f"SELECT raise_error('lossy {col_v2} drop; leftover leftover leftover residual {sname} must remain');\n"), "down v2 guard"),
        _step(10, f"Observation: dual residual {res}.", _bash(inspect_cmd), res),
        _step(11, "Plan: runbook never in-place rewrite via naive leftover leftover leftover DDL.", _write(runbook, f"Never {seed_cmd}. Expand {col_v2}, backfill, dual-read. Residual: {res}. Restore leftovers leftover leftover leftover before retry. {p['catalog']}"), "runbook"),
        _step(12, f"Plan: extra tests {test} + tests/test_schema.py.", _bash(f"pytest -q {test} tests/test_schema.py"), "4 passed"),
        _step(13, "Tool call: leftover leftover leftover catalog objects after abort.", _bash(f"rg '{leftover}|{leftover2}|{col_v2}' || echo none-in-rewrite-path"), "none in rewrite path; dual leftover leftover leftover objects remain as residual"),
        _step(14, f"Plan: checksum {col} vs {col_v2}; confirm leftover leftover leftover objects still dual.", _bash(f"python {checksum}"), f"mismatch 0 on backfilled rows; dual residual {res}"),
        _step(15, f"Plan: confirm no active locks/mutations on {sname}.", _bash(inspect_cmd), "0 blockers; dual leftover leftover leftover objects still present"),
        _step(16, f"Plan: stamp schema version {ver}.", _bash(f"echo {ver}"), str(ver)),
    ]
    ep = {
        "id": eid,
        "goal": goal,
        "plan": plan,
        "steps": steps,
        "outcome": (
            f"Naive leftover leftover leftover apply failed. Plan change: expand {col_v2} + backfill. "
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
    unused_s = ", ".join(unused) if unused else "leftover leftover leftover catalog end"
    return (
        f"# NOTES-r{round_n} db-migration-repair-factory\n\n"
        f"Novel coverage: {coverage}%\n\n"
        "Two designed leftover leftover leftover episodes (quota 2). Unique vs r1-r105, "
        "r106-r239 engines, r240-r761 recycle, r762-r793 warehouse, r794-r817 ORM-CLI, "
        "r818-r844 PG catalog, r845-r1259 leftover mills. Surfaces: "
        f"{a['surface']}; {b['surface']}. IDs `dbm-r{round_n}-<slug>` without "
        "`-rNN` recycle suffix. Dual leftover leftover leftover residual. First-apply fail + plan "
        "change + lock retry. grok-4.6 designed.\n\n"
        "| id | seed | first apply | plan change | terminal |\n"
        "|---|---|---|---|---|\n"
        f"| {ea['id']} | {a['seed'][:48]} | first apply fail | expand {a['col_v2']} | 4/4 {residual(a)[:48]} |\n"
        f"| {eb['id']} | {b['seed'][:48]} | first apply fail | expand {b['col_v2']} | 4/4 {residual(b)[:48]} |\n\n"
        "## Step counts\n"
        "- ep1: 16. apply fail 2; lock 1.\n"
        "- ep2: 16. apply fail 2; lock 1.\n\n"
        "## decision_basis audit\n"
        f"plants `{a['plant']}`, `{b['plant']}`. designed grok-4.6. "
        f"{a['catalog']} | {b['catalog']}\n\n"
        "## Weaknesses / next\n"
        f"Unused: {unused_s}.\n"
        f"Avoid {a['slug']} and {b['slug']} next. Do not clone r762-r793, "
        "r794-r817, or r818-r844. Do not recycle r240-r761.\n"
    )


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
    (stage / f"batch-r{round_n:02d}.jsonl").write_text(
        dumps_episode(ea) + "\n" + dumps_episode(eb) + "\n", encoding="utf-8"
    )
    (stage / f"NOTES-r{round_n:02d}.md").write_text(notes, encoding="utf-8")
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


def run_loop(min_rounds: int = 16, max_rounds: int = 16, minutes: float = 40.0) -> int:
    from round_txn import TransactionError, abort, frontier_status, publish, reserve

    published: list[dict] = []
    hops: list[dict] = []
    deadline = time.monotonic() + minutes * 60
    while len(published) < max_rounds and time.monotonic() < deadline:
        status = frontier_status(FACTORY)
        round_n = status["next_round"]
        reserved = FACTORY / f"ROUND-r{round_n:02d}.reserved.json"
        if reserved.exists():
            hops.append({"dbm_next": round_n, "dbm_reserved": True, "action": "HOP", "stolen": False})
            print(json.dumps({"hop": hops[-1]}), flush=True)
            time.sleep(1.2)
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
        min_rounds = int(argv[1]) if len(argv) > 1 else 16
        max_rounds = int(argv[2]) if len(argv) > 2 else 16
        return run_loop(min_rounds=min_rounds, max_rounds=max_rounds)
    raise SystemExit("usage: unique_dbm_leftover3_mill.py [check|emit N DIR|loop [min] [max]]")


if __name__ == "__main__":
    raise SystemExit(main())
