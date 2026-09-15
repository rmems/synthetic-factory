#!/usr/bin/env python3
"""CRP plant catalog: AST extract of leftover3 rows, each carrying ``noun``.

``plants_from_source`` walks a mill module for literal ``P(...)`` /
``_p(...)`` calls, or expands a literal ``_RAW`` block with the pinned
``keel{{base + i}}`` loop shape. The committed leftover3 catalog is the
third leftover leftover leftover wave (r729+) extracted from
``experiments/code_review_preference_mill_leftover3.py`` on
``legacy-mill-lane``. The mill files themselves are not vendored.

Every row includes ``noun`` (the third ``P`` argument). ``repo`` is
derived as ``plant/{noun}-{slug}`` and is not a separate extract field.
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
    FINDING_DUPLICATE_FAMILY,
    FINDING_DUPLICATE_SLUG,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_NOUN_MISSING,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_TRIPLE_OUT_OF_DOMAIN,
    bind_import_twin,
    refuse,
    refuse_first,
    refuse_when,
    shown,
)

CATALOG_ID = "crp-leftover3-v1"
FACTORY = "code-review-preference-factory"
GENERATOR = "grok-4.6"
ID_PREFIX = "crp"
WAVE_FIRST_ROUND = 729
PLANTS_PER_ROUND = 3
PAIR_FIRST_ROUND = 432  # pair() PR numbering, extracted from crp-mill-r432

PLANT_FIELDS = (
    "family", "slug", "noun", "title", "core", "boot", "test", "line", "nit",
    "defect", "reach", "missing", "fix", "needles", "notfam",
)
CALL_NAMES = frozenset({"P", "_p"})

__all__ = [
    "CATALOG_ID", "FACTORY", "GENERATOR", "ID_PREFIX", "PAIR_FIRST_ROUND",
    "PLANT_FIELDS", "PLANTS_PER_ROUND", "WAVE_FIRST_ROUND", "Catalog", "Plant",
    "catalog_check", "load_catalog", "plant_from_mapping", "plants_for_round",
    "plants_from_source",
]


@dataclass(frozen=True)
class Plant:
    """One AST-extracted leftover3 plant. ``noun`` is required."""

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


def _literal_or_none(node: ast.AST) -> Any | None:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


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
        literal = _literal_or_none(arg)
        if literal is None:
            return None
        values[PLANT_FIELDS[index]] = literal
    for keyword in node.keywords:
        values[keyword.arg] = _literal(keyword.value)
    return values


def _indexed_noun_base(node: ast.AST) -> tuple[str, int] | None:
    """Parse ``f\"{{prefix}}{{base + i}}\"`` from a ``_p`` noun in a ``_RAW`` expand loop."""

    if not isinstance(node, ast.JoinedStr) or len(node.values) != 2:
        return None
    prefix_node, formatted = node.values
    if not isinstance(prefix_node, ast.Constant) or not isinstance(prefix_node.value, str):
        return None
    prefix = prefix_node.value
    if prefix not in {"keel", "atoll"}:
        return None
    if not isinstance(formatted, ast.FormattedValue):
        return None
    inner = formatted.value
    if isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.Add):
        if isinstance(inner.left, ast.Constant) and isinstance(inner.left.value, int):
            if isinstance(inner.right, ast.Name) and inner.right.id == "i":
                return prefix, inner.left.value
    return None


def _raw_rows_from_tree(tree: ast.AST) -> list[tuple[Any, ...]] | None:
    for node in tree.body:
        name: str | None = None
        value_node: ast.AST | None = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name, value_node = node.target.id, node.value
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name, value_node = target.id, node.value
                    break
        if name != "_RAW" or value_node is None:
            continue
        resolved = _literal_or_none(value_node)
        if not isinstance(resolved, list) or not resolved:
            return None
        rows: list[tuple[Any, ...]] = []
        for row in resolved:
            if not isinstance(row, tuple):
                return None
            rows.append(row)
        return rows
    return None


def _raw_noun_base_from_tree(tree: ast.AST) -> tuple[str, int] | None:
    for node in tree.body:
        if not isinstance(node, ast.For):
            continue
        if not (
            isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "enumerate"
        ):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
                continue
            call = stmt.value
            if not (
                isinstance(call.func, ast.Attribute)
                and call.func.attr == "append"
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "PLANTS"
            ):
                continue
            if not call.args or not isinstance(call.args[0], ast.Call):
                continue
            plant_call = call.args[0]
            if not (
                isinstance(plant_call.func, ast.Name)
                and plant_call.func.id in CALL_NAMES
                and len(plant_call.args) >= 3
            ):
                continue
            indexed = _indexed_noun_base(plant_call.args[2])
            if indexed is not None:
                return indexed
    return None


def _plants_from_raw_enumerate(tree: ast.AST) -> tuple[Plant, ...] | None:
    """Expand literal ``_RAW`` rows using the pinned ``{{prefix}}{{base + i}}`` loop shape."""

    rows = _raw_rows_from_tree(tree)
    if rows is None:
        return None
    indexed = _raw_noun_base_from_tree(tree)
    refuse_when(
        indexed is None,
        FINDING_AST_NOT_A_PLANT,
        "_RAW expand loop has no indexed {{prefix}}{{base + i}} noun",
    )
    prefix, base = indexed
    ordered: list[Plant] = []
    for index, row in enumerate(rows):
        refuse_when(
            len(row) != 13,
            FINDING_AST_NOT_A_PLANT,
            f"_RAW[{index}] must unpack to 13 fields, got {len(row)}",
        )
        (
            family,
            title,
            core,
            boot,
            test,
            line,
            nit,
            defect,
            reach,
            missing,
            fix,
            needles,
            notfam,
        ) = row
        refuse_when(
            not isinstance(family, str) or not family,
            FINDING_AST_NOT_A_PLANT,
            f"_RAW[{index}] family must be a non-empty string",
        )
        refuse_when(
            type(line) is not int,
            FINDING_FIELD_INVALID,
            f"_RAW[{index}].line must be an int, got {shown(line)}",
        )
        mapping = {
            "family": family,
            "slug": family,
            "noun": f"{prefix}{base + index}",
            "title": title,
            "core": core,
            "boot": boot,
            "test": test,
            "line": line,
            "nit": nit,
            "defect": defect,
            "reach": reach,
            "missing": missing,
            "fix": fix,
            "needles": needles,
            "notfam": notfam,
        }
        ordered.append(plant_from_mapping(mapping, f"_RAW[{index}]"))
    return tuple(ordered)


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
    if ordered:
        return tuple(ordered)
    expanded = _plants_from_raw_enumerate(tree)
    if expanded:
        return expanded
    refuse(FINDING_CATALOG_EMPTY, "mill source has no literal P() rows or _RAW expand block")


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


def catalog_check(plants: tuple[Plant, ...] | None = None) -> dict[str, Any]:
    """Fail closed unless every row has noun, unique identity, and a 3-stride."""

    items = load_catalog().plants if plants is None else plants
    refuse_when(not items, FINDING_CATALOG_EMPTY, "catalog has no plants")
    refuse_when(
        len(items) % PLANTS_PER_ROUND != 0,
        FINDING_CATALOG_TRIPLE_STRIDE,
        f"catalog length {len(items)} is not a multiple of {PLANTS_PER_ROUND}",
    )
    _check_unique(items)
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


# AST-extracted leftover3 rows. Field order is PLANT_FIELDS; noun is index 2.
_EXTRACTED_ROWS: tuple[tuple[Any, ...], ...] = (
    (
        'terraform-target-orphan-sku',
        'terraform-target-orphan-sku',
        'keel801',
        'feat: target',
        'main.tf',
        'sku.tf',
        'test_target.py',
        47,
        'tg',
        'terraform apply -target leftover so a Chargeable sku is created without its lock resource and a second apply bills a twin SKU',
        'partial apply',
        'targeted apply must not leave a billed sku without its lock companion',
        'forbid money resources in -target or apply the lock module in the same graph',
        '-target|sku|lock',
        'terraform-statelock-skip-apply plant',
    ),
    (
        'pulumi-ignorechanges-drop-protect',
        'pulumi-ignorechanges-drop-protect',
        'keel802',
        'feat: ignore',
        'index.ts',
        'rds.ts',
        'index.test.ts',
        31,
        'ig',
        'pulumi ignoreChanges leftover on deletionProtect so a leftover stack up deletes the protected RDS and the recreate double-bills',
        'stack up',
        'ignoreChanges must not drop deletionProtect on a billed RDS',
        'keep deletionProtect outside ignoreChanges and protect the URN',
        'ignoreChanges|deletionProtect|RDS',
        'pulumi-refresh-false-recreate plant',
    ),
    (
        'tofu-moved-block-skip-state',
        'tofu-moved-block-skip-state',
        'keel803',
        'feat: moved',
        'moved.tf',
        'sku.tf',
        'moved_test.go',
        22,
        'mv',
        'OpenTofu leftover moved block is commented so state leftover still addresses the old address and apply creates a second billed sku',
        'tofu apply',
        'rename must move state not create a second Chargeable',
        'moved { from = old to = new } plus a plan test that shows 0 add',
        'moved|from|to',
        'crossplane-updatepolicy-manual-claim plant',
    ),
    (
        'helm-atomic-false-hook-orphan',
        'helm-atomic-false-hook-orphan',
        'spar804',
        'feat: atomic',
        'Chart.yaml',
        'hooks.yaml',
        'hook_test.go',
        18,
        'at',
        'helm upgrade --atomic=false leftover so a failed release leftover leaves the charge hook Job and the next upgrade double-charges',
        'release upgrade',
        'a failed upgrade must not leave a Job that Charge.create again',
        '--atomic plus hook-delete-policy hook-succeeded,hook-failed',
        'atomic|hook|Job',
        'helm-hook-delete-before-missing plant',
    ),
    (
        'kustomize-replacements-omit-ns',
        'kustomize-replacements-omit-ns',
        'spar805',
        'feat: replace',
        'kustomization.yaml',
        'replace.yaml',
        'kustomize_test.go',
        14,
        'rp',
        'kustomize replacements leftover omit namespace so leftover name hits staging Charge and prod traffic bills staging SKUs',
        'overlay replace',
        'replacements must be namespace-scoped or they must not retarget Charge',
        'source.namespace + target.namespace selectors and a build test',
        'replacements|namespace|Charge',
        'kustomize-nameprefix-omit-overlay plant',
    ),
    (
        'tanka-apply-prune-false-orphan',
        'tanka-apply-prune-false-orphan',
        'spar806',
        'feat: prune',
        'main.jsonnet',
        'charge.jsonnet',
        'tanka_test.py',
        26,
        'pr',
        'tk apply leftover --prune=false so a leftover charge Deployment stays and both old and new pods POST /charge',
        'tanka apply',
        'orphaned charge Deployments must be pruned',
        'tk apply --prune plus an apply test that asserts one Charge owner',
        'prune|tk apply|Deployment',
        'jsonnet-mergepatch-array-concat plant',
    ),
    (
        'opa-else-true-default-allow',
        'opa-else-true-default-allow',
        'boom807',
        'feat: else',
        'authz.rego',
        'charge.rego',
        'authz_test.rego',
        51,
        'el',
        'OPA leftover allow { input.role == "cashier" } else = true so a leftover missing role is allowed and any caller Charge.create',
        'rego else',
        'else must not default allow on Charge.create',
        'default allow := false and else = false; no else-true on money',
        'else = true|default allow|Charge',
        'opa-input-user-package-leak plant',
    ),
    (
        'cedar-unless-clause-dropped',
        'cedar-unless-clause-dropped',
        'boom808',
        'feat: unless',
        'policy.cedar',
        'charge.cedar',
        'cedar_test.py',
        19,
        'un',
        'Cedar leftover permit ... unless { context.frozen } drops the unless when context is null so a frozen account still charges',
        'cedar unless',
        'missing context.frozen must fail closed not skip unless',
        'require context.frozen is present; forbid when context is empty',
        'unless|context.frozen|permit',
        'cedar-context-ip-permit-all plant',
    ),
    (
        'spicedb-zedtoken-minimize-stale',
        'spicedb-zedtoken-minimize-stale',
        'boom809',
        'feat: zedtoken',
        'check.go',
        'charge.go',
        'check_test.go',
        36,
        'zt',
        'SpiceDB leftover Check uses MinimizeLatency so a just-revoked relation leftover still allows Charge.create',
        'zedtoken check',
        'Check after revoke must not allow the same SKU charge',
        'Consistency FullyConsistent or AtLeastAsFresh(zedtoken) after WriteRelationships',
        'MinimizeLatency|zedtoken|Check',
        'openfga-write-without-consistency plant',
    ),
    (
        'graphql-alias-cost-bypass',
        'graphql-alias-cost-bypass',
        'vang810',
        'feat: cost',
        'cost.ts',
        'schema.ts',
        'cost.test.ts',
        23,
        'al',
        'GraphQL leftover cost analysis counts field name not alias so leftover aliases multiply Charge.create under budget',
        'gql cost',
        'aliased Charge fields must count toward cost or be rejected',
        'cost by resolved field + alias fan-out cap',
        'alias|cost|Charge',
        'graphql-dataloader-tenant-cache plant',
    ),
    (
        'grpc-retry-pushback-ignored',
        'grpc-retry-pushback-ignored',
        'vang811',
        'feat: pushback',
        'client.go',
        'charge.go',
        'client_test.go',
        44,
        'pb',
        'gRPC leftover retry ignores grpc-retry-pushback-ms so a leftover UNAVAILABLE retry double-sends ChargeCreate',
        'retry charge',
        'pushback must delay or drop a retry that would ChargeCreate twice',
        'honor grpc-retry-pushback-ms plus idempotency metadata',
        'pushback|UNAVAILABLE|ChargeCreate',
        'grpc-stream-no-deadline-retry plant',
    ),
    (
        'connect-timeout-interceptor-drop',
        'connect-timeout-interceptor-drop',
        'vang812',
        'feat: timeout',
        'intercept.go',
        'charge.go',
        'intercept_test.go',
        17,
        'to',
        'Connect leftover timeout interceptor drops the error so the client leftover retries ChargeCreate as a new RPC',
        'connect charge',
        'timeout must not be swallowed into a naked retry ChargeCreate',
        'propagate deadline exceeded and reuse Idempotency-Key',
        'timeout|interceptor|ChargeCreate',
        'trpc-superjson-date-utc-shift plant',
    ),
    (
        'clickhouse-ttl-move-lost-refund',
        'clickhouse-ttl-move-lost-refund',
        'clew813',
        'feat: ttl',
        'ttl.sql',
        'refund.sql',
        'test_ttl.sql',
        12,
        'tl',
        'ClickHouse leftover TTL MOVE PARTITION during a refund insert so the refund row leftover never lands and finance keeps the capture',
        'ttl move',
        'TTL move must not drop an in-flight refund for a captured charge',
        'TTL only after COMMIT and a mutation that waits for inserts',
        'TTL MOVE|refund|PARTITION',
        'clickhouse-replacing-no-final plant',
    ),
    (
        'druid-keepsegment-miss-overlap',
        'druid-keepsegment-miss-overlap',
        'clew814',
        'feat: compact',
        'compact.json',
        'spec.json',
        'compact_test.py',
        28,
        'ks',
        'Druid leftover compaction omits keepSegmentGranularity so leftover overlapping segments both SUM the same charge',
        'compact task',
        'compaction must not leave two live segments for the same interval charge',
        'keepSegmentGranularity true plus a query that asserts one row per charge_id',
        'keepSegmentGranularity|compact|charge',
        'druid-rollup-double-count plant',
    ),
    (
        'starrocks-partial-update-dup-pk',
        'starrocks-partial-update-dup-pk',
        'clew815',
        'feat: partial',
        'table.sql',
        'charge.sql',
        'table_test.py',
        21,
        'pu',
        'StarRocks leftover partial_update on PRIMARY KEY with leftover missing columns so a replay appends a second billed amount',
        'sr upsert',
        'partial update must replace the same charge_id not append GMV',
        'full-row upsert or specify all money columns plus unique charge_id',
        'partial_update|PRIMARY KEY|charge_id',
        'pinot-upsert-mode-none-dup plant',
    ),
    (
        'nats-kv-history-zero-lost-ack',
        'nats-kv-history-zero-lost-ack',
        'reef816',
        'feat: kv',
        'kv.go',
        'charge.go',
        'kv_test.go',
        33,
        'kv',
        'NATS KV leftover history=0 so a leftover Put of charged=true vanishes and the worker Charge.create again',
        'kv idempotency',
        'history 0 must not drop the charged marker',
        'history>=1 plus create-only Put on charge_id',
        'history=0|KV|charge_id',
        'nats-js-ackwait-redeliver-charge plant',
    ),
    (
        'kafka-autooffset-latest-skip-refund',
        'kafka-autooffset-latest-skip-refund',
        'reef817',
        'feat: offset',
        'consumer.properties',
        'refund.go',
        'consumer_test.go',
        9,
        'ao',
        'Kafka leftover auto.offset.reset=latest so a restarted refund consumer leftover skips the refund topic and captures stay',
        'refund consumer',
        'restart must not skip unprocessed refund records',
        'auto.offset.reset=earliest plus committed offsets and a unique refund_id',
        'auto.offset.reset|latest|refund',
        'kafka-idempotence-false-dup plant',
    ),
    (
        'pulsar-acktimeout-redeliver-charge',
        'pulsar-acktimeout-redeliver-charge',
        'reef818',
        'feat: acktimeout',
        'consumer.go',
        'charge.go',
        'consumer_test.go',
        41,
        'ak',
        'Pulsar leftover ackTimeout shorter than Stripe RTT so leftover redelivery Charge.create runs twice',
        'pulsar consumer',
        'ackTimeout must outlast the Stripe call or the handler must be idempotent',
        'ackTimeout>=30s plus Idempotency-Key = messageId',
        'ackTimeout|redeliver|Charge.create',
        'redpanda-txn-id-missing-abort plant',
    ),
    (
        'cue-list-open-extra-sku',
        'cue-list-open-extra-sku',
        'batten819',
        'feat: list',
        'sku.cue',
        'price.cue',
        'sku_test.go',
        15,
        'ls',
        'CUE leftover [...#Sku] is open-tailed so leftover extra sku entries are accepted and a hidden SKU is billed',
        'cue list',
        'sku lists must reject extra elements',
        '[N]#Sku closed list plus cue vet',
        '[...]#Sku|vet|sku',
        'cue-closed-struct-extra-sku plant',
    ),
    (
        'dhall-aslocation-unsigned-import',
        'dhall-aslocation-unsigned-import',
        'batten820',
        'feat: aslocation',
        'price.dhall',
        'import.dhall',
        'price_test.py',
        18,
        'al',
        'Dhall leftover as Location import leftover skips integrity so a swapped price file leftover bills 100x',
        'dhall import',
        'as Location must not load an unsigned price map',
        'sha256 integrity on every import and no as Location for money',
        'as Location|sha256|price',
        'dhall-tomap-type-hole-price plant',
    ),
    (
        'nickel-merge-priority-force-price',
        'nickel-merge-priority-force-price',
        'batten821',
        'feat: merge',
        'price.ncl',
        'sku.ncl',
        'price_test.py',
        24,
        'mp',
        'Nickel leftover merge force leftover lets an overlay override cents without a contract so a leftover 1-cent SKU is billed as 10000',
        'ncl merge',
        'force merge must not bypass the cents contract',
        'contract on cents plus default merge not force',
        'force|contract|cents',
        'jsonnet-importstr-secret-double plant',
    ),
    (
        'nix-flakelock-narhash-omit',
        'nix-flakelock-narhash-omit',
        'leech822',
        'feat: flake',
        'flake.lock',
        'flake.nix',
        'flake_test.py',
        20,
        'nh',
        'nix leftover flake.lock omits narHash so a leftover input swap injects a charge binary that double-posts',
        'nix flake',
        'inputs without narHash must not evaluate in CI',
        'require narHash on every flake input and --no-update-lock-file',
        'narHash|flake.lock|input',
        'nix-fetchurl-sha256-empty plant',
    ),
    (
        'guix-inferior-ungraft-charge',
        'guix-inferior-ungraft-charge',
        'leech823',
        'feat: ungraft',
        'manifest.scm',
        'charge.scm',
        'manifest_test.py',
        27,
        'ug',
        'Guix leftover inferior --no-grafts leftover installs the ungrafted charge CLI that still POSTs /charge twice',
        'guix package',
        'production must not install an ungrafted charge CLI',
        'forbid --no-grafts on money packages plus a graft test',
        '--no-grafts|inferior|charge',
        'guix-ungexp-gexp-charge-dup plant',
    ),
    (
        'portage-accept-keywords-live-ebuild',
        'portage-accept-keywords-live-ebuild',
        'leech824',
        'feat: keywords',
        'package.accept_keywords',
        'charge.ebuild',
        'ebuild_test.py',
        16,
        'ak',
        'Portage leftover ACCEPT_KEYWORDS=** leftover pulls a live ebuild whose src_install leftover double-captures',
        'emerge charge',
        'live keywords must not install an unpinned charge ebuild',
        'pin a stable keyword and SRC_URI hash',
        'ACCEPT_KEYWORDS|live|SRC_URI',
        'spack-concretizer-hash-flip plant',
    ),
    (
        'duckdb-copy-overwrite-no-txn',
        'duckdb-copy-overwrite-no-txn',
        'luff825',
        'feat: copy',
        'gmv.sql',
        'copy.sql',
        'test_copy.py',
        13,
        'cp',
        'DuckDB leftover COPY ... OVERWRITE outside a txn so a leftover crash leaves half the GMV file and finance double-imports the next file',
        'copy gmv',
        'COPY overwrite must be atomic or finance must not re-import a torn file',
        'COPY inside BEGIN; commit rename of a temp file',
        'COPY|OVERWRITE|txn',
        'duckdb-attach-write-stale-gmv plant',
    ),
    (
        'sqlite-shared-cache-writer-lost',
        'sqlite-shared-cache-writer-lost',
        'luff826',
        'feat: shared',
        'db.py',
        'refund.py',
        'test_shared.py',
        35,
        'sc',
        'SQLite leftover shared-cache writer leftover unlocks mid-refund so a second connection leftover commits the capture without the refund',
        'shared cache',
        'shared-cache must not drop a refund while the capture commits',
        'WAL + one writer connection or IMMEDIATE txn covering capture+refund',
        'shared-cache|IMMEDIATE|refund',
        'sqlite-wal-checkpoint-lost-refund plant',
    ),
    (
        'turso-embedded-replica-stale-gmv',
        'turso-embedded-replica-stale-gmv',
        'luff827',
        'feat: replica',
        'replica.go',
        'gmv.sql',
        'replica_test.go',
        19,
        'er',
        'Turso leftover embedded replica sync leftover lags so finance leftover SUMs a stale GMV snapshot and re-invoices yesterday',
        'turso replica',
        'invoice queries must not run on a replica behind the invoice watermark',
        'wait for frame_no >= watermark or query primary',
        'embedded replica|frame_no|watermark',
        'motherduck-share-snapshot-stale plant',
    ),
    (
        'wasm-wasi-clock-unbounded-loop',
        'wasm-wasi-clock-unbounded-loop',
        'cringle828',
        'feat: clock',
        'host.go',
        'charge.go',
        'host_test.go',
        38,
        'ck',
        'WASM leftover WASI clock_time_get is unmetered so a guest leftover busy-waits then Charge.create twice after timeout',
        'wasi clock',
        'guest must not call Charge.create more than once per invoice after a clock loop',
        'fuel on clock_time_get plus host idempotency map',
        'clock_time_get|fuel|Charge.create',
        'wasm-host-call-unmetered-charge plant',
    ),
    (
        'lua-setfenv-restore-miss',
        'lua-setfenv-restore-miss',
        'cringle829',
        'feat: setfenv',
        'sandbox.lua',
        'charge.lua',
        'sandbox_test.py',
        21,
        'sf',
        'Lua leftover setfenv leftover is not restored so a later template leftover sees os.execute and curls Charge.create',
        'lua env',
        'setfenv must restore a sandbox that cannot os.execute a charge',
        'setfenv restore in finally plus nil os.execute',
        'setfenv|os.execute|restore',
        'lua-sandbox-os-execute-charge plant',
    ),
    (
        'extism-host-fn-reentry-charge',
        'extism-host-fn-reentry-charge',
        'cringle830',
        'feat: reentry',
        'host.go',
        'plugin.go',
        'host_test.go',
        29,
        're',
        'Extism leftover host function leftover re-enters Charge.create while the first call is in flight so two captures land',
        'extism host',
        'host Charge.create must not re-enter for the same invoice_id',
        'reentrancy guard plus idempotency on invoice_id',
        'reenter|Charge.create|invoice_id',
        'cel-optional-shortcircuit-skip-deny plant',
    ),
    (
        'jwt-typ-none-confused-verify',
        'jwt-typ-none-confused-verify',
        'shroud831',
        'feat: typ',
        'jwt.go',
        'charge.go',
        'jwt_test.go',
        54,
        'ty',
        'JWT leftover Verify accepts typ=none leftover so an unsigned token leftover authorizes Charge.create',
        'jwt typ',
        'typ none must not authorize Charge.create',
        'require typ=JWT and alg allow-list; reject none',
        'typ=none|alg|Charge',
        'jwt-nbf-unverified-early plant',
    ),
    (
        'paseto-purpose-local-as-public',
        'paseto-purpose-local-as-public',
        'shroud832',
        'feat: purpose',
        'paseto.py',
        'keys.py',
        'test_paseto.py',
        20,
        'pu',
        'PASETO leftover parser leftover treats v4.local as v4.public so a leftover shared-secret token verifies as a charge grant',
        'paseto purpose',
        'local tokens must not verify as public charge grants',
        'strict purpose check before verify and reject purpose mismatch',
        'v4.local|v4.public|purpose',
        'paseto-footer-unbound-keyid plant',
    ),
    (
        'branca-ttl-unverified-early',
        'branca-ttl-unverified-early',
        'shroud833',
        'feat: ttl',
        'branca.go',
        'charge.go',
        'branca_test.go',
        16,
        'tt',
        'Branca leftover decode leftover skips ttl so an expired leftover token still Charge.create',
        'branca ttl',
        'expired ttl must not authorize Charge.create',
        'decode with ttl and reject timestamp + ttl < now',
        'ttl|timestamp|Charge',
        'macaroon-caveat-unverified-sku plant',
    ),
    (
        'argon2-ad-omit-context',
        'argon2-ad-omit-context',
        'tack834',
        'feat: ad',
        'hash.go',
        'passwd.go',
        'hash_test.go',
        13,
        'ad',
        'argon2 leftover AssociatedData leftover is omitted so a leftover hash minted for support login verifies on the cashier path',
        'argon2 ad',
        'hashes must bind AssociatedData to the login surface',
        'AssociatedData=surface plus verify that fails across surfaces',
        'AssociatedData|argon2id|surface',
        'argon2-type-i-not-id plant',
    ),
    (
        'bcrypt-cost-four-offline',
        'bcrypt-cost-four-offline',
        'tack835',
        'feat: cost',
        'hash.py',
        'passwd.py',
        'test_hash.py',
        11,
        'cs',
        'bcrypt leftover cost=4 leftover so offline guess leftover opens the cashier in minutes',
        'bcrypt cost',
        'cost 4 must not be used on cashier passwords',
        'cost>=12 and reject hashes with cost<10 at verify',
        'cost=4|bcrypt|cashier',
        'bcrypt-72-byte-truncate plant',
    ),
    (
        'yescrypt-flags-default-weak',
        'yescrypt-flags-default-weak',
        'tack836',
        'feat: flags',
        'kdf.go',
        'passwd.go',
        'kdf_test.go',
        18,
        'fl',
        'yescrypt leftover flags leftover default to YESCRYPT_WORM so leftover parallel attack opens two wallets with one password',
        'yescrypt flags',
        'WORM flags must not be used for wallet passwords',
        'YESCRYPT_RW_DEFAULTS plus per-row salt',
        'YESCRYPT_WORM|flags|salt',
        'scrypt-n-small-salt-reuse plant',
    ),
    (
        'temporal-signal-buffer-drop-refund',
        'temporal-signal-buffer-drop-refund',
        'hank837',
        'feat: signal',
        'workflow.go',
        'refund.go',
        'workflow_test.go',
        56,
        'sg',
        'Temporal leftover signal buffer leftover drops Refund when the workflow is ContinueAsNew so the capture leftover stays',
        'signal refund',
        'Refund signals must not be dropped across ContinueAsNew',
        'drain signals before ContinueAsNew and persist refund intent',
        'signal|buffer|Refund',
        'temporal-continueasnew-side-effect plant',
    ),
    (
        'cadence-sticky-cache-stale-decision',
        'cadence-sticky-cache-stale-decision',
        'hank838',
        'feat: sticky',
        'worker.go',
        'charge.go',
        'worker_test.go',
        42,
        'st',
        'Cadence leftover sticky cache leftover replays a stale decision leftover so Charge.create runs after the workflow already refunded',
        'sticky worker',
        'sticky cache must not emit Charge.create after refund',
        'disable sticky on money workflows or invalidate cache on refund',
        'sticky|decision|Charge.create',
        'cadence-parent-close-abandon-child plant',
    ),
    (
        'restate-journal-skip-replay-charge',
        'restate-journal-skip-replay-charge',
        'hank839',
        'feat: journal',
        'service.ts',
        'charge.ts',
        'service.test.ts',
        25,
        'jr',
        'Restate leftover journal skip leftover re-executes Charge.create on replay so a recovered invocation double-captures',
        'restate replay',
        'replay must not Charge.create a SKU already journaled',
        'ctx.run idempotent key=invoice_id and no journal skip',
        'journal|ctx.run|invoice_id',
        'conductor-fork-join-timeout-retry plant',
    ),
    (
        'wire-cleanup-unbind-midflight',
        'wire-cleanup-unbind-midflight',
        'foot840',
        'feat: cleanup',
        'wire.go',
        'charge.go',
        'wire_test.go',
        27,
        'cl',
        'Wire leftover Cleanup leftover closes ChargeClient mid-request so the retry leftover constructs a second client and double-captures',
        'wire cleanup',
        'Cleanup must not close ChargeClient while a charge is in flight',
        'lifecycle After request plus sync.Once on client close',
        'Cleanup|ChargeClient|close',
        'wire-provider-set-double-bind plant',
    ),
    (
        'dagger-export-cache-replay-charge',
        'dagger-export-cache-replay-charge',
        'foot841',
        'feat: export',
        'ci.go',
        'charge.go',
        'ci_test.go',
        32,
        'ex',
        'Dagger leftover Export leftover caches the charge step so a leftover cache hit replays Charge.create',
        'dagger export',
        'cache must not replay Charge.create',
        'CacheVolume exclude on charge steps plus withExec --no-cache for money',
        'Export|CacheVolume|Charge.create',
        'dagger-withenv-secret-plaintext plant',
    ),
    (
        'fx-decorate-order-flip-hook',
        'fx-decorate-order-flip-hook',
        'foot842',
        'feat: decorate',
        'module.go',
        'charge.go',
        'module_test.go',
        22,
        'dc',
        'fx leftover Decorate leftover reverses hook order so leftover OnStop Charge.create runs at boot and double-captures',
        'fx decorate',
        'Decorate must not run OnStop Charge.create at start',
        'explicit hook order test plus Charge.create only in OnStart once',
        'Decorate|OnStop|OnStart',
        'fx-invoke-onstart-double-hook plant',
    ),
    (
        'sqlc-batchexec-ignore-rows',
        'sqlc-batchexec-ignore-rows',
        'gaff843',
        'feat: batch',
        'invoice.sql',
        'batch.go',
        'batch_test.go',
        24,
        'be',
        'sqlc leftover :batchexec leftover ignores RowsAffected so a leftover retry inserts a second invoice_id and GMV doubles',
        'batch invoice',
        'retry of BatchExec must not insert a second invoice_id',
        'check RowsAffected and ON CONFLICT (invoice_id) DO NOTHING',
        'batchexec|RowsAffected|invoice_id',
        'sqlc-copyfrom-no-conflict plant',
    ),
    (
        'prisma-middleware-skip-softdelete',
        'prisma-middleware-skip-softdelete',
        'gaff844',
        'feat: middleware',
        'wallet.ts',
        'mw.ts',
        'wallet.test.ts',
        30,
        'mw',
        'Prisma leftover middleware leftover skips soft-delete filter so a leftover debit hits a refunded wallet and overdrafts',
        'prisma middleware',
        'soft-deleted wallets must not accept a debit',
        'middleware that always AND deletedAt=null on wallet update',
        'deletedAt|middleware|$use',
        'prisma-interactive-txn-lost-update plant',
    ),
    (
        'drizzle-idle-txn-lost-update',
        'drizzle-idle-txn-lost-update',
        'gaff845',
        'feat: idle',
        'wallet.ts',
        'debit.ts',
        'wallet.test.ts',
        28,
        'id',
        'Drizzle leftover transaction leftover idles past idle_in_transaction so leftover two debits both commit against the pre-debit snapshot',
        'drizzle debit',
        'idle transactions must not both commit the same wallet debit',
        'statement timeout plus UPDATE ... SET bal = bal - n WHERE bal >= n',
        'idle_in_transaction|UPDATE|bal',
        'ent-hook-skip-mutators-serial plant',
    ),
    (
        'websocket-ping-interval-zero',
        'websocket-ping-interval-zero',
        'stay846',
        'feat: ping',
        'ws.py',
        'order.py',
        'test_ws.py',
        37,
        'pg',
        'WebSocket leftover ping_interval=0 leftover so a leftover half-open socket never dies and a reconnect leftover PLACE_ORDER double-fills',
        'order ping',
        'dead sockets must close before a reconnect PLACE_ORDER',
        'ping_interval>0 plus lastSeq skip on resume',
        'ping_interval|PLACE_ORDER|half-open',
        'websocket-resume-seq-skip plant',
    ),
    (
        'sse-retry-field-omitted',
        'sse-retry-field-omitted',
        'stay847',
        'feat: retry',
        'stream.ts',
        'charge.ts',
        'stream.test.ts',
        26,
        'ry',
        'SSE leftover omits retry: leftover so EventSource leftover reconnects immediately and replays a captured charge',
        'sse retry',
        'reconnect must not emit a charge id already sent',
        'retry: 5000 plus Last-Event-ID skip',
        'retry:|Last-Event-ID|charge',
        'sse-last-event-id-ignored plant',
    ),
    (
        'webtransport-datagram-unreliable-charge',
        'webtransport-datagram-unreliable-charge',
        'stay848',
        'feat: datagram',
        'wt.ts',
        'charge.ts',
        'wt.test.ts',
        18,
        'dg',
        'WebTransport leftover datagram leftover is unreliable so a leftover retry after loss Charge.create twice',
        'wt datagram',
        'unreliable datagrams must not carry Charge.create',
        'use reliable streams plus idempotency on invoice_id',
        'datagram|unreliable|Charge.create',
        'mqtt-qos0-retained-stale-price plant',
    ),
)


def _plants_from_extracted() -> tuple[Plant, ...]:
    plants = tuple(
        plant_from_mapping(dict(zip(PLANT_FIELDS, row, strict=True)), f"extracted[{index}]")
        for index, row in enumerate(_EXTRACTED_ROWS)
    )
    _check_unique(plants)
    return plants


_CATALOG = Catalog(CATALOG_ID, _plants_from_extracted())


def load_catalog() -> Catalog:
    return _CATALOG


bind_import_twin(__name__)
