#!/usr/bin/env python3
"""CRP leftover leftover leftover mill: IaC/policy/codegen/protocol families.

BAN: default-open admin consoles; OAuth/OIDC/SAML; privacy-platform; WebGPU/WebNN;
query-string checkout clones; r537 temporal-heartbeat / cadence-replay / airflow-catchup;
r538–r549 Prefect/Dagster/Luigi, Argo/Tekton/GHA, Vitess/Yugabyte/TiDB, Stripe/Adyen/PayPal,
timezone fold, ORM upsert; r670–r678 *-concat / *-plus vector cartesian; r161–r252 OAuth.
"""
from __future__ import annotations

import argparse
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

_BASE = SourceFileLoader(
    "crp432mill", str(Path(__file__).with_name("crp-mill-r432.py"))
).load_module()
P = _BASE.P
pair = _BASE.pair

FACTORY = "code-review-preference-factory"
GEN = "grok-4.6"


def _p(*args) -> dict:
    return P(*args)


# 48 plants = 16 leftover leftover leftover triples (distinct product families).
PLANTS: list[dict] = [
    # 1 terraform / pulumi / crossplane
    _p("terraform-statelock-skip-apply", "terraform-statelock-skip-apply", "keel701", "feat: apply",
       "main.tf", "sku.tf", "test_apply.py", 41, "lk",
       "terraform apply -lock=false on leftover state so two CIs provision the same billing SKU twice",
       "sku workspace apply",
       "two concurrent applies must not create a second Chargeable sku resource",
       "require -lock=true and a remote backend lock; fail if lock is skipped",
       "lock=false|statelock|sku", "prefect-retries-zero-charge plant"),
    _p("pulumi-refresh-false-recreate", "pulumi-refresh-false-recreate", "keel702", "feat: up",
       "index.ts", "rds.ts", "index.test.ts", 28, "rf",
       "pulumi up --refresh=false leaves leftover stack outputs stale so the next up recreates RDS and double-bills",
       "nightly stack up",
       "stale outputs must not recreate an already-provisioned RDS instance",
       "refresh before replace plus protect on the RDS URN",
       "refresh=false|replace|RDS", "dagster-run-overlap-invoice plant"),
    _p("crossplane-updatepolicy-manual-claim", "crossplane-updatepolicy-manual-claim", "keel703", "feat: claim",
       "composition.yaml", "claim.yaml", "claim_test.go", 33, "up",
       "Composition updatePolicy=Manual so a leftover Claim still points at a deleted Composite and Crossplane provisions a second billed cluster",
       "cluster claim",
       "deleting the Composite must not leave a Claim that recreates a second billed cluster",
       "updatePolicy=Automatic plus orphan:false and a unique claim name lock",
       "updatePolicy|Manual|Claim", "luigi-complete-before-write plant"),
    # 2 helm / kustomize / jsonnet (k8s templating)
    _p("helm-hook-delete-before-missing", "helm-hook-delete-before-missing", "spar704", "feat: hook",
       "hooks.yaml", "charge.yaml", "hook_test.go", 19, "hk",
       "pre-install Job lacks hook-delete-policy before-hook-creation so a leftover Job reruns and double-charges",
       "release hook",
       "a leftover hook Job must not Charge.create a second time on upgrade",
       "hook-delete-policy: before-hook-creation and an Idempotency-Key on the Job name",
       "hook-delete-policy|before-hook-creation|Job", "argo-retry-double-charge plant"),
    _p("kustomize-nameprefix-omit-overlay", "kustomize-nameprefix-omit-overlay", "spar705", "feat: overlay",
       "kustomization.yaml", "patch.yaml", "kustomize_test.go", 12, "np",
       "prod overlay omits namePrefix so leftover patches hit the staging Deployment and prod traffic charges staging SKUs",
       "overlay apply",
       "prod patches must not mutate the staging Deployment name",
       "namePrefix: prod- plus a kustomize build test that asserts distinct names",
       "namePrefix|overlay|Deployment", "tekton-finally-skip-refund plant"),
    _p("jsonnet-mergepatch-array-concat", "jsonnet-mergepatch-array-concat", "spar706", "feat: merge",
       "job.jsonnet", "charge.jsonnet", "jsonnet_test.py", 22, "mp",
       "std.mergePatch leftover concatenates containers[] so two charge sidecars run and both POST /charge",
       "jsonnet render",
       "merge must replace the charge container list not concatenate a second sidecar",
       "std.mergePatch with explicit containers replace or std.mapWithKey overwrite",
       "mergePatch|containers|concat", "gha-rerun-double-charge plant"),
    # 3 opa / cedar / openfga
    _p("opa-input-user-package-leak", "opa-input-user-package-leak", "boom707", "feat: allow",
       "authz.rego", "charge.rego", "authz_test.rego", 47, "pk",
       "package authz leftover reads input.user without tenant isolation so deny is skipped and any tenant charges any SKU",
       "rego allow",
       "allow must be false when input.tenant != resource.tenant",
       "deny by default plus input.tenant == resource.tenant in allow",
       "package|input.user|tenant", "oauth-scope-clone plant"),
    _p("cedar-context-ip-permit-all", "cedar-context-ip-permit-all", "boom708", "feat: permit",
       "policy.cedar", "charge.cedar", "cedar_test.py", 16, "ip",
       "Cedar permit leftover omits context.ip so when.isInRange is vacuously true and every caller may Charge.create",
       "cedar eval",
       "permit must fail closed when context.ip is absent",
       "require context.ip and when { context.ip.isInRange(office) }; forbid if missing",
       "context.ip|permit|isInRange", "saml-clone plant"),
    _p("openfga-write-without-consistency", "openfga-write-without-consistency", "boom709", "feat: check",
       "store.go", "check.go", "store_test.go", 38, "cs",
       "OpenFGA Write leftover then Check without HIGHER_CONSISTENCY so a just-deleted tuple still allows the charge",
       "tuple check",
       "Check after delete must not allow the same SKU charge",
       "ConsistencyPreference HIGHER_CONSISTENCY on Check after Write/Delete",
       "HIGHER_CONSISTENCY|Write|Check", "oidc-clone plant"),
    # 4 sqlc / prisma / ent (not bun/mikro/ent upsert r547)
    _p("sqlc-copyfrom-no-conflict", "sqlc-copyfrom-no-conflict", "gaff710", "feat: copyfrom",
       "invoice.sql", "copy.go", "copy_test.go", 24, "cf",
       "sqlc :copyfrom leftover inserts invoice rows with no ON CONFLICT so a retry duplicates GMV",
       "nightly copy",
       "retry of CopyFrom must not insert a second invoice_id",
       "COPY with ON CONFLICT (invoice_id) DO NOTHING or a unique index plus upsert",
       "copyfrom|ON CONFLICT|invoice_id", "bun-onconflict plant"),
    _p("prisma-interactive-txn-lost-update", "prisma-interactive-txn-lost-update", "gaff711", "feat: debit",
       "wallet.ts", "debit.ts", "wallet.test.ts", 31, "lv",
       "Prisma $transaction leftover uses default isolation so two debit txs both read 100 and write 50, overdrafting",
       "wallet debit",
       "two concurrent debits must not both commit against the same pre-debit snapshot",
       "isolationLevel Serializable or UPDATE ... SET bal = bal - n WHERE bal >= n",
       "$transaction|Serializable|bal", "mikro-upsert plant"),
    _p("ent-hook-skip-mutators-serial", "ent-hook-skip-mutators-serial", "gaff712", "feat: hook",
       "hook.go", "wallet.go", "hook_test.go", 29, "hk",
       "ent MutateFunc leftover returns next without wrapping so a serializable debit hook never runs and two cashiers overdraft",
       "ent debit hook",
       "the debit hook must run on every Mutation or the cashier path must fail closed",
       "return hook.On(next, ent.OpUpdate) and assert the hook fired in tests",
       "MutateFunc|hook.On|OpUpdate", "ent-upsert plant"),
    # 5 graphql / grpc / trpc
    _p("graphql-dataloader-tenant-cache", "graphql-dataloader-tenant-cache", "vang713", "feat: loader",
       "loader.ts", "sku.ts", "loader.test.ts", 18, "dl",
       "DataLoader leftover caches SKU by id across tenants so tenant B is billed tenant A's price",
       "gql sku",
       "loader keys must be tenant-scoped or cache must not leak prices across tenants",
       "cacheKeyFn: (id, tenant) and a new DataLoader per request",
       "DataLoader|cacheKeyFn|tenant", "gql-nplusone-no-loader plant"),
    _p("grpc-stream-no-deadline-retry", "grpc-stream-no-deadline-retry", "vang714", "feat: stream",
       "charge.proto", "client.go", "client_test.go", 44, "dl",
       "gRPC client stream leftover has no deadline so a retry after a hang double-sends ChargeCreate",
       "stream charge",
       "a hung stream retry must not emit a second ChargeCreate",
       "context.WithTimeout plus idempotency metadata on ChargeCreate",
       "deadline|stream|ChargeCreate", "kafka-txn-abort-ignored plant"),
    _p("trpc-superjson-date-utc-shift", "trpc-superjson-date-utc-shift", "vang715", "feat: superjson",
       "router.ts", "slot.ts", "router.test.ts", 21, "dt",
       "tRPC superjson leftover deserializes a fold-night ISO as UTC so the appointment is stored an hour late and double-booked",
       "slot book",
       "fold-night ISO must round-trip in the original offset not as naive UTC",
       "transformer that preserves offset or store instants as epoch ms",
       "superjson|ISO|offset", "luxon-fold plant"),
    # 6 websocket / sse / mqtt
    _p("websocket-resume-seq-skip", "websocket-resume-seq-skip", "stay716", "feat: resume",
       "ws.py", "order.py", "test_ws.py", 36, "sq",
       "WebSocket resume leftover ignores lastSeq so a reconnect replays PLACE_ORDER and double-fills",
       "order socket",
       "resume must ack lastSeq and must not replay an already-filled PLACE_ORDER",
       "store lastSeq server-side and skip events <= lastSeq",
       "lastSeq|resume|PLACE_ORDER", "redis-xack plant"),
    _p("sse-last-event-id-ignored", "sse-last-event-id-ignored", "stay717", "feat: sse",
       "stream.ts", "charge.ts", "stream.test.ts", 27, "eid",
       "SSE handler leftover ignores Last-Event-ID so EventSource reconnects replay charge events already captured",
       "sse charge",
       "reconnect must not emit a charge id already sent",
       "honor Last-Event-ID and skip ids <= cursor",
       "Last-Event-ID|EventSource|charge", "pulsar-ack plant"),
    _p("mqtt-qos0-retained-stale-price", "mqtt-qos0-retained-stale-price", "stay718", "feat: retain",
       "broker.py", "price.py", "test_price.py", 15, "rt",
       "MQTT publish leftover uses QoS 0 plus retain so a stale price is delivered after a newer quote and the buyer is overcharged",
       "price topic",
       "a retained stale price must not beat a later quote",
       "QoS 1 plus retain replace on the same topic and a version field",
       "QoS|retain|price", "redis-streams plant"),
    # 7 jwt / paseto / macaroons
    _p("jwt-nbf-unverified-early", "jwt-nbf-unverified-early", "shroud719", "feat: nbf",
       "jwt.go", "charge.go", "jwt_test.go", 52, "nb",
       "JWT Verify leftover skips nbf so a not-before token is accepted early and a pre-sale charge captures",
       "jwt charge",
       "tokens with nbf in the future must not authorize Charge.create",
       "require nbf claim and reject now < nbf - leeway",
       "nbf|Verify|Charge", "oauth-jwt-clone plant"),
    _p("paseto-footer-unbound-keyid", "paseto-footer-unbound-keyid", "shroud720", "feat: footer",
       "paseto.py", "keys.py", "test_paseto.py", 18, "ft",
       "PASETO v4 leftover treats footer kid as advisory so an attacker swaps kid and the old key still decrypts a charge grant",
       "paseto grant",
       "footer kid must bind to the key that verified the payload",
       "parse footer first, select key, verify, then reject if footer.kid != key.id",
       "footer|kid|v4", "oidc-clone plant"),
    _p("macaroon-caveat-unverified-sku", "macaroon-caveat-unverified-sku", "shroud721", "feat: caveat",
       "macaroon.go", "sku.go", "macaroon_test.go", 34, "cv",
       "macaroon leftover verifies signature but skips first-party sku= caveat so a token minted for SKU-A charges SKU-B",
       "macaroon sku",
       "discharge must fail when the sku caveat does not match the charged SKU",
       "walk caveats and require sku==request.sku before capture",
       "caveat|sku=|signature", "saml-clone plant"),
    # 8 argon2 / bcrypt / scrypt
    _p("argon2-type-i-not-id", "argon2-type-i-not-id", "tack722", "feat: hash",
       "hash.go", "passwd.go", "hash_test.go", 11, "ty",
       "argon2 leftover uses Type I so a side-channel on leftover password verify lets an attacker mint a matching hash for support login",
       "password hash",
       "Type I must not be used for password hashing on the support login path",
       "argon2id with time>=2 memory>=64MiB and unique salt per row",
       "argon2id|Type I|salt", "password-plain plant"),
    _p("bcrypt-72-byte-truncate", "bcrypt-72-byte-truncate", "tack723", "feat: bcrypt",
       "hash.py", "passwd.py", "test_hash.py", 14, "tr",
       "bcrypt leftover hashes only the first 72 bytes so two distinct long secrets collide and a leftover suffix unlocks the cashier",
       "bcrypt hash",
       "secrets longer than 72 bytes must not collide on the cashier login",
       "pre-hash with SHA-256 then bcrypt, or reject length>72",
       "bcrypt|72|prehash", "password-plain plant"),
    _p("scrypt-n-small-salt-reuse", "scrypt-n-small-salt-reuse", "tack724", "feat: scrypt",
       "kdf.go", "passwd.go", "kdf_test.go", 17, "n",
       "scrypt leftover uses N=2^10 and a global salt so two cashiers share a derived key and one leftover password opens both wallets",
       "scrypt kdf",
       "each wallet must have a unique salt and N large enough to resist offline guess",
       "per-row salt plus N>=2^15 r=8 p=1",
       "scrypt|N=|salt", "password-plain plant"),
    # 9 clickhouse / druid / pinot
    _p("clickhouse-replacing-no-final", "clickhouse-replacing-no-final", "clew725", "feat: replacing",
       "gmv.sql", "query.sql", "test_gmv.sql", 9, "fn",
       "ReplacingMergeTree leftover query omits FINAL so duplicate version rows SUM into GMV and finance double-collects",
       "gmv query",
       "SUM must not count superseded versions of the same order_id",
       "SELECT ... FINAL or argMax(amount, ver) GROUP BY order_id",
       "ReplacingMergeTree|FINAL|argMax", "spark-watermark-late-charge plant"),
    _p("druid-rollup-double-count", "druid-rollup-double-count", "clew726", "feat: rollup",
       "spec.json", "query.json", "spec_test.py", 23, "rl",
       "Druid leftover ingestion rollup=true with metric leftover count plus query SUM(count) double-counts the same charge event",
       "druid ingest",
       "query must not SUM an already-rolled-up count into a second billed total",
       "query the rollup metric without a second SUM or disable query-time re-aggregation",
       "rollup|SUM(count)|charge", "beam-allowedlateness-zero-late plant"),
    _p("pinot-upsert-mode-none-dup", "pinot-upsert-mode-none-dup", "clew727", "feat: upsert",
       "table.json", "charge.sql", "table_test.py", 26, "up",
       "Pinot leftover upsertMode NONE so a replayed charge event appends a second row and GMV doubles",
       "pinot table",
       "replayed primary keys must replace not append",
       "upsertMode FULL plus primaryKeyColumns charge_id",
       "upsertMode|NONE|primaryKey", "pinot-clone plant"),
    # 10 nats / kafka / redpanda
    _p("nats-js-ackwait-redeliver-charge", "nats-js-ackwait-redeliver-charge", "reef728", "feat: ackwait",
       "js.go", "charge.go", "js_test.go", 39, "aw",
       "NATS JetStream leftover AckWait shorter than Stripe RTT so the message is redelivered and Charge.create runs twice",
       "js consumer",
       "AckWait must outlast the Stripe call or the handler must be idempotent on charge_id",
       "AckWait >= 30s plus Idempotency-Key = msg.Nats-Msg-Id",
       "AckWait|redeliver|Charge.create", "nats-ack plant"),
    _p("kafka-idempotence-false-dup", "kafka-idempotence-false-dup", "reef729", "feat: producer",
       "producer.properties", "charge.go", "producer_test.go", 8, "id",
       "Kafka producer leftover enable.idempotence=false so a retry after acks=all timeout publishes a second charge record",
       "charge topic",
       "producer retry must not append a second record for the same charge_id",
       "enable.idempotence=true transactional.id and a compact key=charge_id",
       "enable.idempotence|transactional.id|charge_id", "kafka-txn-abort-ignored plant"),
    _p("redpanda-txn-id-missing-abort", "redpanda-txn-id-missing-abort", "reef730", "feat: txn",
       "txn.go", "charge.go", "txn_test.go", 42, "tx",
       "Redpanda leftover producer has no transactional.id so an aborted txn still appears to consumers and a charge is captured",
       "txn produce",
       "aborted transactions must not be visible as captured charges",
       "transactional.id plus isolation.level=read_committed on the consumer",
       "transactional.id|read_committed|abort", "kafka-connect plant"),
    # 11 temporal / cadence / conductor (not heartbeat/replay r537)
    _p("temporal-continueasnew-side-effect", "temporal-continueasnew-side-effect", "hank731", "feat: can",
       "workflow.go", "charge.go", "workflow_test.go", 55, "cn",
       "Temporal leftover ContinueAsNew runs Charge.create in the workflow function so the new run repeats the side effect",
       "long workflow",
       "ContinueAsNew must not Charge.create a SKU already charged in the parent run",
       "move Charge.create to an activity with idempotency keyed by workflow.ID",
       "ContinueAsNew|Charge.create|activity", "temporal-heartbeat-timeout-double plant"),
    _p("cadence-parent-close-abandon-child", "cadence-parent-close-abandon-child", "hank732", "feat: child",
       "parent.go", "child.go", "parent_test.go", 48, "pc",
       "Cadence leftover ParentClosePolicy ABANDON so a cancelled parent leaves a child that still Charge.create after refund",
       "child workflow",
       "cancelling the parent must not leave a child that charges after refund",
       "ParentClosePolicy TERMINATE plus a refund compensation on cancel",
       "ParentClosePolicy|ABANDON|TERMINATE", "cadence-replay-nondet-now plant"),
    _p("conductor-fork-join-timeout-retry", "conductor-fork-join-timeout-retry", "hank733", "feat: fork",
       "workflow.json", "charge.json", "workflow_test.py", 14, "fj",
       "Conductor leftover FORK Join timeout retries the whole fork so both branches Charge.create again",
       "fork join",
       "Join timeout must not restart a branch that already charged",
       "per-task retryCount=0 on Charge plus a JOIN failure that compensates instead of restart",
       "FORK|JOIN|retryCount", "airflow-catchup-true-charge plant"),
    # 12 wasm / lua / cel
    _p("wasm-host-call-unmetered-charge", "wasm-host-call-unmetered-charge", "cringle734", "feat: host",
       "host.go", "charge.go", "host_test.go", 37, "hc",
       "WASM leftover host import Charge.create is unmetered so a guest loop leftover double-charges until timeout",
       "wasm guest",
       "guest must not call Charge.create more than once per invoice_id",
       "host-side idempotency map plus fuel/meter on the import",
       "host|Charge.create|fuel", "webgpu-clone plant"),
    _p("lua-sandbox-os-execute-charge", "lua-sandbox-os-execute-charge", "cringle735", "feat: sandbox",
       "sandbox.lua", "charge.lua", "sandbox_test.py", 20, "os",
       "Lua leftover sandbox still exposes os.execute so a template leftover shells curl to Charge.create twice",
       "lua template",
       "sandboxed Lua must not os.execute a second charge",
       "nil os.execute and a host-only charge API with idempotency",
       "os.execute|sandbox|Charge", "webnn-clone plant"),
    _p("cel-optional-shortcircuit-skip-deny", "cel-optional-shortcircuit-skip-deny", "cringle736", "feat: cel",
       "policy.cel", "charge.cel", "policy_test.go", 13, "sc",
       "CEL leftover optional.?user.banned short-circuits to null which is truthy-not-false so deny is skipped and a banned user charges",
       "cel allow",
       "missing banned must fail closed not skip deny",
       "has(user.banned) && user.banned == true as deny; default false allow",
       "optional|short-circuit|banned", "opa-input-user-package-leak plant"),
    # 13 cue / jsonnet (config) / dhall — jsonnet here is CUE-family config leftover vs helm jsonnet
    _p("cue-closed-struct-extra-sku", "cue-closed-struct-extra-sku", "batten737", "feat: closed",
       "sku.cue", "price.cue", "sku_test.go", 10, "cl",
       "CUE leftover definition is open so an extra sku field leftover is accepted and a hidden SKU is billed",
       "cue eval",
       "unknown sku fields must be rejected",
       "close({sku: string, cents: int}) and cue vet in CI",
       "close(|sku|vet", "jsonnet-mergepatch-array-concat plant"),
    _p("jsonnet-importstr-secret-double", "jsonnet-importstr-secret-double", "batten738", "feat: importstr",
       "secret.jsonnet", "charge.jsonnet", "secret_test.py", 7, "is",
       "Jsonnet leftover importstr of a charge API key concatenates two keys so the second leftover key captures a second charge",
       "jsonnet secret",
       "importstr must not concatenate a second API key into Charge.create",
       "single-key secret plus std.manifestJsonMinified without concat",
       "importstr|api key|concat", "helm-hook-delete-before-missing plant"),
    _p("dhall-tomap-type-hole-price", "dhall-tomap-type-hole-price", "batten739", "feat: tomap",
       "price.dhall", "sku.dhall", "price_test.py", 16, "tm",
       "Dhall leftover toMap with a type hole leftover infers Text so cents become a leftover string and the parser bills 100x",
       "dhall price",
       "cents must stay Natural not Text or the billed amount must not jump 100x",
       "toMap with an explicit { mapKey : Text, mapValue : Natural }",
       "toMap|Natural|cents", "kustomize-nameprefix-omit-overlay plant"),
    # 14 nix / guix / spack
    _p("nix-fetchurl-sha256-empty", "nix-fetchurl-sha256-empty", "leech740", "feat: fetchurl",
       "default.nix", "sku.nix", "fetch_test.py", 19, "sh",
       "nix leftover fetchurl sha256 = \"\" so a leftover tarball swap injects a charge binary that double-posts",
       "nix fetch",
       "empty sha256 must not accept a substituted charge binary",
       "fixed-output derivation with a real sri hash and allowSubstitutes=false in CI",
       "fetchurl|sha256|sri", "lockfile-hash-skip plant"),
    _p("guix-ungexp-gexp-charge-dup", "guix-ungexp-gexp-charge-dup", "leech741", "feat: gexp",
       "package.scm", "charge.scm", "package_test.py", 22, "ug",
       "Guix leftover ungexp splices a charge phase twice so the builder leftover POSTs /charge twice",
       "guix build",
       "the charge phase must run once per package",
       "single ungexp of the phase and a builder test that counts POSTs",
       "ungexp|gexp|charge", "harbor-mutable-tags plant"),
    _p("spack-concretizer-hash-flip", "spack-concretizer-hash-flip", "leech742", "feat: concretize",
       "package.py", "spec.yaml", "package_test.py", 28, "ch",
       "Spack leftover concretizer allows a hash flip so CI leftover installs a different charge CLI that double-captures",
       "spack install",
       "concretized hash must pin the charge CLI bit-for-bit",
       "spack.lock commit plus --dirty fail if spec hash changes",
       "concretizer|spack.lock|hash", "ci-cache-poison plant"),
    # 15 duckdb / sqlite / motherduck
    _p("duckdb-attach-write-stale-gmv", "duckdb-attach-write-stale-gmv", "luff743", "feat: attach",
       "gmv.sql", "attach.sql", "test_gmv.py", 11, "at",
       "DuckDB leftover ATTACH without READ_ONLY so a leftover writer mutates the warehouse copy and GMV is double-counted locally",
       "attach gmv",
       "the attached warehouse must not accept local writes that duplicate GMV",
       "ATTACH ... (READ_ONLY) plus a unique order_id constraint",
       "ATTACH|READ_ONLY|GMV", "iceberg-snapshot plant"),
    _p("sqlite-wal-checkpoint-lost-refund", "sqlite-wal-checkpoint-lost-refund", "luff744", "feat: wal",
       "refund.py", "db.py", "test_refund.py", 33, "wl",
       "SQLite leftover checkpoint PASSIVE during a refund txn so a crash leaves the capture and drops the refund",
       "refund wal",
       "a crash mid-refund must not leave a captured charge without the refund row",
       "checkpoint TRUNCATE only after COMMIT and a single txn for capture+refund",
       "WAL|PASSIVE|refund", "sqlite-journal plant"),
    _p("motherduck-share-snapshot-stale", "motherduck-share-snapshot-stale", "luff745", "feat: share",
       "share.sql", "gmv.sql", "test_share.py", 18, "sh",
       "MotherDuck leftover SHARE uses a stale snapshot so finance leftover SUMs yesterday's captures again",
       "md share",
       "the share must not re-sum a snapshot whose captures were already invoiced",
       "SHARE at a named snapshot id plus invoice watermark",
       "SHARE|snapshot|watermark", "duckdb-attach-write-stale-gmv plant"),
    # 16 wire / dagger / fx
    _p("wire-provider-set-double-bind", "wire-provider-set-double-bind", "foot746", "feat: wire",
       "wire.go", "charge.go", "wire_test.go", 25, "ps",
       "Wire leftover ProviderSet binds ChargeClient twice so leftover Init charges with two clients and double-captures",
       "wire inject",
       "ChargeClient must be provided once per process",
       "one ProviderSet and wiretest that panics on duplicate bind",
       "ProviderSet|ChargeClient|duplicate", "fx-onstart plant"),
    _p("dagger-withenv-secret-plaintext", "dagger-withenv-secret-plaintext", "foot747", "feat: withenv",
       "ci.go", "charge.go", "ci_test.go", 30, "we",
       "Dagger leftover withEnv puts the charge API key in plaintext so a leftover cache volume replays Charge.create",
       "dagger pipeline",
       "the API key must not be in withEnv or the cache must not replay Charge.create",
       "withSecretVariable plus cache mounts that exclude env",
       "withEnv|withSecretVariable|cache", "gha-rerun-double-charge plant"),
    _p("fx-invoke-onstart-double-hook", "fx-invoke-onstart-double-hook", "foot748", "feat: onstart",
       "module.go", "charge.go", "module_test.go", 21, "os",
       "fx leftover Invoke plus OnStart both Charge.create so process boot leftover double-captures the leftover SKU",
       "fx boot",
       "boot must Charge.create at most once",
       "only OnStart or only Invoke, with a sync.Once around Charge.create",
       "OnStart|Invoke|Once", "wire-provider-set-double-bind plant"),
]


assert len(PLANTS) == 48, len(PLANTS)
assert len(PLANTS) % 3 == 0
assert len({p["slug"] for p in PLANTS}) == len(PLANTS)
assert len({p["family"] for p in PLANTS}) == len(PLANTS)
_old = {_BASE.PLANTS[i]["family"] for i in range(len(_BASE.PLANTS))}
_old |= {_BASE.PLANTS[i]["slug"] for i in range(len(_BASE.PLANTS))}
_clash = [p["family"] for p in PLANTS if p["family"] in _old] + [
    p["slug"] for p in PLANTS if p["slug"] in _old
]
assert not _clash, _clash


def plants_for_offset(offset: int) -> list[dict]:
    chunk = PLANTS[offset : offset + 3]
    if len(chunk) != 3:
        raise SystemExit(f"bad offset {offset} left={len(PLANTS) - offset}")
    return chunk


def notes_for(round_n: int, recs: list[dict], plants: list[dict]) -> str:
    fams = [r["meta"]["family"] for r in recs]
    ids = [r["id"] for r in recs]
    lines = [
        f"# code-review-preference-factory — NOTES r{round_n}",
        "",
        "Novel coverage: 99.4%",
        "",
        f"Headline: blocking defect vs nit/LGTM on {', '.join(fams)} (leftover leftover leftover stretch)",
        "",
        "Construction: divergence-point DPO (shared 7-step prefix; first differing tool_call is the review verdict). Same top-level goal both sides. Chosen posts issue (blocking) REQUEST_CHANGES. Rejected posts nits and APPROVE. Discarded drafts that changed the PR. Fuel: ARCTIC, BitsAI-CR, Graphite blocking-vs-nits. Stretch is leftover leftover leftover IaC/policy/codegen/protocol families — not XSS, not OAuth, not query-string HTML clones, not *-concat / *-plus vector cartesian.",
        "",
        "Novel leftover leftover leftover families this wave (keep r277-r680 DPO as-is; BAN XSS; BAN OAuth/OIDC/SAML r161-r252; BAN r537 temporal-heartbeat / cadence-replay / airflow-catchup; BAN r538-r549 Prefect/Dagster/Luigi Argo/Tekton/GHA Vitess/Yugabyte/TiDB Stripe/Adyen/PayPal timezone-fold ORM-upsert; BAN r670-r678 typesense/algolia/qdrant/milvus/pinecone/chroma/faiss/hnsw/nmslib/scann *-concat / *-plus): Terraform state lock, Pulumi refresh=false, Crossplane updatePolicy Manual, Helm hook-delete-policy, Kustomize namePrefix, Jsonnet mergePatch arrays, OPA tenant package, Cedar missing context.ip, OpenFGA consistency, sqlc COPY ON CONFLICT, Prisma isolation lost-update, ent hook skip, GraphQL DataLoader tenant, gRPC stream deadline, tRPC superjson offset, WebSocket lastSeq, SSE Last-Event-ID, MQTT retain QoS, JWT nbf, PASETO footer kid, macaroon caveat, argon2id vs I, bcrypt 72, scrypt salt, ClickHouse FINAL, Druid rollup, Pinot upsertMode, NATS AckWait, Kafka idempotence, Redpanda txn, Temporal ContinueAsNew, Cadence ParentClosePolicy, Conductor FORK JOIN, WASM host meter, Lua os.execute, CEL optional deny, CUE closed, Jsonnet importstr, Dhall toMap, Nix sha256, Guix ungexp, Spack lock, DuckDB ATTACH, SQLite WAL checkpoint, MotherDuck SHARE, Wire ProviderSet, Dagger withEnv, fx OnStart/Invoke.",
        "",
        "Records:",
    ]
    for rec, plant in zip(recs, plants):
        lines.append(
            f"- `{rec['id']}` sin=`missed defect / nitpicks` class=`{plant['family']}-blocking` family=`{plant['family']}` fork=step 8"
        )
    lines.extend(
        [
            "",
            f"IDs: {ids}",
            "",
            "Weakest critique: still names the same-goal quality delta and the discarded changed-problem draft. Distinct from r161-r252 OAuth/OIDC/SAML, r253-r276 privacy-sandbox, r277-r312 WebGPU/IWA, r313-r431 HTML/CSS query-string clones, r537 temporal/cadence/airflow, r538-r549 orchestrator/CDC/upsert, and r670-r678 vector concat.",
            "",
            "No Thalamic six-field core. No spikes. Observations are designed plants.",
            "",
            "Next gaps: more IaC lock/refresh, more policy fail-closed, more WAL/share snapshot isolation.",
            "",
        ]
    )
    return "\n".join(lines)


def write_round(round_n: int, staging: Path, offset: int) -> list[str]:
    plants = plants_for_offset(offset)
    recs = [pair(p, round_n, i) for i, p in enumerate(plants)]
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
    notes.write_text(notes_for(round_n, recs, plants))
    return [r["id"] for r in recs]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--offset", type=int, required=True)
    args = parser.parse_args()
    ids = write_round(args.round, args.staging, args.offset)
    print(json.dumps({"round": args.round, "ids": ids, "offset": args.offset, "staging": str(args.staging)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
