#!/usr/bin/env python3
"""Corpus audit pipeline for the training-readiness audit.

``CorpusAudit`` owns the mutable counters and drives one file at a time
through decode, mill quarantine, exact-JSON validation, route dispatch
(code-repair, oracle, generic), and the per-record signal axes in
``training_audit_axes``. Facade seams are resolved through ``self.api`` so
``training_audit`` keeps owning the patchable names.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("training_audit_observe")
    from .training_audit_axes import AuditAxes
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_observe"
    )
    from training_audit_axes import AuditAxes


@dataclass(frozen=True)
class _AdmissionRoute:
    """The admission inputs one routed record carries."""

    lane: str
    obj: object
    where: str
    factory: str
    bucket: dict


class CorpusAudit(AuditAxes):
    """Mutable counters for one read-only training-audit pass."""

    def __init__(self, api, run_dir, mill_findings_by_ref, mill_mix):
        self.api = api
        self.run_dir = run_dir
        self.mill_findings_by_ref = mill_findings_by_ref
        self.mill_mix = mill_mix
        self.rights_audit = self.api._rights_audit.RightsAudit(())
        self.completion_source = None
        self._init_corpus_counters()
        self._init_identity_axes()
        self._init_signal_axes()

    def _init_corpus_counters(self):
        """Per-factory buckets and the flat record ledgers."""
        self.factories = defaultdict(
            lambda: {
                "files": 0,
                "records": 0,
                "eligible_records": 0,
                "bytes": 0,
                "approx_tokens": 0,
                "exact_json_contract_errors": 0,
                "by_kind": Counter(),
                "record_tokens": [],
            }
        )
        self.totals = Counter()
        self.code_repair = Counter()
        self.code_repair_reasons = Counter()
        self.oracle = Counter()
        self.oracle_reasons = Counter()
        self.kinds = Counter()
        self.record_errors = []
        self.unresolved_record_warnings = []

    def _init_identity_axes(self):
        """Id, duplicate, provenance, and gate ledgers."""
        self.ids = {}
        self.root_ids = {}
        self.canonical_id_records = 0
        self.root_id_records = 0
        self.missing_ids = []
        self.missing_root_ids = []
        self.duplicate_ids = []
        self.content_seen = {}
        self.exact_duplicates = []
        self.provenance = Counter()
        self.provenance_examples = defaultdict(list)
        self.gate_by_role = defaultdict(Counter)
        self.gate_errors = Counter()
        self.gate_error_examples = []

    def _init_signal_axes(self):
        """Preference, reward, distillation, and episode signal counters."""
        # Keep historic keys present for an all-episode preference corpus.
        self.preference = Counter(
            pairs=0,
            same_context=0,
            same_state=0,
            same_proposal=0,
            same_goal=0,
            episode_pairs=0,
            thalamic_pairs=0,
        )
        self.chosen_decisions = Counter()
        self.reward_keys = Counter()
        self.reward_shapes = Counter()
        self.tags = Counter()
        self.distillation = self.api.DistillationAudit()
        self.episodes = Counter(
            episodes=0,
            steps=0,
            decision_basis_steps=0,
            missing_decision_basis_steps=0,
            legacy_thought_only_steps=0,
            hidden_thought_fields=0,
        )
        self.hidden_thought_examples = []

    def observe_file(self, relative, payload=None):
        if payload is None:
            path = Path(relative)
            rel = path.relative_to(self.run_dir)
            payload = path.read_bytes()
        else:
            rel = Path(relative)
        factory = self.api.factory_for_path(self.run_dir, self.run_dir / rel)
        bucket = self.factories[factory]
        bucket["files"] += 1
        bucket["bytes"] += len(payload)
        self.totals["files"] += 1
        self.totals["bytes"] += len(payload)

        try:
            raw_lines = self.api._completion.audit_jsonl_records(
                rel, payload, self._completed_published_payload,
            )
        except self.api.StrictJsonlError as exc:
            self.record_errors.append(str(exc))
            return
        procedural_before = self.code_repair["records"]
        for line_number, raw_line in enumerate(raw_lines, 1):
            self._observe_line(raw_line, line_number, rel, factory)
        if self.code_repair["records"] > procedural_before:
            self._observe_completed_procedural_file(rel, payload, procedural_before)

    def _completed_published_payload(self, rel, payload) -> bool:
        source_root = self.completion_source or self.run_dir
        return self.api._completion.completed_published_payload(source_root, rel, payload)

    def _observe_completed_procedural_file(self, rel, payload, previous_records):
        if self._completed_published_payload(rel, payload):
            self.code_repair["completed_records"] += self.code_repair["records"] - previous_records

    def _observe_line(self, raw_line, line_number, rel, factory):
        if not raw_line.strip():
            return
        bucket = self.factories[factory]
        where = f"{rel}:{line_number}"
        try:
            line = raw_line.decode("utf-8")
        except UnicodeDecodeError as exc:
            self.record_errors.append(f"{where}: invalid UTF-8: {exc}")
            return

        self.totals["records"] += 1
        bucket["records"] += 1
        token_estimate = max(1, math.ceil(len(line.encode("utf-8")) / 4))
        try:
            obj = json.loads(
                line,
                object_pairs_hook=self.api.reject_duplicate_object_keys,
                parse_constant=self.api.reject_json_constant,
                parse_float=self.api._parse_finite_json_float,
            )
        except (ValueError, RecursionError) as exc:
            self._record_parse_error(where, exc, token_estimate, bucket)
            return

        finding = self.mill_findings_by_ref.get((rel.as_posix(), line_number))
        procedural_route = self._registered_code_repair_route(obj, factory)
        if finding is not None and not procedural_route:
            # Foreign evidence is excluded before every training invariant,
            # including the exact-JSON serialization contract.
            self.totals["quarantined"] += 1
            return
        try:
            self.api.canonical_blob(obj)
        except (ValueError, RecursionError) as exc:
            self._record_exact_json_contract_error(where, exc, token_estimate, bucket)
            return

        self._account_tokens(token_estimate, bucket)
        self._observe_valid_record(obj, where, factory)

    @staticmethod
    def _registered_code_repair_route(obj, factory):
        """Return whether path-derived registry authority permits procedural validation."""
        if not isinstance(obj, dict) or obj.get("family") != "python-function-repair":
            return False
        if __package__:
            from .curate_identity import default_registry
        else:
            from curate_identity import default_registry
        row = default_registry().by_path_id.get(factory)
        return (
            row is not None
            and row.identity_authoritative
            and "code_repair" in row.record_kinds
        )

    @staticmethod
    def _oracle_shaped(obj):
        """Whether the record carries the oracle-grounded schema.

        Registry authority is deliberately not part of this test: routing is
        decided by the payload's own schema, and ``natural_eligibility`` (which
        refuses a row that is not the sealed authority) makes the admit/refuse
        call. Gating the route on registry authority instead would let a
        schema-matching record fall through to the generic path, where it is
        counted eligible before any oracle invariant runs.
        """
        if __package__:
            from .oracle_grounded.record import SCHEMA_ID
        else:
            from oracle_grounded.record import SCHEMA_ID
        return isinstance(obj, dict) and obj.get("schema") == SCHEMA_ID

    def _observe_oracle(self, obj, where, factory, bucket):
        self._observe_admitted(_AdmissionRoute("oracle", obj, where, factory, bucket))

    def _observe_valid_record(self, obj, where, factory):
        bucket = self.factories[factory]
        if isinstance(obj, dict) and obj.get("family") == "python-function-repair":
            self._observe_code_repair(obj, where, factory, bucket)
            return
        if self._oracle_shaped(obj):
            self._observe_oracle(obj, where, factory, bucket)
            return
        self.totals["eligible_records"] += 1
        bucket["eligible_records"] += 1
        kind = self._observe_record(obj, where, factory)
        self.kinds[kind] += 1
        bucket["by_kind"][kind] += 1

    def _observe_code_repair(self, obj, where, factory, bucket):
        self._observe_admitted(_AdmissionRoute("code_repair", obj, where, factory, bucket))

    @staticmethod
    def _admission_lane(lane, obj):
        """The eligibility callable, error type, and record id of one lane."""
        if lane == "oracle":
            if __package__:
                from .oracle_grounded.admission import (
                    OracleAdmissionError as error_type,
                    natural_eligibility,
                )
            else:
                from oracle_grounded.admission import (
                    OracleAdmissionError as error_type,
                    natural_eligibility,
                )
            return natural_eligibility, error_type, obj.get("id")
        if __package__:
            from .code_repair.admission import natural_eligibility
            from .code_repair.source_policy import SourcePolicyError as error_type
        else:
            from code_repair.admission import natural_eligibility
            from code_repair.source_policy import SourcePolicyError as error_type
        return natural_eligibility, error_type, obj["id"]

    def _observe_admitted(self, route):
        """Shared accounting once a registry admission lane is chosen."""
        if __package__:
            from .curate_identity import default_registry
        else:
            from curate_identity import default_registry
        ledger, reason_counts = (
            (self.oracle, self.oracle_reasons)
            if route.lane == "oracle"
            else (self.code_repair, self.code_repair_reasons)
        )
        eligibility_of, error_type, checked_id = self._admission_lane(route.lane, route.obj)
        self.kinds[route.lane] += 1
        route.bucket["by_kind"][route.lane] += 1
        ledger["records"] += 1
        row = default_registry().by_path_id.get(route.factory)
        try:
            eligible, reasons = eligibility_of(route.obj, row)
        except error_type as exc:
            ledger["invalid_records"] += 1
            self.record_errors.append(f"{route.where}: {exc}")
            return
        self._observe_identity(route.obj, checked_id, route.where)
        self._observe_duplicate(route.obj, route.where)
        if not eligible:
            ledger["evidence_only_records"] += 1
            reason_counts.update(reasons)
            return
        ledger["eligible_records"] += 1
        self.totals["eligible_records"] += 1
        route.bucket["eligible_records"] += 1

    def _record_parse_error(self, where, exc, token_estimate, bucket):
        self._account_tokens(token_estimate, bucket)
        self.record_errors.append(f"{where}: JSON parse error: {exc}")
        self.kinds["unknown"] += 1
        bucket["by_kind"]["unknown"] += 1

    def _record_exact_json_contract_error(self, where, exc, token_estimate, bucket):
        self._account_tokens(token_estimate, bucket)
        self.totals["exact_json_contract_errors"] += 1
        bucket["exact_json_contract_errors"] += 1
        self.record_errors.append(f"{where}: exact JSON contract error: {exc}")
        self.kinds["exact_json_contract_error"] += 1
        bucket["by_kind"]["exact_json_contract_error"] += 1

    def _account_tokens(self, token_estimate, bucket):
        self.totals["approx_tokens"] += token_estimate
        bucket["approx_tokens"] += token_estimate
        bucket["record_tokens"].append(token_estimate)

    def _observe_record(self, obj, where, factory):
        errors, warnings, kind, checked_id = self.api.check_record(
            obj,
            where,
            factory_staging=self._strict_agentic(obj),
        )
        self.record_errors.extend(errors)
        self._observe_embedded_episodes(obj, kind, where)
        self._observe_warnings(warnings)
        self._observe_identity(obj, checked_id, where)
        self._observe_duplicate(obj, where)
        self._observe_provenance(obj, kind, where)
        self._observe_gates(obj, kind, where)
        self._observe_preference(obj, kind)
        self._observe_vocabulary(obj)
        self.distillation.observe(
            factory=factory,
            where=where,
            kind=kind,
            record=obj,
        )
        self._observe_agentic(obj, kind, where)
        return kind

    def _strict_agentic(self, obj):
        return self.api._record_audit.strict_agentic(obj, self.api.episode_like)

    def report(self):
        report = self.api.build_report(
            code_repair=self.code_repair,
            code_repair_reasons=self.code_repair_reasons,
            oracle=self.oracle,
            oracle_reasons=self.oracle_reasons,
            run_dir=self.run_dir,
            factories=self.factories,
            totals=self.totals,
            kinds=self.kinds,
            mill_mix=self.mill_mix,
            root_ids=self.root_ids,
            canonical_id_records=self.canonical_id_records,
            root_id_records=self.root_id_records,
            missing_ids=self.missing_ids,
            missing_root_ids=self.missing_root_ids,
            duplicate_ids=self.duplicate_ids,
            provenance=self.provenance,
            provenance_examples=self.provenance_examples,
            gate_by_role=self.gate_by_role,
            gate_errors=self.gate_errors,
            gate_error_examples=self.gate_error_examples,
            preference=self.preference,
            chosen_decisions=self.chosen_decisions,
            reward_keys=self.reward_keys,
            reward_shapes=self.reward_shapes,
            tags=self.tags,
            bridge=self.distillation.report(),
            episodes=self.episodes,
            hidden_thought_examples=self.hidden_thought_examples,
            exact_duplicates=self.exact_duplicates,
            record_errors=self.record_errors,
            unresolved_record_warnings=self.unresolved_record_warnings,
        )
        report["rights_manifest_sha256"] = self.rights_audit.manifest_sha256
        report["rights_compose_sha256"] = self.rights_audit.compose_sha256
        rights_blockers = self.rights_audit.blockers
        if rights_blockers:
            report["blockers"].extend(rights_blockers)
            report["training_ready"] = False
        return report


if __package__:
    _expose_package_sibling(__name__)
