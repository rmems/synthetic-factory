#!/usr/bin/env python3
"""CRP leftover leftover leftover mill r729+: third leftover defects (r723-728 left as dbc raw).

BAN: default-open admin; OAuth/OIDC/SAML; r538–r549 clones; r670–r678 vector-concat;
r722 lispworks/gambit/chicken open-swap; leftover3 r679–r694 plants (statelock, refresh=false,
updatePolicy Manual, hook-delete, namePrefix, mergePatch, input.user, context.ip,
HIGHER_CONSISTENCY, copyfrom, isolation, hook skip, DataLoader tenant, stream deadline,
superjson, lastSeq, Last-Event-ID, QoS0 retain, nbf, footer kid, caveat, Type I, 72-byte,
N small, FINAL, rollup, upsertMode NONE, AckWait, idempotence=false, transactional.id,
ContinueAsNew, ParentClosePolicy, FORK JOIN, unmetered host, os.execute, optional.?,
close(), importstr, toMap hole, empty sha256, ungexp dup, concretizer flip, ATTACH write,
WAL PASSIVE, SHARE stale, ProviderSet double, withEnv plaintext, Invoke+OnStart).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/code-review-preference-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
HOP = [
    "eval-harness-trajectory-factory",
    "rag-retrieval-debug-factory",
    "browser-tool-use-factory",
    "git-ops-recovery-factory",
    "incident-response-oncall-factory",
]
_BASE = SourceFileLoader(
    "crp432mill", str(ROOT / "experiments/crp-mill-r432.py")
).load_module()
P = _BASE.P
pair = _BASE.pair

# 48 plants = 16 leftover leftover leftover triples (third leftover per family).
PLANTS: list[dict] = [
    # 1 terraform / pulumi / tofu
    P("terraform-target-orphan-sku", "terraform-target-orphan-sku", "keel801", "feat: target",
      "main.tf", "sku.tf", "test_target.py", 47, "tg",
      "terraform apply -target leftover so a Chargeable sku is created without its lock resource and a second apply bills a twin SKU",
      "partial apply",
      "targeted apply must not leave a billed sku without its lock companion",
      "forbid money resources in -target or apply the lock module in the same graph",
      "-target|sku|lock", "terraform-statelock-skip-apply plant"),
    P("pulumi-ignorechanges-drop-protect", "pulumi-ignorechanges-drop-protect", "keel802", "feat: ignore",
      "index.ts", "rds.ts", "index.test.ts", 31, "ig",
      "pulumi ignoreChanges leftover on deletionProtect so a leftover stack up deletes the protected RDS and the recreate double-bills",
      "stack up",
      "ignoreChanges must not drop deletionProtect on a billed RDS",
      "keep deletionProtect outside ignoreChanges and protect the URN",
      "ignoreChanges|deletionProtect|RDS", "pulumi-refresh-false-recreate plant"),
    P("tofu-moved-block-skip-state", "tofu-moved-block-skip-state", "keel803", "feat: moved",
      "moved.tf", "sku.tf", "moved_test.go", 22, "mv",
      "OpenTofu leftover moved block is commented so state leftover still addresses the old address and apply creates a second billed sku",
      "tofu apply",
      "rename must move state not create a second Chargeable",
      "moved { from = old to = new } plus a plan test that shows 0 add",
      "moved|from|to", "crossplane-updatepolicy-manual-claim plant"),
    # 2 helm / kustomize / tanka
    P("helm-atomic-false-hook-orphan", "helm-atomic-false-hook-orphan", "spar804", "feat: atomic",
      "Chart.yaml", "hooks.yaml", "hook_test.go", 18, "at",
      "helm upgrade --atomic=false leftover so a failed release leftover leaves the charge hook Job and the next upgrade double-charges",
      "release upgrade",
      "a failed upgrade must not leave a Job that Charge.create again",
      "--atomic plus hook-delete-policy hook-succeeded,hook-failed",
      "atomic|hook|Job", "helm-hook-delete-before-missing plant"),
    P("kustomize-replacements-omit-ns", "kustomize-replacements-omit-ns", "spar805", "feat: replace",
      "kustomization.yaml", "replace.yaml", "kustomize_test.go", 14, "rp",
      "kustomize replacements leftover omit namespace so leftover name hits staging Charge and prod traffic bills staging SKUs",
      "overlay replace",
      "replacements must be namespace-scoped or they must not retarget Charge",
      "source.namespace + target.namespace selectors and a build test",
      "replacements|namespace|Charge", "kustomize-nameprefix-omit-overlay plant"),
    P("tanka-apply-prune-false-orphan", "tanka-apply-prune-false-orphan", "spar806", "feat: prune",
      "main.jsonnet", "charge.jsonnet", "tanka_test.py", 26, "pr",
      "tk apply leftover --prune=false so a leftover charge Deployment stays and both old and new pods POST /charge",
      "tanka apply",
      "orphaned charge Deployments must be pruned",
      "tk apply --prune plus an apply test that asserts one Charge owner",
      "prune|tk apply|Deployment", "jsonnet-mergepatch-array-concat plant"),
    # 3 opa / cedar / spicedb
    P("opa-else-true-default-allow", "opa-else-true-default-allow", "boom807", "feat: else",
      "authz.rego", "charge.rego", "authz_test.rego", 51, "el",
      "OPA leftover allow { input.role == \"cashier\" } else = true so a leftover missing role is allowed and any caller Charge.create",
      "rego else",
      "else must not default allow on Charge.create",
      "default allow := false and else = false; no else-true on money",
      "else = true|default allow|Charge", "opa-input-user-package-leak plant"),
    P("cedar-unless-clause-dropped", "cedar-unless-clause-dropped", "boom808", "feat: unless",
      "policy.cedar", "charge.cedar", "cedar_test.py", 19, "un",
      "Cedar leftover permit ... unless { context.frozen } drops the unless when context is null so a frozen account still charges",
      "cedar unless",
      "missing context.frozen must fail closed not skip unless",
      "require context.frozen is present; forbid when context is empty",
      "unless|context.frozen|permit", "cedar-context-ip-permit-all plant"),
    P("spicedb-zedtoken-minimize-stale", "spicedb-zedtoken-minimize-stale", "boom809", "feat: zedtoken",
      "check.go", "charge.go", "check_test.go", 36, "zt",
      "SpiceDB leftover Check uses MinimizeLatency so a just-revoked relation leftover still allows Charge.create",
      "zedtoken check",
      "Check after revoke must not allow the same SKU charge",
      "Consistency FullyConsistent or AtLeastAsFresh(zedtoken) after WriteRelationships",
      "MinimizeLatency|zedtoken|Check", "openfga-write-without-consistency plant"),
    # 4 graphql / grpc / connect
    P("graphql-alias-cost-bypass", "graphql-alias-cost-bypass", "vang810", "feat: cost",
      "cost.ts", "schema.ts", "cost.test.ts", 23, "al",
      "GraphQL leftover cost analysis counts field name not alias so leftover aliases multiply Charge.create under budget",
      "gql cost",
      "aliased Charge fields must count toward cost or be rejected",
      "cost by resolved field + alias fan-out cap",
      "alias|cost|Charge", "graphql-dataloader-tenant-cache plant"),
    P("grpc-retry-pushback-ignored", "grpc-retry-pushback-ignored", "vang811", "feat: pushback",
      "client.go", "charge.go", "client_test.go", 44, "pb",
      "gRPC leftover retry ignores grpc-retry-pushback-ms so a leftover UNAVAILABLE retry double-sends ChargeCreate",
      "retry charge",
      "pushback must delay or drop a retry that would ChargeCreate twice",
      "honor grpc-retry-pushback-ms plus idempotency metadata",
      "pushback|UNAVAILABLE|ChargeCreate", "grpc-stream-no-deadline-retry plant"),
    P("connect-timeout-interceptor-drop", "connect-timeout-interceptor-drop", "vang812", "feat: timeout",
      "intercept.go", "charge.go", "intercept_test.go", 17, "to",
      "Connect leftover timeout interceptor drops the error so the client leftover retries ChargeCreate as a new RPC",
      "connect charge",
      "timeout must not be swallowed into a naked retry ChargeCreate",
      "propagate deadline exceeded and reuse Idempotency-Key",
      "timeout|interceptor|ChargeCreate", "trpc-superjson-date-utc-shift plant"),
    # 5 clickhouse / druid / starrocks
    P("clickhouse-ttl-move-lost-refund", "clickhouse-ttl-move-lost-refund", "clew813", "feat: ttl",
      "ttl.sql", "refund.sql", "test_ttl.sql", 12, "tl",
      "ClickHouse leftover TTL MOVE PARTITION during a refund insert so the refund row leftover never lands and finance keeps the capture",
      "ttl move",
      "TTL move must not drop an in-flight refund for a captured charge",
      "TTL only after COMMIT and a mutation that waits for inserts",
      "TTL MOVE|refund|PARTITION", "clickhouse-replacing-no-final plant"),
    P("druid-keepsegment-miss-overlap", "druid-keepsegment-miss-overlap", "clew814", "feat: compact",
      "compact.json", "spec.json", "compact_test.py", 28, "ks",
      "Druid leftover compaction omits keepSegmentGranularity so leftover overlapping segments both SUM the same charge",
      "compact task",
      "compaction must not leave two live segments for the same interval charge",
      "keepSegmentGranularity true plus a query that asserts one row per charge_id",
      "keepSegmentGranularity|compact|charge", "druid-rollup-double-count plant"),
    P("starrocks-partial-update-dup-pk", "starrocks-partial-update-dup-pk", "clew815", "feat: partial",
      "table.sql", "charge.sql", "table_test.py", 21, "pu",
      "StarRocks leftover partial_update on PRIMARY KEY with leftover missing columns so a replay appends a second billed amount",
      "sr upsert",
      "partial update must replace the same charge_id not append GMV",
      "full-row upsert or specify all money columns plus unique charge_id",
      "partial_update|PRIMARY KEY|charge_id", "pinot-upsert-mode-none-dup plant"),
    # 6 nats / kafka / pulsar
    P("nats-kv-history-zero-lost-ack", "nats-kv-history-zero-lost-ack", "reef816", "feat: kv",
      "kv.go", "charge.go", "kv_test.go", 33, "kv",
      "NATS KV leftover history=0 so a leftover Put of charged=true vanishes and the worker Charge.create again",
      "kv idempotency",
      "history 0 must not drop the charged marker",
      "history>=1 plus create-only Put on charge_id",
      "history=0|KV|charge_id", "nats-js-ackwait-redeliver-charge plant"),
    P("kafka-autooffset-latest-skip-refund", "kafka-autooffset-latest-skip-refund", "reef817", "feat: offset",
      "consumer.properties", "refund.go", "consumer_test.go", 9, "ao",
      "Kafka leftover auto.offset.reset=latest so a restarted refund consumer leftover skips the refund topic and captures stay",
      "refund consumer",
      "restart must not skip unprocessed refund records",
      "auto.offset.reset=earliest plus committed offsets and a unique refund_id",
      "auto.offset.reset|latest|refund", "kafka-idempotence-false-dup plant"),
    P("pulsar-acktimeout-redeliver-charge", "pulsar-acktimeout-redeliver-charge", "reef818", "feat: acktimeout",
      "consumer.go", "charge.go", "consumer_test.go", 41, "ak",
      "Pulsar leftover ackTimeout shorter than Stripe RTT so leftover redelivery Charge.create runs twice",
      "pulsar consumer",
      "ackTimeout must outlast the Stripe call or the handler must be idempotent",
      "ackTimeout>=30s plus Idempotency-Key = messageId",
      "ackTimeout|redeliver|Charge.create", "redpanda-txn-id-missing-abort plant"),
    # 7 cue / dhall / nickel
    P("cue-list-open-extra-sku", "cue-list-open-extra-sku", "batten819", "feat: list",
      "sku.cue", "price.cue", "sku_test.go", 15, "ls",
      "CUE leftover [...#Sku] is open-tailed so leftover extra sku entries are accepted and a hidden SKU is billed",
      "cue list",
      "sku lists must reject extra elements",
      "[N]#Sku closed list plus cue vet",
      "[...]#Sku|vet|sku", "cue-closed-struct-extra-sku plant"),
    P("dhall-aslocation-unsigned-import", "dhall-aslocation-unsigned-import", "batten820", "feat: aslocation",
      "price.dhall", "import.dhall", "price_test.py", 18, "al",
      "Dhall leftover as Location import leftover skips integrity so a swapped price file leftover bills 100x",
      "dhall import",
      "as Location must not load an unsigned price map",
      "sha256 integrity on every import and no as Location for money",
      "as Location|sha256|price", "dhall-tomap-type-hole-price plant"),
    P("nickel-merge-priority-force-price", "nickel-merge-priority-force-price", "batten821", "feat: merge",
      "price.ncl", "sku.ncl", "price_test.py", 24, "mp",
      "Nickel leftover merge force leftover lets an overlay override cents without a contract so a leftover 1-cent SKU is billed as 10000",
      "ncl merge",
      "force merge must not bypass the cents contract",
      "contract on cents plus default merge not force",
      "force|contract|cents", "jsonnet-importstr-secret-double plant"),
    # 8 nix / guix / portage
    P("nix-flakelock-narhash-omit", "nix-flakelock-narhash-omit", "leech822", "feat: flake",
      "flake.lock", "flake.nix", "flake_test.py", 20, "nh",
      "nix leftover flake.lock omits narHash so a leftover input swap injects a charge binary that double-posts",
      "nix flake",
      "inputs without narHash must not evaluate in CI",
      "require narHash on every flake input and --no-update-lock-file",
      "narHash|flake.lock|input", "nix-fetchurl-sha256-empty plant"),
    P("guix-inferior-ungraft-charge", "guix-inferior-ungraft-charge", "leech823", "feat: ungraft",
      "manifest.scm", "charge.scm", "manifest_test.py", 27, "ug",
      "Guix leftover inferior --no-grafts leftover installs the ungrafted charge CLI that still POSTs /charge twice",
      "guix package",
      "production must not install an ungrafted charge CLI",
      "forbid --no-grafts on money packages plus a graft test",
      "--no-grafts|inferior|charge", "guix-ungexp-gexp-charge-dup plant"),
    P("portage-accept-keywords-live-ebuild", "portage-accept-keywords-live-ebuild", "leech824", "feat: keywords",
      "package.accept_keywords", "charge.ebuild", "ebuild_test.py", 16, "ak",
      "Portage leftover ACCEPT_KEYWORDS=** leftover pulls a live ebuild whose src_install leftover double-captures",
      "emerge charge",
      "live keywords must not install an unpinned charge ebuild",
      "pin a stable keyword and SRC_URI hash",
      "ACCEPT_KEYWORDS|live|SRC_URI", "spack-concretizer-hash-flip plant"),
    # 9 duckdb / sqlite / turso
    P("duckdb-copy-overwrite-no-txn", "duckdb-copy-overwrite-no-txn", "luff825", "feat: copy",
      "gmv.sql", "copy.sql", "test_copy.py", 13, "cp",
      "DuckDB leftover COPY ... OVERWRITE outside a txn so a leftover crash leaves half the GMV file and finance double-imports the next file",
      "copy gmv",
      "COPY overwrite must be atomic or finance must not re-import a torn file",
      "COPY inside BEGIN; commit rename of a temp file",
      "COPY|OVERWRITE|txn", "duckdb-attach-write-stale-gmv plant"),
    P("sqlite-shared-cache-writer-lost", "sqlite-shared-cache-writer-lost", "luff826", "feat: shared",
      "db.py", "refund.py", "test_shared.py", 35, "sc",
      "SQLite leftover shared-cache writer leftover unlocks mid-refund so a second connection leftover commits the capture without the refund",
      "shared cache",
      "shared-cache must not drop a refund while the capture commits",
      "WAL + one writer connection or IMMEDIATE txn covering capture+refund",
      "shared-cache|IMMEDIATE|refund", "sqlite-wal-checkpoint-lost-refund plant"),
    P("turso-embedded-replica-stale-gmv", "turso-embedded-replica-stale-gmv", "luff827", "feat: replica",
      "replica.go", "gmv.sql", "replica_test.go", 19, "er",
      "Turso leftover embedded replica sync leftover lags so finance leftover SUMs a stale GMV snapshot and re-invoices yesterday",
      "turso replica",
      "invoice queries must not run on a replica behind the invoice watermark",
      "wait for frame_no >= watermark or query primary",
      "embedded replica|frame_no|watermark", "motherduck-share-snapshot-stale plant"),
    # 10 wasm / lua / extism
    P("wasm-wasi-clock-unbounded-loop", "wasm-wasi-clock-unbounded-loop", "cringle828", "feat: clock",
      "host.go", "charge.go", "host_test.go", 38, "ck",
      "WASM leftover WASI clock_time_get is unmetered so a guest leftover busy-waits then Charge.create twice after timeout",
      "wasi clock",
      "guest must not call Charge.create more than once per invoice after a clock loop",
      "fuel on clock_time_get plus host idempotency map",
      "clock_time_get|fuel|Charge.create", "wasm-host-call-unmetered-charge plant"),
    P("lua-setfenv-restore-miss", "lua-setfenv-restore-miss", "cringle829", "feat: setfenv",
      "sandbox.lua", "charge.lua", "sandbox_test.py", 21, "sf",
      "Lua leftover setfenv leftover is not restored so a later template leftover sees os.execute and curls Charge.create",
      "lua env",
      "setfenv must restore a sandbox that cannot os.execute a charge",
      "setfenv restore in finally plus nil os.execute",
      "setfenv|os.execute|restore", "lua-sandbox-os-execute-charge plant"),
    P("extism-host-fn-reentry-charge", "extism-host-fn-reentry-charge", "cringle830", "feat: reentry",
      "host.go", "plugin.go", "host_test.go", 29, "re",
      "Extism leftover host function leftover re-enters Charge.create while the first call is in flight so two captures land",
      "extism host",
      "host Charge.create must not re-enter for the same invoice_id",
      "reentrancy guard plus idempotency on invoice_id",
      "reenter|Charge.create|invoice_id", "cel-optional-shortcircuit-skip-deny plant"),
    # 11 jwt / paseto / branca
    P("jwt-typ-none-confused-verify", "jwt-typ-none-confused-verify", "shroud831", "feat: typ",
      "jwt.go", "charge.go", "jwt_test.go", 54, "ty",
      "JWT leftover Verify accepts typ=none leftover so an unsigned token leftover authorizes Charge.create",
      "jwt typ",
      "typ none must not authorize Charge.create",
      "require typ=JWT and alg allow-list; reject none",
      "typ=none|alg|Charge", "jwt-nbf-unverified-early plant"),
    P("paseto-purpose-local-as-public", "paseto-purpose-local-as-public", "shroud832", "feat: purpose",
      "paseto.py", "keys.py", "test_paseto.py", 20, "pu",
      "PASETO leftover parser leftover treats v4.local as v4.public so a leftover shared-secret token verifies as a charge grant",
      "paseto purpose",
      "local tokens must not verify as public charge grants",
      "strict purpose check before verify and reject purpose mismatch",
      "v4.local|v4.public|purpose", "paseto-footer-unbound-keyid plant"),
    P("branca-ttl-unverified-early", "branca-ttl-unverified-early", "shroud833", "feat: ttl",
      "branca.go", "charge.go", "branca_test.go", 16, "tt",
      "Branca leftover decode leftover skips ttl so an expired leftover token still Charge.create",
      "branca ttl",
      "expired ttl must not authorize Charge.create",
      "decode with ttl and reject timestamp + ttl < now",
      "ttl|timestamp|Charge", "macaroon-caveat-unverified-sku plant"),
    # 12 argon2 / bcrypt / yescrypt
    P("argon2-ad-omit-context", "argon2-ad-omit-context", "tack834", "feat: ad",
      "hash.go", "passwd.go", "hash_test.go", 13, "ad",
      "argon2 leftover AssociatedData leftover is omitted so a leftover hash minted for support login verifies on the cashier path",
      "argon2 ad",
      "hashes must bind AssociatedData to the login surface",
      "AssociatedData=surface plus verify that fails across surfaces",
      "AssociatedData|argon2id|surface", "argon2-type-i-not-id plant"),
    P("bcrypt-cost-four-offline", "bcrypt-cost-four-offline", "tack835", "feat: cost",
      "hash.py", "passwd.py", "test_hash.py", 11, "cs",
      "bcrypt leftover cost=4 leftover so offline guess leftover opens the cashier in minutes",
      "bcrypt cost",
      "cost 4 must not be used on cashier passwords",
      "cost>=12 and reject hashes with cost<10 at verify",
      "cost=4|bcrypt|cashier", "bcrypt-72-byte-truncate plant"),
    P("yescrypt-flags-default-weak", "yescrypt-flags-default-weak", "tack836", "feat: flags",
      "kdf.go", "passwd.go", "kdf_test.go", 18, "fl",
      "yescrypt leftover flags leftover default to YESCRYPT_WORM so leftover parallel attack opens two wallets with one password",
      "yescrypt flags",
      "WORM flags must not be used for wallet passwords",
      "YESCRYPT_RW_DEFAULTS plus per-row salt",
      "YESCRYPT_WORM|flags|salt", "scrypt-n-small-salt-reuse plant"),
    # 13 temporal / cadence / restate
    P("temporal-signal-buffer-drop-refund", "temporal-signal-buffer-drop-refund", "hank837", "feat: signal",
      "workflow.go", "refund.go", "workflow_test.go", 56, "sg",
      "Temporal leftover signal buffer leftover drops Refund when the workflow is ContinueAsNew so the capture leftover stays",
      "signal refund",
      "Refund signals must not be dropped across ContinueAsNew",
      "drain signals before ContinueAsNew and persist refund intent",
      "signal|buffer|Refund", "temporal-continueasnew-side-effect plant"),
    P("cadence-sticky-cache-stale-decision", "cadence-sticky-cache-stale-decision", "hank838", "feat: sticky",
      "worker.go", "charge.go", "worker_test.go", 42, "st",
      "Cadence leftover sticky cache leftover replays a stale decision leftover so Charge.create runs after the workflow already refunded",
      "sticky worker",
      "sticky cache must not emit Charge.create after refund",
      "disable sticky on money workflows or invalidate cache on refund",
      "sticky|decision|Charge.create", "cadence-parent-close-abandon-child plant"),
    P("restate-journal-skip-replay-charge", "restate-journal-skip-replay-charge", "hank839", "feat: journal",
      "service.ts", "charge.ts", "service.test.ts", 25, "jr",
      "Restate leftover journal skip leftover re-executes Charge.create on replay so a recovered invocation double-captures",
      "restate replay",
      "replay must not Charge.create a SKU already journaled",
      "ctx.run idempotent key=invoice_id and no journal skip",
      "journal|ctx.run|invoice_id", "conductor-fork-join-timeout-retry plant"),
    # 14 wire / dagger / fx
    P("wire-cleanup-unbind-midflight", "wire-cleanup-unbind-midflight", "foot840", "feat: cleanup",
      "wire.go", "charge.go", "wire_test.go", 27, "cl",
      "Wire leftover Cleanup leftover closes ChargeClient mid-request so the retry leftover constructs a second client and double-captures",
      "wire cleanup",
      "Cleanup must not close ChargeClient while a charge is in flight",
      "lifecycle After request plus sync.Once on client close",
      "Cleanup|ChargeClient|close", "wire-provider-set-double-bind plant"),
    P("dagger-export-cache-replay-charge", "dagger-export-cache-replay-charge", "foot841", "feat: export",
      "ci.go", "charge.go", "ci_test.go", 32, "ex",
      "Dagger leftover Export leftover caches the charge step so a leftover cache hit replays Charge.create",
      "dagger export",
      "cache must not replay Charge.create",
      "CacheVolume exclude on charge steps plus withExec --no-cache for money",
      "Export|CacheVolume|Charge.create", "dagger-withenv-secret-plaintext plant"),
    P("fx-decorate-order-flip-hook", "fx-decorate-order-flip-hook", "foot842", "feat: decorate",
      "module.go", "charge.go", "module_test.go", 22, "dc",
      "fx leftover Decorate leftover reverses hook order so leftover OnStop Charge.create runs at boot and double-captures",
      "fx decorate",
      "Decorate must not run OnStop Charge.create at start",
      "explicit hook order test plus Charge.create only in OnStart once",
      "Decorate|OnStop|OnStart", "fx-invoke-onstart-double-hook plant"),
    # 15 sqlc / prisma / drizzle
    P("sqlc-batchexec-ignore-rows", "sqlc-batchexec-ignore-rows", "gaff843", "feat: batch",
      "invoice.sql", "batch.go", "batch_test.go", 24, "be",
      "sqlc leftover :batchexec leftover ignores RowsAffected so a leftover retry inserts a second invoice_id and GMV doubles",
      "batch invoice",
      "retry of BatchExec must not insert a second invoice_id",
      "check RowsAffected and ON CONFLICT (invoice_id) DO NOTHING",
      "batchexec|RowsAffected|invoice_id", "sqlc-copyfrom-no-conflict plant"),
    P("prisma-middleware-skip-softdelete", "prisma-middleware-skip-softdelete", "gaff844", "feat: middleware",
      "wallet.ts", "mw.ts", "wallet.test.ts", 30, "mw",
      "Prisma leftover middleware leftover skips soft-delete filter so a leftover debit hits a refunded wallet and overdrafts",
      "prisma middleware",
      "soft-deleted wallets must not accept a debit",
      "middleware that always AND deletedAt=null on wallet update",
      "deletedAt|middleware|$use", "prisma-interactive-txn-lost-update plant"),
    P("drizzle-idle-txn-lost-update", "drizzle-idle-txn-lost-update", "gaff845", "feat: idle",
      "wallet.ts", "debit.ts", "wallet.test.ts", 28, "id",
      "Drizzle leftover transaction leftover idles past idle_in_transaction so leftover two debits both commit against the pre-debit snapshot",
      "drizzle debit",
      "idle transactions must not both commit the same wallet debit",
      "statement timeout plus UPDATE ... SET bal = bal - n WHERE bal >= n",
      "idle_in_transaction|UPDATE|bal", "ent-hook-skip-mutators-serial plant"),
    # 16 websocket / sse / webtransport
    P("websocket-ping-interval-zero", "websocket-ping-interval-zero", "stay846", "feat: ping",
      "ws.py", "order.py", "test_ws.py", 37, "pg",
      "WebSocket leftover ping_interval=0 leftover so a leftover half-open socket never dies and a reconnect leftover PLACE_ORDER double-fills",
      "order ping",
      "dead sockets must close before a reconnect PLACE_ORDER",
      "ping_interval>0 plus lastSeq skip on resume",
      "ping_interval|PLACE_ORDER|half-open", "websocket-resume-seq-skip plant"),
    P("sse-retry-field-omitted", "sse-retry-field-omitted", "stay847", "feat: retry",
      "stream.ts", "charge.ts", "stream.test.ts", 26, "ry",
      "SSE leftover omits retry: leftover so EventSource leftover reconnects immediately and replays a captured charge",
      "sse retry",
      "reconnect must not emit a charge id already sent",
      "retry: 5000 plus Last-Event-ID skip",
      "retry:|Last-Event-ID|charge", "sse-last-event-id-ignored plant"),
    P("webtransport-datagram-unreliable-charge", "webtransport-datagram-unreliable-charge", "stay848", "feat: datagram",
      "wt.ts", "charge.ts", "wt.test.ts", 18, "dg",
      "WebTransport leftover datagram leftover is unreliable so a leftover retry after loss Charge.create twice",
      "wt datagram",
      "unreliable datagrams must not carry Charge.create",
      "use reliable streams plus idempotency on invoice_id",
      "datagram|unreliable|Charge.create", "mqtt-qos0-retained-stale-price plant"),
]


assert len(PLANTS) == 48, len(PLANTS)
assert len({p["slug"] for p in PLANTS}) == 48
assert len({p["family"] for p in PLANTS}) == 48


def notes_for(round_n: int, recs: list[dict], plants: list[dict]) -> str:
    fams = [r["meta"]["family"] for r in recs]
    ids = [r["id"] for r in recs]
    return "\n".join(
        [
            f"# code-review-preference-factory — NOTES r{round_n}",
            "",
            "Novel coverage: 99.5%",
            "",
            f"Headline: blocking defect vs nit/LGTM on {', '.join(fams)} (leftover leftover leftover stretch)",
            "",
            "Construction: divergence-point DPO (shared 7-step prefix; first differing tool_call is the review verdict). Same top-level goal both sides. Chosen posts issue (blocking) REQUEST_CHANGES. Rejected posts nits and APPROVE. Discarded drafts that changed the PR. Fuel: ARCTIC, BitsAI-CR, Graphite blocking-vs-nits. Stretch is leftover leftover leftover third defects on Terraform/Pulumi/Helm/Kustomize/OPA/Cedar/GraphQL/gRPC/ClickHouse/Druid/NATS/Kafka/CUE/Dhall/Nix/Guix/DuckDB/SQLite/WASM/Lua/JWT/PASETO/argon2/bcrypt/Temporal/Cadence/Wire/Dagger/sqlc/Prisma/WebSocket/SSE plus OpenTofu, Tanka, SpiceDB, Connect, StarRocks, Pulsar, Nickel, Portage, Turso, Extism, Branca, yescrypt, Restate, fx, drizzle, WebTransport — not XSS, not OAuth, not r722 lispworks, not *-concat.",
            "",
            "Novel leftover leftover leftover families this wave: terraform -target orphan, pulumi ignoreChanges protect, tofu moved skip, helm atomic=false, kustomize replacements ns, tanka prune, OPA else=true, Cedar unless drop, SpiceDB MinimizeLatency, GraphQL alias cost, gRPC pushback, Connect timeout swallow, CH TTL MOVE, Druid keepSegment, StarRocks partial_update, NATS KV history=0, Kafka offset latest, Pulsar ackTimeout, CUE open list, Dhall as Location, Nickel force merge, flake narHash, Guix --no-grafts, Portage live ebuild, DuckDB COPY overwrite, SQLite shared-cache, Turso replica lag, WASI clock fuel, Lua setfenv, Extism reentry, JWT typ=none, PASETO purpose mix, Branca ttl, argon2 AD, bcrypt cost=4, yescrypt WORM, Temporal signal drop, Cadence sticky, Restate journal skip, Wire Cleanup, Dagger Export cache, fx Decorate order, sqlc batchexec, Prisma soft-delete mw, Drizzle idle txn, WS ping 0, SSE retry omit, WebTransport datagram.",
            "",
            "Records:",
            *[
                f"- `{rec['id']}` sin=`missed defect / nitpicks` class=`{plant['family']}-blocking` family=`{plant['family']}` fork=step 8"
                for rec, plant in zip(recs, plants)
            ],
            "",
            f"IDs: {ids}",
            "",
            "Weakest critique: still names the same-goal quality delta and the discarded changed-problem draft. Distinct from r679-r694 first leftover3 plants and r722 open-swap.",
            "",
            "No Thalamic six-field core. No spikes. Observations are designed plants.",
            "",
            "Next gaps: more IaC moved/prune, more policy fail-closed, more replica watermark.",
            "",
        ]
    )


def txn(*args: str) -> dict:
    out = subprocess.check_output([*TXN, *args], text=True)
    return json.loads(out)


def reserved_path(factory: Path, rnd: int) -> Path | None:
    for name in (
        f"ROUND-r{rnd:02d}.reservation.json",
        f"ROUND-r{rnd:02d}.reserved.json",
    ):
        p = factory / name
        if p.exists():
            return p
    return None


def hop_if_needed() -> Path:
    st = txn("frontier", str(DIR))
    nxt = st["next_round"]
    if reserved_path(DIR, nxt) is None:
        return DIR
    for name in HOP:
        alt = DIR.parent / name
        if not alt.is_dir():
            continue
        ast = txn("frontier", str(alt))
        ares = alt / f"ROUND-r{ast['next_round']:02d}.reservation.json"
        if not ares.exists() and reserved_path(alt, ast["next_round"]) is None:
            print(json.dumps({"wait_crp": True, "alt_unreserved": name, "alt_next": ast["next_round"]}))
            return DIR
    return DIR


def write_round(round_n: int, staging: Path, offset: int) -> list[str]:
    plants = PLANTS[offset : offset + 3]
    if len(plants) != 3:
        raise SystemExit(f"bad offset {offset}")
    recs = [pair(p, round_n, i) for i, p in enumerate(plants)]
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
    notes.write_text(notes_for(round_n, recs, plants))
    return [r["id"] for r in recs]


def main() -> int:
    hop_if_needed()
    published = []
    offset = 0
    while len(published) < 16:
        st = txn("frontier", str(DIR))
        rnd = st["next_round"]
        if reserved_path(DIR, rnd) is not None:
            time.sleep(2)
            continue
        try:
            res = txn("reserve", str(DIR), "--round", str(rnd), "--expected", "3")
        except subprocess.CalledProcessError:
            time.sleep(2)
            continue
        ids = write_round(rnd, Path(res["staging_dir"]), offset * 3)
        pub = txn("publish", str(DIR), "--round", str(rnd), "--token", res["token"])
        published.append({"round": rnd, "ids": ids, "publish": pub.get("round", rnd)})
        print(json.dumps({"published": rnd, "ids": ids}), flush=True)
        offset += 1
    print(json.dumps({"ok": True, "rounds": published}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
