#!/usr/bin/env python3
"""Code-family plant catalog: prior leftover3 wave indexed by the code mill.

``plants_from_source`` walks a mill module for ``P(...)`` / ``_p(...)``
calls. ``notfam_slugs_from_source`` is the experiments/code* extract
seam: every ``P().notfam`` on
``experiments/code_review_preference_mill_leftover3.py`` names one
prior leftover3 slug. Full rows are AST-extracted from
``experiments/crp-mill-leftover3.py`` on ``legacy-mill-lane`` and
ordered to match that notfam index. Mill files are not vendored.

The third leftover leftover leftover wave from the code mill is already
in ``pipelines/crp`` (``crp-leftover3-v1``, r729-r744) and is refused
here as a covered slug set.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ._contract import (
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_TRIPLE_STRIDE,
    FINDING_COVERED_SLUG,
    FINDING_DUPLICATE_FAMILY,
    FINDING_DUPLICATE_SLUG,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_NOTFAM_DRIFT,
    FINDING_NOUN_MISSING,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_TRIPLE_OUT_OF_DOMAIN,
    bind_import_twin,
    refuse,
    refuse_first,
    refuse_when,
    shown,
)

CATALOG_ID = "code-leftover3-prior-v1"
FACTORY = "code-review-preference-factory"
GENERATOR = "grok-4.6"
ID_PREFIX = "crp"
WAVE_FIRST_ROUND = 679
PLANTS_PER_ROUND = 3
PAIR_FIRST_ROUND = 432
SOURCE_CODE_MILL = "experiments/code_review_preference_mill_leftover3.py"
SOURCE_LEFTOVER3_MILL = "experiments/crp-mill-leftover3.py"
SOURCE_REF = "origin/legacy-mill-lane"
SOURCE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"

PLANT_FIELDS = (
    "family", "slug", "noun", "title", "core", "boot", "test", "line", "nit",
    "defect", "reach", "missing", "fix", "needles", "notfam",
)
CALL_NAMES = frozenset({"P", "_p"})

# Slugs the code mill names in P().notfam order (strip trailing " plant").
CODE_MILL_NOTFAM = (
    "terraform-statelock-skip-apply",
    "pulumi-refresh-false-recreate",
    "crossplane-updatepolicy-manual-claim",
    "helm-hook-delete-before-missing",
    "kustomize-nameprefix-omit-overlay",
    "jsonnet-mergepatch-array-concat",
    "opa-input-user-package-leak",
    "cedar-context-ip-permit-all",
    "openfga-write-without-consistency",
    "graphql-dataloader-tenant-cache",
    "grpc-stream-no-deadline-retry",
    "trpc-superjson-date-utc-shift",
    "clickhouse-replacing-no-final",
    "druid-rollup-double-count",
    "pinot-upsert-mode-none-dup",
    "nats-js-ackwait-redeliver-charge",
    "kafka-idempotence-false-dup",
    "redpanda-txn-id-missing-abort",
    "cue-closed-struct-extra-sku",
    "dhall-tomap-type-hole-price",
    "jsonnet-importstr-secret-double",
    "nix-fetchurl-sha256-empty",
    "guix-ungexp-gexp-charge-dup",
    "spack-concretizer-hash-flip",
    "duckdb-attach-write-stale-gmv",
    "sqlite-wal-checkpoint-lost-refund",
    "motherduck-share-snapshot-stale",
    "wasm-host-call-unmetered-charge",
    "lua-sandbox-os-execute-charge",
    "cel-optional-shortcircuit-skip-deny",
    "jwt-nbf-unverified-early",
    "paseto-footer-unbound-keyid",
    "macaroon-caveat-unverified-sku",
    "argon2-type-i-not-id",
    "bcrypt-72-byte-truncate",
    "scrypt-n-small-salt-reuse",
    "temporal-continueasnew-side-effect",
    "cadence-parent-close-abandon-child",
    "conductor-fork-join-timeout-retry",
    "wire-provider-set-double-bind",
    "dagger-withenv-secret-plaintext",
    "fx-invoke-onstart-double-hook",
    "sqlc-copyfrom-no-conflict",
    "prisma-interactive-txn-lost-update",
    "ent-hook-skip-mutators-serial",
    "websocket-resume-seq-skip",
    "sse-last-event-id-ignored",
    "mqtt-qos0-retained-stale-price",
)

# Third leftover leftover leftover slugs already landed in pipelines/crp.
CRP_LEFTOVER3_SLUGS = frozenset({
    "terraform-target-orphan-sku",
    "pulumi-ignorechanges-drop-protect",
    "tofu-moved-block-skip-state",
    "helm-atomic-false-hook-orphan",
    "kustomize-replacements-omit-ns",
    "tanka-apply-prune-false-orphan",
    "opa-else-true-default-allow",
    "cedar-unless-clause-dropped",
    "spicedb-zedtoken-minimize-stale",
    "graphql-alias-cost-bypass",
    "grpc-retry-pushback-ignored",
    "connect-timeout-interceptor-drop",
    "clickhouse-ttl-move-lost-refund",
    "druid-keepsegment-miss-overlap",
    "starrocks-partial-update-dup-pk",
    "nats-kv-history-zero-lost-ack",
    "kafka-autooffset-latest-skip-refund",
    "pulsar-acktimeout-redeliver-charge",
    "cue-list-open-extra-sku",
    "dhall-aslocation-unsigned-import",
    "nickel-merge-priority-force-price",
    "nix-flakelock-narhash-omit",
    "guix-inferior-ungraft-charge",
    "portage-accept-keywords-live-ebuild",
    "duckdb-copy-overwrite-no-txn",
    "sqlite-shared-cache-writer-lost",
    "turso-embedded-replica-stale-gmv",
    "wasm-wasi-clock-unbounded-loop",
    "lua-setfenv-restore-miss",
    "extism-host-fn-reentry-charge",
    "jwt-typ-none-confused-verify",
    "paseto-purpose-local-as-public",
    "branca-ttl-unverified-early",
    "argon2-ad-omit-context",
    "bcrypt-cost-four-offline",
    "yescrypt-flags-default-weak",
    "temporal-signal-buffer-drop-refund",
    "cadence-sticky-cache-stale-decision",
    "restate-journal-skip-replay-charge",
    "wire-cleanup-unbind-midflight",
    "dagger-export-cache-replay-charge",
    "fx-decorate-order-flip-hook",
    "sqlc-batchexec-ignore-rows",
    "prisma-middleware-skip-softdelete",
    "drizzle-idle-txn-lost-update",
    "websocket-ping-interval-zero",
    "sse-retry-field-omitted",
    "webtransport-datagram-unreliable-charge",
})

__all__ = [
    "CATALOG_ID", "CODE_MILL_NOTFAM", "CRP_LEFTOVER3_SLUGS", "FACTORY",
    "GENERATOR", "ID_PREFIX", "PAIR_FIRST_ROUND", "PLANT_FIELDS",
    "PLANTS_PER_ROUND", "SOURCE_CODE_MILL", "SOURCE_COMMIT",
    "SOURCE_LEFTOVER3_MILL", "SOURCE_REF", "WAVE_FIRST_ROUND", "Catalog",
    "Plant", "catalog_check", "load_catalog", "notfam_slugs_from_source",
    "plant_from_mapping", "plants_for_round", "plants_from_source",
]


@dataclass(frozen=True)
class Plant:
    """One AST-extracted prior leftover3 plant. ``noun`` is required."""

    family: str
    slug: str
    noun: str
    title: str
    core: str
    boot: str
    test: str
    line: int
    nit: str
    defect: str
    reach: str
    missing: str
    fix: str
    needles: str
    notfam: str

    @property
    def repo(self) -> str:
        return f"plant/{self.noun}-{self.slug}"

    def as_mapping(self) -> dict[str, Any]:
        payload = {field: getattr(self, field) for field in PLANT_FIELDS}
        payload["repo"] = self.repo
        return payload


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    plants: tuple[Plant, ...]

    def plant(self, slug: str) -> Plant:
        for item in self.plants:
            if item.slug == slug:
                return item
        refuse(FINDING_FIELD_INVALID, f"no plant {shown(slug)} in the catalog")


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError) as exc:
        refuse(FINDING_AST_NOT_A_PLANT, f"P() argument is not a literal: {exc}")


def _call_values(node: ast.Call) -> dict[str, Any] | None:
    """Literal ``P`` / ``_p`` kwargs, or None for wrappers such as ``_p(*args)``."""

    if any(isinstance(arg, ast.Starred) for arg in node.args):
        return None
    if any(keyword.arg is None for keyword in node.keywords):
        return None
    values: dict[str, Any] = {}
    for index, arg in enumerate(node.args):
        if index >= len(PLANT_FIELDS):
            refuse(FINDING_AST_NOT_A_PLANT, "P() has extra positional arguments")
        values[PLANT_FIELDS[index]] = _literal(arg)
    for keyword in node.keywords:
        values[keyword.arg] = _literal(keyword.value)
    return values


def _require_plant_fields(values: Mapping[str, Any], where: str) -> dict[str, Any]:
    missing = [field for field in PLANT_FIELDS if field not in values]
    refuse_when(bool(missing), FINDING_FIELD_MISSING, f"{where} missing {missing}")
    noun = values["noun"]
    refuse_when(
        not isinstance(noun, str) or not noun,
        FINDING_NOUN_MISSING,
        f"{where} noun must be a non-empty string, got {shown(noun)}",
    )
    line = values["line"]
    refuse_when(
        type(line) is not int,
        FINDING_FIELD_INVALID,
        f"{where}.line must be an int, got {shown(line)}",
    )
    checked = {}
    for field in PLANT_FIELDS:
        value = values[field]
        if field == "line":
            checked[field] = value
            continue
        refuse_when(
            not isinstance(value, str) or not value,
            FINDING_FIELD_INVALID,
            f"{where}.{field} must be a non-empty string, got {shown(value)}",
        )
        checked[field] = value
    return checked


def plant_from_mapping(values: Mapping[str, Any], where: str = "plant") -> Plant:
    """Validate one mapping (AST row or JSON) into a frozen plant with noun."""

    return Plant(**_require_plant_fields(values, where))


def plants_from_source(text: str) -> tuple[Plant, ...]:
    """AST-extract ``P`` / ``_p`` catalog rows, requiring ``noun`` on each."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_AST_NOT_A_PLANT, f"mill source is not parseable: {exc}")
    ordered: list[Plant] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            if isinstance(func, ast.Name) and func.id in CALL_NAMES:
                values = _call_values(node)
                if values:
                    ordered.append(
                        plant_from_mapping(values, f"P() at line {node.lineno}")
                    )
            self.generic_visit(node)

    Visitor().visit(tree)
    return tuple(ordered)


def notfam_slugs_from_source(text: str) -> tuple[str, ...]:
    """AST-extract ``P().notfam`` slugs (strip a trailing `` plant``)."""

    return tuple(
        plant.notfam.removesuffix(" plant") for plant in plants_from_source(text)
    )


def _check_unique(plants: tuple[Plant, ...]) -> None:
    slugs: dict[str, str] = {}
    families: dict[str, str] = {}
    for plant in plants:
        if plant.slug in slugs:
            refuse(
                FINDING_DUPLICATE_SLUG,
                f"slug {shown(plant.slug)} repeats ({slugs[plant.slug]} and {plant.family})",
            )
        slugs[plant.slug] = plant.family
        if plant.family in families:
            refuse(
                FINDING_DUPLICATE_FAMILY,
                f"family {shown(plant.family)} repeats",
            )
        families[plant.family] = plant.slug


def _reject_covered(plants: tuple[Plant, ...]) -> None:
    overlap = [plant.slug for plant in plants if plant.slug in CRP_LEFTOVER3_SLUGS]
    refuse_when(
        bool(overlap),
        FINDING_COVERED_SLUG,
        f"slug already in pipelines/crp leftover3: {overlap[:3]}",
    )


def catalog_check(plants: tuple[Plant, ...] | None = None) -> dict[str, Any]:
    """Fail closed unless every row has noun, unique identity, and the notfam index."""

    items = load_catalog().plants if plants is None else plants
    refuse_when(not items, FINDING_CATALOG_EMPTY, "catalog has no plants")
    refuse_when(
        len(items) % PLANTS_PER_ROUND != 0,
        FINDING_CATALOG_TRIPLE_STRIDE,
        f"catalog length {len(items)} is not a multiple of {PLANTS_PER_ROUND}",
    )
    _check_unique(items)
    _reject_covered(items)
    slugs = tuple(plant.slug for plant in items)
    refuse_when(
        slugs != CODE_MILL_NOTFAM,
        FINDING_NOTFAM_DRIFT,
        "committed slugs drifted from the code mill notfam index",
    )
    for plant in items:
        refuse_when(not plant.noun, FINDING_NOUN_MISSING, f"{plant.slug} is missing noun")
        refuse_when(
            plant.repo != f"plant/{plant.noun}-{plant.slug}",
            FINDING_FIELD_INVALID,
            f"{plant.slug} repo drifted from noun",
        )
    return {
        "status": "ok",
        "catalog_id": CATALOG_ID,
        "plants": len(items),
        "triples": len(items) // PLANTS_PER_ROUND,
        "nouns": len({plant.noun for plant in items}),
        "first_round": WAVE_FIRST_ROUND,
        "last_round": WAVE_FIRST_ROUND + len(items) // PLANTS_PER_ROUND - 1,
        "source_code_mill": SOURCE_CODE_MILL,
        "source_leftover3_mill": SOURCE_LEFTOVER3_MILL,
    }


def plants_for_round(round_n: int, plants: tuple[Plant, ...] | None = None) -> tuple[Plant, ...]:
    items = load_catalog().plants if plants is None else plants
    last = WAVE_FIRST_ROUND + len(items) // PLANTS_PER_ROUND - 1
    refuse_first((
        (type(round_n) is not int, FINDING_ROUND_OUT_OF_DOMAIN,
         f"round must be an int, got {shown(round_n)}"),
        (type(round_n) is int and not WAVE_FIRST_ROUND <= round_n <= last,
         FINDING_ROUND_OUT_OF_DOMAIN,
         f"round must lie in [{WAVE_FIRST_ROUND}, {last}], got {shown(round_n)}"),
    ))
    start = (round_n - WAVE_FIRST_ROUND) * PLANTS_PER_ROUND
    chunk = items[start:start + PLANTS_PER_ROUND]
    refuse_when(
        len(chunk) != PLANTS_PER_ROUND,
        FINDING_TRIPLE_OUT_OF_DOMAIN,
        f"no plant triple for r{round_n}",
    )
    return chunk


# AST-extracted prior leftover3 rows, ordered by the code mill notfam index.
# Field order is PLANT_FIELDS; noun is index 2.
_EXTRACTED_ROWS: tuple[tuple[Any, ...], ...] = (
    (
        'terraform-statelock-skip-apply',
        'terraform-statelock-skip-apply',
        'keel701',
        'feat: apply',
        'main.tf',
        'sku.tf',
        'test_apply.py',
        41,
        'lk',
        'terraform apply -lock=false on leftover state so two CIs provision the same billing SKU twice',
        'sku workspace apply',
        'two concurrent applies must not create a second Chargeable sku resource',
        'require -lock=true and a remote backend lock; fail if lock is skipped',
        'lock=false|statelock|sku',
        'prefect-retries-zero-charge plant',
    ),
    (
        'pulumi-refresh-false-recreate',
        'pulumi-refresh-false-recreate',
        'keel702',
        'feat: up',
        'index.ts',
        'rds.ts',
        'index.test.ts',
        28,
        'rf',
        'pulumi up --refresh=false leaves leftover stack outputs stale so the next up recreates RDS and double-bills',
        'nightly stack up',
        'stale outputs must not recreate an already-provisioned RDS instance',
        'refresh before replace plus protect on the RDS URN',
        'refresh=false|replace|RDS',
        'dagster-run-overlap-invoice plant',
    ),
    (
        'crossplane-updatepolicy-manual-claim',
        'crossplane-updatepolicy-manual-claim',
        'keel703',
        'feat: claim',
        'composition.yaml',
        'claim.yaml',
        'claim_test.go',
        33,
        'up',
        'Composition updatePolicy=Manual so a leftover Claim still points at a deleted Composite and Crossplane provisions a second billed cluster',
        'cluster claim',
        'deleting the Composite must not leave a Claim that recreates a second billed cluster',
        'updatePolicy=Automatic plus orphan:false and a unique claim name lock',
        'updatePolicy|Manual|Claim',
        'luigi-complete-before-write plant',
    ),
    (
        'helm-hook-delete-before-missing',
        'helm-hook-delete-before-missing',
        'spar704',
        'feat: hook',
        'hooks.yaml',
        'charge.yaml',
        'hook_test.go',
        19,
        'hk',
        'pre-install Job lacks hook-delete-policy before-hook-creation so a leftover Job reruns and double-charges',
        'release hook',
        'a leftover hook Job must not Charge.create a second time on upgrade',
        'hook-delete-policy: before-hook-creation and an Idempotency-Key on the Job name',
        'hook-delete-policy|before-hook-creation|Job',
        'argo-retry-double-charge plant',
    ),
    (
        'kustomize-nameprefix-omit-overlay',
        'kustomize-nameprefix-omit-overlay',
        'spar705',
        'feat: overlay',
        'kustomization.yaml',
        'patch.yaml',
        'kustomize_test.go',
        12,
        'np',
        'prod overlay omits namePrefix so leftover patches hit the staging Deployment and prod traffic charges staging SKUs',
        'overlay apply',
        'prod patches must not mutate the staging Deployment name',
        'namePrefix: prod- plus a kustomize build test that asserts distinct names',
        'namePrefix|overlay|Deployment',
        'tekton-finally-skip-refund plant',
    ),
    (
        'jsonnet-mergepatch-array-concat',
        'jsonnet-mergepatch-array-concat',
        'spar706',
        'feat: merge',
        'job.jsonnet',
        'charge.jsonnet',
        'jsonnet_test.py',
        22,
        'mp',
        'std.mergePatch leftover concatenates containers[] so two charge sidecars run and both POST /charge',
        'jsonnet render',
        'merge must replace the charge container list not concatenate a second sidecar',
        'std.mergePatch with explicit containers replace or std.mapWithKey overwrite',
        'mergePatch|containers|concat',
        'gha-rerun-double-charge plant',
    ),
    (
        'opa-input-user-package-leak',
        'opa-input-user-package-leak',
        'boom707',
        'feat: allow',
        'authz.rego',
        'charge.rego',
        'authz_test.rego',
        47,
        'pk',
        'package authz leftover reads input.user without tenant isolation so deny is skipped and any tenant charges any SKU',
        'rego allow',
        'allow must be false when input.tenant != resource.tenant',
        'deny by default plus input.tenant == resource.tenant in allow',
        'package|input.user|tenant',
        'oauth-scope-clone plant',
    ),
    (
        'cedar-context-ip-permit-all',
        'cedar-context-ip-permit-all',
        'boom708',
        'feat: permit',
        'policy.cedar',
        'charge.cedar',
        'cedar_test.py',
        16,
        'ip',
        'Cedar permit leftover omits context.ip so when.isInRange is vacuously true and every caller may Charge.create',
        'cedar eval',
        'permit must fail closed when context.ip is absent',
        'require context.ip and when { context.ip.isInRange(office) }; forbid if missing',
        'context.ip|permit|isInRange',
        'saml-clone plant',
    ),
    (
        'openfga-write-without-consistency',
        'openfga-write-without-consistency',
        'boom709',
        'feat: check',
        'store.go',
        'check.go',
        'store_test.go',
        38,
        'cs',
        'OpenFGA Write leftover then Check without HIGHER_CONSISTENCY so a just-deleted tuple still allows the charge',
        'tuple check',
        'Check after delete must not allow the same SKU charge',
        'ConsistencyPreference HIGHER_CONSISTENCY on Check after Write/Delete',
        'HIGHER_CONSISTENCY|Write|Check',
        'oidc-clone plant',
    ),
    (
        'graphql-dataloader-tenant-cache',
        'graphql-dataloader-tenant-cache',
        'vang713',
        'feat: loader',
        'loader.ts',
        'sku.ts',
        'loader.test.ts',
        18,
        'dl',
        "DataLoader leftover caches SKU by id across tenants so tenant B is billed tenant A's price",
        'gql sku',
        'loader keys must be tenant-scoped or cache must not leak prices across tenants',
        'cacheKeyFn: (id, tenant) and a new DataLoader per request',
        'DataLoader|cacheKeyFn|tenant',
        'gql-nplusone-no-loader plant',
    ),
    (
        'grpc-stream-no-deadline-retry',
        'grpc-stream-no-deadline-retry',
        'vang714',
        'feat: stream',
        'charge.proto',
        'client.go',
        'client_test.go',
        44,
        'dl',
        'gRPC client stream leftover has no deadline so a retry after a hang double-sends ChargeCreate',
        'stream charge',
        'a hung stream retry must not emit a second ChargeCreate',
        'context.WithTimeout plus idempotency metadata on ChargeCreate',
        'deadline|stream|ChargeCreate',
        'kafka-txn-abort-ignored plant',
    ),
    (
        'trpc-superjson-date-utc-shift',
        'trpc-superjson-date-utc-shift',
        'vang715',
        'feat: superjson',
        'router.ts',
        'slot.ts',
        'router.test.ts',
        21,
        'dt',
        'tRPC superjson leftover deserializes a fold-night ISO as UTC so the appointment is stored an hour late and double-booked',
        'slot book',
        'fold-night ISO must round-trip in the original offset not as naive UTC',
        'transformer that preserves offset or store instants as epoch ms',
        'superjson|ISO|offset',
        'luxon-fold plant',
    ),
    (
        'clickhouse-replacing-no-final',
        'clickhouse-replacing-no-final',
        'clew725',
        'feat: replacing',
        'gmv.sql',
        'query.sql',
        'test_gmv.sql',
        9,
        'fn',
        'ReplacingMergeTree leftover query omits FINAL so duplicate version rows SUM into GMV and finance double-collects',
        'gmv query',
        'SUM must not count superseded versions of the same order_id',
        'SELECT ... FINAL or argMax(amount, ver) GROUP BY order_id',
        'ReplacingMergeTree|FINAL|argMax',
        'spark-watermark-late-charge plant',
    ),
    (
        'druid-rollup-double-count',
        'druid-rollup-double-count',
        'clew726',
        'feat: rollup',
        'spec.json',
        'query.json',
        'spec_test.py',
        23,
        'rl',
        'Druid leftover ingestion rollup=true with metric leftover count plus query SUM(count) double-counts the same charge event',
        'druid ingest',
        'query must not SUM an already-rolled-up count into a second billed total',
        'query the rollup metric without a second SUM or disable query-time re-aggregation',
        'rollup|SUM(count)|charge',
        'beam-allowedlateness-zero-late plant',
    ),
    (
        'pinot-upsert-mode-none-dup',
        'pinot-upsert-mode-none-dup',
        'clew727',
        'feat: upsert',
        'table.json',
        'charge.sql',
        'table_test.py',
        26,
        'up',
        'Pinot leftover upsertMode NONE so a replayed charge event appends a second row and GMV doubles',
        'pinot table',
        'replayed primary keys must replace not append',
        'upsertMode FULL plus primaryKeyColumns charge_id',
        'upsertMode|NONE|primaryKey',
        'pinot-clone plant',
    ),
    (
        'nats-js-ackwait-redeliver-charge',
        'nats-js-ackwait-redeliver-charge',
        'reef728',
        'feat: ackwait',
        'js.go',
        'charge.go',
        'js_test.go',
        39,
        'aw',
        'NATS JetStream leftover AckWait shorter than Stripe RTT so the message is redelivered and Charge.create runs twice',
        'js consumer',
        'AckWait must outlast the Stripe call or the handler must be idempotent on charge_id',
        'AckWait >= 30s plus Idempotency-Key = msg.Nats-Msg-Id',
        'AckWait|redeliver|Charge.create',
        'nats-ack plant',
    ),
    (
        'kafka-idempotence-false-dup',
        'kafka-idempotence-false-dup',
        'reef729',
        'feat: producer',
        'producer.properties',
        'charge.go',
        'producer_test.go',
        8,
        'id',
        'Kafka producer leftover enable.idempotence=false so a retry after acks=all timeout publishes a second charge record',
        'charge topic',
        'producer retry must not append a second record for the same charge_id',
        'enable.idempotence=true transactional.id and a compact key=charge_id',
        'enable.idempotence|transactional.id|charge_id',
        'kafka-txn-abort-ignored plant',
    ),
    (
        'redpanda-txn-id-missing-abort',
        'redpanda-txn-id-missing-abort',
        'reef730',
        'feat: txn',
        'txn.go',
        'charge.go',
        'txn_test.go',
        42,
        'tx',
        'Redpanda leftover producer has no transactional.id so an aborted txn still appears to consumers and a charge is captured',
        'txn produce',
        'aborted transactions must not be visible as captured charges',
        'transactional.id plus isolation.level=read_committed on the consumer',
        'transactional.id|read_committed|abort',
        'kafka-connect plant',
    ),
    (
        'cue-closed-struct-extra-sku',
        'cue-closed-struct-extra-sku',
        'batten737',
        'feat: closed',
        'sku.cue',
        'price.cue',
        'sku_test.go',
        10,
        'cl',
        'CUE leftover definition is open so an extra sku field leftover is accepted and a hidden SKU is billed',
        'cue eval',
        'unknown sku fields must be rejected',
        'close({sku: string, cents: int}) and cue vet in CI',
        'close(|sku|vet',
        'jsonnet-mergepatch-array-concat plant',
    ),
    (
        'dhall-tomap-type-hole-price',
        'dhall-tomap-type-hole-price',
        'batten739',
        'feat: tomap',
        'price.dhall',
        'sku.dhall',
        'price_test.py',
        16,
        'tm',
        'Dhall leftover toMap with a type hole leftover infers Text so cents become a leftover string and the parser bills 100x',
        'dhall price',
        'cents must stay Natural not Text or the billed amount must not jump 100x',
        'toMap with an explicit { mapKey : Text, mapValue : Natural }',
        'toMap|Natural|cents',
        'kustomize-nameprefix-omit-overlay plant',
    ),
    (
        'jsonnet-importstr-secret-double',
        'jsonnet-importstr-secret-double',
        'batten738',
        'feat: importstr',
        'secret.jsonnet',
        'charge.jsonnet',
        'secret_test.py',
        7,
        'is',
        'Jsonnet leftover importstr of a charge API key concatenates two keys so the second leftover key captures a second charge',
        'jsonnet secret',
        'importstr must not concatenate a second API key into Charge.create',
        'single-key secret plus std.manifestJsonMinified without concat',
        'importstr|api key|concat',
        'helm-hook-delete-before-missing plant',
    ),
    (
        'nix-fetchurl-sha256-empty',
        'nix-fetchurl-sha256-empty',
        'leech740',
        'feat: fetchurl',
        'default.nix',
        'sku.nix',
        'fetch_test.py',
        19,
        'sh',
        'nix leftover fetchurl sha256 = "" so a leftover tarball swap injects a charge binary that double-posts',
        'nix fetch',
        'empty sha256 must not accept a substituted charge binary',
        'fixed-output derivation with a real sri hash and allowSubstitutes=false in CI',
        'fetchurl|sha256|sri',
        'lockfile-hash-skip plant',
    ),
    (
        'guix-ungexp-gexp-charge-dup',
        'guix-ungexp-gexp-charge-dup',
        'leech741',
        'feat: gexp',
        'package.scm',
        'charge.scm',
        'package_test.py',
        22,
        'ug',
        'Guix leftover ungexp splices a charge phase twice so the builder leftover POSTs /charge twice',
        'guix build',
        'the charge phase must run once per package',
        'single ungexp of the phase and a builder test that counts POSTs',
        'ungexp|gexp|charge',
        'harbor-mutable-tags plant',
    ),
    (
        'spack-concretizer-hash-flip',
        'spack-concretizer-hash-flip',
        'leech742',
        'feat: concretize',
        'package.py',
        'spec.yaml',
        'package_test.py',
        28,
        'ch',
        'Spack leftover concretizer allows a hash flip so CI leftover installs a different charge CLI that double-captures',
        'spack install',
        'concretized hash must pin the charge CLI bit-for-bit',
        'spack.lock commit plus --dirty fail if spec hash changes',
        'concretizer|spack.lock|hash',
        'ci-cache-poison plant',
    ),
    (
        'duckdb-attach-write-stale-gmv',
        'duckdb-attach-write-stale-gmv',
        'luff743',
        'feat: attach',
        'gmv.sql',
        'attach.sql',
        'test_gmv.py',
        11,
        'at',
        'DuckDB leftover ATTACH without READ_ONLY so a leftover writer mutates the warehouse copy and GMV is double-counted locally',
        'attach gmv',
        'the attached warehouse must not accept local writes that duplicate GMV',
        'ATTACH ... (READ_ONLY) plus a unique order_id constraint',
        'ATTACH|READ_ONLY|GMV',
        'iceberg-snapshot plant',
    ),
    (
        'sqlite-wal-checkpoint-lost-refund',
        'sqlite-wal-checkpoint-lost-refund',
        'luff744',
        'feat: wal',
        'refund.py',
        'db.py',
        'test_refund.py',
        33,
        'wl',
        'SQLite leftover checkpoint PASSIVE during a refund txn so a crash leaves the capture and drops the refund',
        'refund wal',
        'a crash mid-refund must not leave a captured charge without the refund row',
        'checkpoint TRUNCATE only after COMMIT and a single txn for capture+refund',
        'WAL|PASSIVE|refund',
        'sqlite-journal plant',
    ),
    (
        'motherduck-share-snapshot-stale',
        'motherduck-share-snapshot-stale',
        'luff745',
        'feat: share',
        'share.sql',
        'gmv.sql',
        'test_share.py',
        18,
        'sh',
        "MotherDuck leftover SHARE uses a stale snapshot so finance leftover SUMs yesterday's captures again",
        'md share',
        'the share must not re-sum a snapshot whose captures were already invoiced',
        'SHARE at a named snapshot id plus invoice watermark',
        'SHARE|snapshot|watermark',
        'duckdb-attach-write-stale-gmv plant',
    ),
    (
        'wasm-host-call-unmetered-charge',
        'wasm-host-call-unmetered-charge',
        'cringle734',
        'feat: host',
        'host.go',
        'charge.go',
        'host_test.go',
        37,
        'hc',
        'WASM leftover host import Charge.create is unmetered so a guest loop leftover double-charges until timeout',
        'wasm guest',
        'guest must not call Charge.create more than once per invoice_id',
        'host-side idempotency map plus fuel/meter on the import',
        'host|Charge.create|fuel',
        'webgpu-clone plant',
    ),
    (
        'lua-sandbox-os-execute-charge',
        'lua-sandbox-os-execute-charge',
        'cringle735',
        'feat: sandbox',
        'sandbox.lua',
        'charge.lua',
        'sandbox_test.py',
        20,
        'os',
        'Lua leftover sandbox still exposes os.execute so a template leftover shells curl to Charge.create twice',
        'lua template',
        'sandboxed Lua must not os.execute a second charge',
        'nil os.execute and a host-only charge API with idempotency',
        'os.execute|sandbox|Charge',
        'webnn-clone plant',
    ),
    (
        'cel-optional-shortcircuit-skip-deny',
        'cel-optional-shortcircuit-skip-deny',
        'cringle736',
        'feat: cel',
        'policy.cel',
        'charge.cel',
        'policy_test.go',
        13,
        'sc',
        'CEL leftover optional.?user.banned short-circuits to null which is truthy-not-false so deny is skipped and a banned user charges',
        'cel allow',
        'missing banned must fail closed not skip deny',
        'has(user.banned) && user.banned == true as deny; default false allow',
        'optional|short-circuit|banned',
        'opa-input-user-package-leak plant',
    ),
    (
        'jwt-nbf-unverified-early',
        'jwt-nbf-unverified-early',
        'shroud719',
        'feat: nbf',
        'jwt.go',
        'charge.go',
        'jwt_test.go',
        52,
        'nb',
        'JWT Verify leftover skips nbf so a not-before token is accepted early and a pre-sale charge captures',
        'jwt charge',
        'tokens with nbf in the future must not authorize Charge.create',
        'require nbf claim and reject now < nbf - leeway',
        'nbf|Verify|Charge',
        'oauth-jwt-clone plant',
    ),
    (
        'paseto-footer-unbound-keyid',
        'paseto-footer-unbound-keyid',
        'shroud720',
        'feat: footer',
        'paseto.py',
        'keys.py',
        'test_paseto.py',
        18,
        'ft',
        'PASETO v4 leftover treats footer kid as advisory so an attacker swaps kid and the old key still decrypts a charge grant',
        'paseto grant',
        'footer kid must bind to the key that verified the payload',
        'parse footer first, select key, verify, then reject if footer.kid != key.id',
        'footer|kid|v4',
        'oidc-clone plant',
    ),
    (
        'macaroon-caveat-unverified-sku',
        'macaroon-caveat-unverified-sku',
        'shroud721',
        'feat: caveat',
        'macaroon.go',
        'sku.go',
        'macaroon_test.go',
        34,
        'cv',
        'macaroon leftover verifies signature but skips first-party sku= caveat so a token minted for SKU-A charges SKU-B',
        'macaroon sku',
        'discharge must fail when the sku caveat does not match the charged SKU',
        'walk caveats and require sku==request.sku before capture',
        'caveat|sku=|signature',
        'saml-clone plant',
    ),
    (
        'argon2-type-i-not-id',
        'argon2-type-i-not-id',
        'tack722',
        'feat: hash',
        'hash.go',
        'passwd.go',
        'hash_test.go',
        11,
        'ty',
        'argon2 leftover uses Type I so a side-channel on leftover password verify lets an attacker mint a matching hash for support login',
        'password hash',
        'Type I must not be used for password hashing on the support login path',
        'argon2id with time>=2 memory>=64MiB and unique salt per row',
        'argon2id|Type I|salt',
        'password-plain plant',
    ),
    (
        'bcrypt-72-byte-truncate',
        'bcrypt-72-byte-truncate',
        'tack723',
        'feat: bcrypt',
        'hash.py',
        'passwd.py',
        'test_hash.py',
        14,
        'tr',
        'bcrypt leftover hashes only the first 72 bytes so two distinct long secrets collide and a leftover suffix unlocks the cashier',
        'bcrypt hash',
        'secrets longer than 72 bytes must not collide on the cashier login',
        'pre-hash with SHA-256 then bcrypt, or reject length>72',
        'bcrypt|72|prehash',
        'password-plain plant',
    ),
    (
        'scrypt-n-small-salt-reuse',
        'scrypt-n-small-salt-reuse',
        'tack724',
        'feat: scrypt',
        'kdf.go',
        'passwd.go',
        'kdf_test.go',
        17,
        'n',
        'scrypt leftover uses N=2^10 and a global salt so two cashiers share a derived key and one leftover password opens both wallets',
        'scrypt kdf',
        'each wallet must have a unique salt and N large enough to resist offline guess',
        'per-row salt plus N>=2^15 r=8 p=1',
        'scrypt|N=|salt',
        'password-plain plant',
    ),
    (
        'temporal-continueasnew-side-effect',
        'temporal-continueasnew-side-effect',
        'hank731',
        'feat: can',
        'workflow.go',
        'charge.go',
        'workflow_test.go',
        55,
        'cn',
        'Temporal leftover ContinueAsNew runs Charge.create in the workflow function so the new run repeats the side effect',
        'long workflow',
        'ContinueAsNew must not Charge.create a SKU already charged in the parent run',
        'move Charge.create to an activity with idempotency keyed by workflow.ID',
        'ContinueAsNew|Charge.create|activity',
        'temporal-heartbeat-timeout-double plant',
    ),
    (
        'cadence-parent-close-abandon-child',
        'cadence-parent-close-abandon-child',
        'hank732',
        'feat: child',
        'parent.go',
        'child.go',
        'parent_test.go',
        48,
        'pc',
        'Cadence leftover ParentClosePolicy ABANDON so a cancelled parent leaves a child that still Charge.create after refund',
        'child workflow',
        'cancelling the parent must not leave a child that charges after refund',
        'ParentClosePolicy TERMINATE plus a refund compensation on cancel',
        'ParentClosePolicy|ABANDON|TERMINATE',
        'cadence-replay-nondet-now plant',
    ),
    (
        'conductor-fork-join-timeout-retry',
        'conductor-fork-join-timeout-retry',
        'hank733',
        'feat: fork',
        'workflow.json',
        'charge.json',
        'workflow_test.py',
        14,
        'fj',
        'Conductor leftover FORK Join timeout retries the whole fork so both branches Charge.create again',
        'fork join',
        'Join timeout must not restart a branch that already charged',
        'per-task retryCount=0 on Charge plus a JOIN failure that compensates instead of restart',
        'FORK|JOIN|retryCount',
        'airflow-catchup-true-charge plant',
    ),
    (
        'wire-provider-set-double-bind',
        'wire-provider-set-double-bind',
        'foot746',
        'feat: wire',
        'wire.go',
        'charge.go',
        'wire_test.go',
        25,
        'ps',
        'Wire leftover ProviderSet binds ChargeClient twice so leftover Init charges with two clients and double-captures',
        'wire inject',
        'ChargeClient must be provided once per process',
        'one ProviderSet and wiretest that panics on duplicate bind',
        'ProviderSet|ChargeClient|duplicate',
        'fx-onstart plant',
    ),
    (
        'dagger-withenv-secret-plaintext',
        'dagger-withenv-secret-plaintext',
        'foot747',
        'feat: withenv',
        'ci.go',
        'charge.go',
        'ci_test.go',
        30,
        'we',
        'Dagger leftover withEnv puts the charge API key in plaintext so a leftover cache volume replays Charge.create',
        'dagger pipeline',
        'the API key must not be in withEnv or the cache must not replay Charge.create',
        'withSecretVariable plus cache mounts that exclude env',
        'withEnv|withSecretVariable|cache',
        'gha-rerun-double-charge plant',
    ),
    (
        'fx-invoke-onstart-double-hook',
        'fx-invoke-onstart-double-hook',
        'foot748',
        'feat: onstart',
        'module.go',
        'charge.go',
        'module_test.go',
        21,
        'os',
        'fx leftover Invoke plus OnStart both Charge.create so process boot leftover double-captures the leftover SKU',
        'fx boot',
        'boot must Charge.create at most once',
        'only OnStart or only Invoke, with a sync.Once around Charge.create',
        'OnStart|Invoke|Once',
        'wire-provider-set-double-bind plant',
    ),
    (
        'sqlc-copyfrom-no-conflict',
        'sqlc-copyfrom-no-conflict',
        'gaff710',
        'feat: copyfrom',
        'invoice.sql',
        'copy.go',
        'copy_test.go',
        24,
        'cf',
        'sqlc :copyfrom leftover inserts invoice rows with no ON CONFLICT so a retry duplicates GMV',
        'nightly copy',
        'retry of CopyFrom must not insert a second invoice_id',
        'COPY with ON CONFLICT (invoice_id) DO NOTHING or a unique index plus upsert',
        'copyfrom|ON CONFLICT|invoice_id',
        'bun-onconflict plant',
    ),
    (
        'prisma-interactive-txn-lost-update',
        'prisma-interactive-txn-lost-update',
        'gaff711',
        'feat: debit',
        'wallet.ts',
        'debit.ts',
        'wallet.test.ts',
        31,
        'lv',
        'Prisma $transaction leftover uses default isolation so two debit txs both read 100 and write 50, overdrafting',
        'wallet debit',
        'two concurrent debits must not both commit against the same pre-debit snapshot',
        'isolationLevel Serializable or UPDATE ... SET bal = bal - n WHERE bal >= n',
        '$transaction|Serializable|bal',
        'mikro-upsert plant',
    ),
    (
        'ent-hook-skip-mutators-serial',
        'ent-hook-skip-mutators-serial',
        'gaff712',
        'feat: hook',
        'hook.go',
        'wallet.go',
        'hook_test.go',
        29,
        'hk',
        'ent MutateFunc leftover returns next without wrapping so a serializable debit hook never runs and two cashiers overdraft',
        'ent debit hook',
        'the debit hook must run on every Mutation or the cashier path must fail closed',
        'return hook.On(next, ent.OpUpdate) and assert the hook fired in tests',
        'MutateFunc|hook.On|OpUpdate',
        'ent-upsert plant',
    ),
    (
        'websocket-resume-seq-skip',
        'websocket-resume-seq-skip',
        'stay716',
        'feat: resume',
        'ws.py',
        'order.py',
        'test_ws.py',
        36,
        'sq',
        'WebSocket resume leftover ignores lastSeq so a reconnect replays PLACE_ORDER and double-fills',
        'order socket',
        'resume must ack lastSeq and must not replay an already-filled PLACE_ORDER',
        'store lastSeq server-side and skip events <= lastSeq',
        'lastSeq|resume|PLACE_ORDER',
        'redis-xack plant',
    ),
    (
        'sse-last-event-id-ignored',
        'sse-last-event-id-ignored',
        'stay717',
        'feat: sse',
        'stream.ts',
        'charge.ts',
        'stream.test.ts',
        27,
        'eid',
        'SSE handler leftover ignores Last-Event-ID so EventSource reconnects replay charge events already captured',
        'sse charge',
        'reconnect must not emit a charge id already sent',
        'honor Last-Event-ID and skip ids <= cursor',
        'Last-Event-ID|EventSource|charge',
        'pulsar-ack plant',
    ),
    (
        'mqtt-qos0-retained-stale-price',
        'mqtt-qos0-retained-stale-price',
        'stay718',
        'feat: retain',
        'broker.py',
        'price.py',
        'test_price.py',
        15,
        'rt',
        'MQTT publish leftover uses QoS 0 plus retain so a stale price is delivered after a newer quote and the buyer is overcharged',
        'price topic',
        'a retained stale price must not beat a later quote',
        'QoS 1 plus retain replace on the same topic and a version field',
        'QoS|retain|price',
        'redis-streams plant',
    ),
)



def _plants_from_extracted() -> tuple[Plant, ...]:
    plants = tuple(
        plant_from_mapping(dict(zip(PLANT_FIELDS, row, strict=True)), f"extracted[{index}]")
        for index, row in enumerate(_EXTRACTED_ROWS)
    )
    _check_unique(plants)
    _reject_covered(plants)
    return plants


_CATALOG = Catalog(CATALOG_ID, _plants_from_extracted())


def load_catalog() -> Catalog:
    return _CATALOG


bind_import_twin(__name__)
