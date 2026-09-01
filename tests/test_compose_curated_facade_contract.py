#!/usr/bin/env python3
"""Historical API and patch-through contracts for ``compose_curated``."""

from __future__ import annotations

import inspect
import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
_ORIGINAL_SYS_PATH = list(sys.path)
compose_curated = importlib.import_module("pipelines.compose_curated")
export_hf = importlib.import_module("pipelines.export_hf")
sys.path[:] = _ORIGINAL_SYS_PATH


HISTORICAL_BINDINGS = set(
    """
    ACTION_EXCLUDED ACTION_NOT_APPLICABLE ACTION_RETAINED Any
    BRIDGE_ORDER_ERROR_FRAGMENT CODING_STEP_ERROR_RE COMPOSE_NAME COMPOSE_VERSION
    ComposeDecision ComposeError Counter FFPC_UNITS_MIGRATION LANE_ORDER
    MANIFEST_DIRNAME MANIFEST_FILENAME Mapping MutableMapping
    PREFERENCE_CANDIDATE_KEYS Path PinnedDestination REASON_DUPLICATE_CURATED_RECORD
    REASON_DUPLICATE_SOURCE_RECORD REASON_EMPTY_CORPUS
    REASON_IDENTITY_INVALID_PAYLOAD_SHAPE REASON_INVALID_JSON REASON_INVALID_UTF8
    REASON_MIXED_PREFERENCE_FAMILIES REASON_REWARD_ONTOLOGY
    REASON_TRAJECTORY_GATE_PASSED REASON_TRAJECTORY_GOAL_NORMALIZED
    REASON_TRAJECTORY_IDENTICAL REASON_TRAJECTORY_OUTCOME_MISSING
    REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT REASON_TRAJECTORY_PREFIX_ABSENT
    REASON_TRAJECTORY_REWARD_MISSING REASON_TRAJECTORY_REWARD_NOT_DIVERGENT
    REASON_TRAJECTORY_SIDE_INVALID REASON_TRAJECTORY_STEPS_EMPTY
    REASON_TRAJECTORY_STEPS_INVALID RECORDS_DIRNAME REWARD_SIDECAR_FILENAME
    SUMMARY_FILENAME TRAJECTORY_GOAL_LOCATIONS TransactionError _ComposeRunState
    _PIPELINES _PROBE_FAILED _TRAJECTORY_DIVERGENCE_FIELDS
    _TrajectoryPreferenceDecision __all__ _append_coding_lane_stage
    _assert_descriptor_contained _assert_destination_disjoint _assert_new_destination
    _assert_opened_source_identity _assert_source_path_unchanged
    _assert_unaliased_regular_member _audit_records
    _authenticate_composed_artifacts _bridge_order_repaired_copy
    _bridge_view_trajectory _calibration_id_candidates _canonical_sha256
    _capture_source_snapshot _captured_source_payloads _claim_output_id
    _coding_lane_curator _coding_steps_repaired_copy _collect_source_directory
    _commit_compose_summary _compat_trajectory_preference _compose_bridge_stage
    _compose_bridge_view_coding _compose_coding_stage _compose_episode_preference
    _compose_identity_stage _compose_legacy_preference
    _compose_mixed_family_preference_exclusion _compose_one_line
    _compose_preferences_stage _compose_rewards_stage _compose_run_summary
    _compose_same_state_preference _compose_source_file
    _container_calibration_id_candidates _contains_raw_segments
    _create_pinned_new_directory _curate_trajectory_sides
    _deduplicate_curated_record _deferred_lane_repair _destination_write_parts
    _directory_binding_matches _directory_identity _discard_created_destination
    _drain_descriptor _excluded_source_line _hidden_only_curation_applies
    _identity_owner _identity_retry _identity_stage_detail_of
    _identity_stage_evidence _is_bridge_order_only_rejection
    _is_coding_step_only_rejection _is_same_state_pair _is_under_raw
    _json_pointer_tokens _jsonl_physical_lines _load_calibration
    _mapped_legacy_id_paths _mixed_preference_families _new_manifest_entry
    _normalize_trajectory_goal_whitespace _open_pinned_child
    _open_pinned_child_directory _original_id_paths
    _owner_calibration_id_candidates _parse_finite_json_float _pinned_root_path
    _pop_json_pointer _post_transform_semantic_sha256 _present_trajectory_goals
    _read_exact_child_file _read_exact_regular_file _read_pinned_child_bytes
    _record_excluded_line _record_retained_line _refuse_existing_destination
    _reject_duplicate_object_keys _require_exact_directory _scan_source_directory
    _semantic_identity_owners _side_curation_failed_decision
    _source_entry_metadata _source_member_path _source_preference_shape
    _source_snapshot_identities _stable_file_identity _stage _strip_assigned_ids
    _strip_hidden_only_side _strip_provenance_labels _strip_sidecar_binding
    _trajectory_divergence_reasons _trajectory_gate_passed _trajectory_goal_owner
    _trajectory_preference _trajectory_side_needs_coding
    _trajectory_side_validation_errors _trajectory_step_reasons
    _validated_member_relative _verify_directory_binding _verify_pinned_child
    _whitespace_only_goal _write_compose_provenance _write_emitted_records
    _write_new_text argparse calibration_for canonical_json compact_audit_report
    compose_mill compose_record compose_run compose_source_line contextlib copy
    create_pinned_destination curate_agentic curate_bridge curate_coding
    curate_identity curate_preferences curate_rewards curate_trajectory_preferences
    dataclass factory_identity_for_path field is_bridge_record is_episode_record
    is_preference_record json jsonl_physical_lines main
    mill_quarantined_decision os parse_args preference_side_kinds re
    reject_json_constant sha256_hex source_jsonl_members sys training_audit
    transform_contract write_pinned_new_bytes
    """.split()
)


HISTORICAL_SIGNATURES = dict(
    line.strip().split("\t", 1)
    for line in """
    _append_coding_lane_stage\t(stages: 'list[dict[str, Any]]', module: 'Any', curated: 'Any', manifest: 'Mapping[str, Any]') -> "'ComposeDecision | Any'"
    _audit_records\t(records_dir: 'Path', record_count: 'int') -> 'dict[str, Any]'
    _authenticate_composed_artifacts\t(pinned_destination: 'PinnedDestination', expected_digests: 'Mapping[str, str]') -> 'None'
    _bridge_order_repaired_copy\t(record: 'Mapping[str, Any]', *, source_path: 'str', source_line: 'int', source_sha256: 'str') -> 'dict[str, Any] | None'
    _bridge_view_trajectory\t(record: 'Mapping[str, Any]') -> 'dict[str, Any] | None'
    _calibration_id_candidates\t(record: 'Mapping[str, Any]')
    _capture_source_snapshot\t(resolved_source: 'Path') -> 'tuple[tuple[str, ...], dict[str, bytes], dict[str, tuple[str, bool]]]'
    _captured_source_payloads\t(resolved_source: 'Path', source_members: 'tuple[str, ...]') -> 'dict[str, bytes]'
    _claim_output_id\t(state: '_ComposeRunState', output_id: 'Any', location: 'str') -> 'None'
    _coding_lane_curator\t(current: 'dict[str, Any]', registered_kind: 'Any') -> 'Any'
    _coding_steps_repaired_copy\t(record: 'Mapping[str, Any]', *, source_path: 'str', source_line: 'int', source_sha256: 'str') -> 'dict[str, Any] | None'
    _commit_compose_summary\t(state: '_ComposeRunState', pinned_destination: 'PinnedDestination', summary: 'Mapping[str, Any]', manifest_sha256: 'str', sidecar_sha256: 'str') -> 'None'
    _compose_bridge_stage\t(current: 'dict[str, Any]', stages: 'list[dict[str, Any]]', *, source_path: 'str', source_line: 'int', source_sha256: 'str', source_file_sha256: 'str | None') -> "'ComposeDecision | dict[str, Any]'"
    _compose_bridge_view_coding\t(current: 'dict[str, Any]', trajectory: 'dict[str, Any]', stages: 'list[dict[str, Any]]', *, source_path: 'str', source_line: 'int') -> "'ComposeDecision | dict[str, Any]'"
    _compose_coding_stage\t(current: 'dict[str, Any]', registered_kind: 'Any', stages: 'list[dict[str, Any]]', *, source_path: 'str', source_line: 'int', source_sha256: 'str') -> "'ComposeDecision | dict[str, Any]'"
    _compose_episode_preference\t(current: 'dict[str, Any]', side_kinds: 'tuple[str, str]', stages: 'list[dict[str, Any]]', *, source_path: 'str', source_line: 'int') -> "'ComposeDecision | tuple[Any, list[str]]'"
    _compose_identity_stage\t(record: 'Any', stages: 'list[dict[str, Any]]', *, source_path: 'str', source_line: 'int', source_sha256: 'str') -> "'ComposeDecision | tuple[dict[str, Any], Any]'"
    _compose_legacy_preference\t(current: 'dict[str, Any]', side_kinds: 'tuple[str, str]', stages: 'list[dict[str, Any]]') -> 'tuple[Any, list[str]]'
    _compose_mixed_family_preference_exclusion\t(side_kinds: 'tuple[str, str]', stages: 'list[dict[str, Any]]') -> 'ComposeDecision'
    _compose_one_line\t(state: '_ComposeRunState', physical_line: 'bytes', *, relative: 'Any', line_number: 'int', source_file_sha256: 'str', catalog: 'Mapping[str, Any] | None', emitted: 'list[str]', mill_findings: 'Mapping[tuple[str, int], Any] | None' = None) -> 'None'
    _compose_preferences_stage\t(current: 'dict[str, Any]', stages: 'list[dict[str, Any]]', *, source_path: 'str', source_line: 'int') -> "'ComposeDecision | dict[str, Any]'"
    _compose_rewards_stage\t(current: 'dict[str, Any]', stages: 'list[dict[str, Any]]', *, source_path: 'str', source_line: 'int', calibration: 'Any') -> "'ComposeDecision | tuple[dict[str, Any], dict[str, Any] | None]'"
    _compose_run_summary\t(state: '_ComposeRunState', *, resolved_source: 'Path', destination_path: 'Path', calibration_descriptor: 'Any', calibrated_records: 'int', manifest_sha256: 'str', sidecar_sha256: 'str', records_dir: 'Path') -> 'dict[str, Any]'
    _compose_same_state_preference\t(current: 'dict[str, Any]', side_kinds: 'tuple[str, str]', stages: 'list[dict[str, Any]]', *, source_path: 'str', source_line: 'int') -> "'ComposeDecision | tuple[Any, list[str]]'"
    _compose_source_file\t(state: '_ComposeRunState', *, relative: 'Any', raw_file: 'bytes', destination_target: 'int | PinnedDestination', catalog: 'Mapping[str, Any] | None', mill_findings: 'Mapping[tuple[str, int], Any] | None' = None) -> 'None'
    _container_calibration_id_candidates\t(container: 'Mapping[str, Any]')
    _deduplicate_curated_record\t(decision: 'ComposeDecision', *, source_path: 'str', source_line: 'int', seen_curated_semantics: 'MutableMapping[str, tuple[str, int]] | None') -> 'ComposeDecision'
    _deferred_lane_repair\t(record: 'Any', identity_result: 'Any', *, source_path: 'str', source_line: 'int', source_sha256: 'str') -> 'tuple[Any, str | None]'
    _excluded_source_line\t(reason: 'str', detail: 'dict[str, Any]') -> 'ComposeDecision'
    _hidden_only_curation_applies\t(current: 'dict[str, Any]', registered_kind: 'Any') -> 'bool'
    _identity_owner\t(record: 'dict[str, Any]', pointer: 'Any') -> 'dict[str, Any] | None'
    _identity_retry\t(repaired: 'dict[str, Any] | None', *, source_path: 'str', source_line: 'int', source_sha256: 'str')
    _identity_stage_detail_of\t(decision: 'ComposeDecision') -> 'dict[str, Any] | None'
    _identity_stage_evidence\t(identity_result: 'Any', deferred_lane: 'str | None', source_side_kinds: 'Any', mixed_preference_families: 'bool') -> 'tuple[list[str], dict[str, Any]]'
    _is_bridge_order_only_rejection\t(mapping: 'Mapping[str, Any]') -> 'bool'
    _is_coding_step_only_rejection\t(mapping: 'Mapping[str, Any]') -> 'bool'
    _json_pointer_tokens\t(pointer: 'Any') -> 'list[str] | None'
    _jsonl_physical_lines\t(raw_file: 'bytes') -> 'list[bytes]'
    _load_calibration\t(source_run: 'Path', units_migration: 'Path | None') -> 'tuple[dict[str, Any], dict[str, Any]]'
    _mapped_legacy_id_paths\t(detail: 'Mapping[str, Any] | None') -> 'tuple[str, ...]'
    _new_manifest_entry\t(relative: 'Any', line_number: 'int', source_sha256: 'str', source_file_sha256: 'str') -> 'dict[str, Any]'
    _original_id_paths\t(originals: 'Any') -> 'list[str]'
    _owner_calibration_id_candidates\t(owner: 'Mapping[str, Any]')
    _pop_json_pointer\t(record: 'dict[str, Any]', pointer: 'Any') -> 'None'
    _post_transform_semantic_sha256\t(decision: 'ComposeDecision') -> 'str'
    _record_excluded_line\t(state: '_ComposeRunState', decision: 'ComposeDecision', entry: 'dict[str, Any]') -> 'None'
    _record_retained_line\t(state: '_ComposeRunState', decision: 'ComposeDecision', entry: 'dict[str, Any]', *, relative: 'Any', location: 'str', emitted: 'list[str]') -> 'None'
    _semantic_identity_owners\t(record: 'dict[str, Any]') -> 'list[dict[str, Any]]'
    _side_curation_failed_decision\t(stages: 'list[dict[str, Any]]', side_curation: 'dict[str, dict[str, Any]]', side_curation_reasons: 'list[str]', side_curation_changed: 'bool', *, side_kinds: 'tuple[str, str]', classification: 'str', **stage_extra: 'Any') -> 'ComposeDecision'
    _source_preference_shape\t(record: 'Any') -> 'tuple[Any, bool]'
    _source_snapshot_identities\t(resolved_source: 'Path', source_members: 'tuple[str, ...]') -> 'dict[str, tuple[tuple[int, ...], str, bool]]'
    _stage\t(lane: 'str', name: 'str', version: 'str', action: 'str', **extra: 'Any') -> 'dict[str, Any]'
    _strip_assigned_ids\t(semantic: 'dict[str, Any]', detail: 'dict[str, Any] | None') -> 'None'
    _strip_provenance_labels\t(semantic: 'dict[str, Any]') -> 'None'
    _strip_sidecar_binding\t(semantic: 'dict[str, Any]') -> 'None'
    _trajectory_preference\t(record: 'dict[str, Any]') -> 'tuple[Any, str, str, str]'
    _write_compose_provenance\t(state: '_ComposeRunState', destination_target: 'int | PinnedDestination') -> 'tuple[str, str]'
    _write_emitted_records\t(state: '_ComposeRunState', destination_target: 'int | PinnedDestination', relative: 'Any', emitted: 'list[str]') -> 'None'
    calibration_for\t(record: 'Mapping[str, Any]', catalog: 'Mapping[str, Any] | None') -> 'Any'
    compact_audit_report\t(report: 'Mapping[str, Any] | None', record_count: 'int') -> 'dict[str, Any]'
    compose_record\t(record: 'Any', *, source_path: 'str', source_line: 'int', source_sha256: 'str', source_file_sha256: 'str | None' = None, calibration: 'Any' = None) -> 'ComposeDecision'
    compose_run\t(source_run: 'str | Path', destination: 'str | Path', *, units_migration: 'str | Path | None' = None) -> 'dict[str, Any]'
    compose_source_line\t(physical_line: 'bytes', *, source_path: 'str', source_line: 'int', source_file_sha256: 'str', calibration_catalog: 'Mapping[str, Any] | None' = None, seen_source_semantics: 'MutableMapping[str, tuple[str, int]] | None' = None, seen_curated_semantics: 'MutableMapping[str, tuple[str, int]] | None' = None) -> 'ComposeDecision'
    jsonl_physical_lines\t(raw_file: 'bytes') -> 'list[bytes]'
    main\t(argv: 'list[str] | None' = None) -> 'int'
    mill_quarantined_decision\t(finding: 'Any') -> 'ComposeDecision'
    parse_args\t(argv: 'list[str] | None' = None) -> 'argparse.Namespace'
    transform_contract\t() -> 'dict[str, Any]'
    """.strip().splitlines()
)


class FacadeSentinel(RuntimeError):
    """A patched historical seam reached through the current facade."""


class ComposeCuratedFacadeContract(unittest.TestCase):
    def _assert_facade_seam(self, binding, message, invocation):
        with mock.patch.object(
            compose_curated,
            binding,
            side_effect=FacadeSentinel(message),
        ):
            with self.assertRaisesRegex(FacadeSentinel, message):
                invocation()

    def test_the_complete_historical_module_surface_is_restored(self):
        missing = sorted(HISTORICAL_BINDINGS - set(vars(compose_curated)))
        self.assertEqual(missing, [])

    def test_every_historical_callable_signature_is_restored(self):
        for name, expected in HISTORICAL_SIGNATURES.items():
            with self.subTest(name=name):
                self.assertEqual(
                    str(inspect.signature(getattr(compose_curated, name))),
                    expected,
                )

        self.assertEqual(
            str(inspect.signature(export_hf.export_run)),
            "(curated_root: 'str | Path', destination: 'str | Path', *, "
            "eval_fraction: 'float' = 0.1, split_salt: 'str' = "
            "'spikenaut.synthetic-factory.split-v1', dataset_name: 'str | None' = None) "
            "-> 'dict[str, Any]'",
        )

    def test_public_calls_use_python_native_binding_diagnostics(self):
        cases = (
            (
                compose_curated.compose_record,
                ({},),
                {},
                "compose_record() missing 3 required keyword-only arguments: "
                "'source_path', 'source_line', and 'source_sha256'",
            ),
            (
                compose_curated.compose_source_line,
                (b"{}",),
                {},
                "compose_source_line() missing 3 required keyword-only arguments: "
                "'source_path', 'source_line', and 'source_file_sha256'",
            ),
            (
                compose_curated.compose_run,
                ("source", "destination"),
                {"unexpected": True},
                "compose_run() got an unexpected keyword argument 'unexpected'",
            ),
            (
                export_hf.export_run,
                ("source", "destination", None),
                {},
                "export_run() takes 2 positional arguments but 3 were given",
            ),
        )
        for function, positional, named, expected in cases:
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError) as raised:
                    function(*positional, **named)
                self.assertEqual(str(raised.exception), expected)

    def test_facade_seams_are_resolved_at_call_time(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = compose_curated._ComposeRunState()
            cases = (
                (
                    "_compose_identity_stage",
                    "identity stage",
                    lambda: compose_curated.compose_record(
                        {},
                        source_path="batch.jsonl",
                        source_line=1,
                        source_sha256="a" * 64,
                    ),
                ),
                (
                    "compose_record",
                    "record composer",
                    lambda: compose_curated.compose_source_line(
                        b"{}",
                        source_path="batch.jsonl",
                        source_line=1,
                        source_file_sha256="b" * 64,
                    ),
                ),
                (
                    "_new_manifest_entry",
                    "manifest builder",
                    lambda: compose_curated._compose_one_line(
                        state,
                        b"{}",
                        relative="batch.jsonl",
                        line_number=1,
                        source_file_sha256="c" * 64,
                        catalog=None,
                        emitted=[],
                    ),
                ),
                (
                    "_capture_source_snapshot",
                    "snapshot capture",
                    lambda: compose_curated.compose_run(
                        root, root / "destination"
                    ),
                ),
            )
            for binding, message, invocation in cases:
                with self.subTest(binding=binding):
                    self._assert_facade_seam(binding, message, invocation)

    def test_source_line_helpers_resolve_through_the_facade(self):
        cases = (
            (
                "_calibration_id_candidates",
                "calibration candidates",
                lambda: compose_curated.compose_source_line(
                    b"{}",
                    source_path="batch.jsonl",
                    source_line=1,
                    source_file_sha256="d" * 64,
                    calibration_catalog={"sentinel": object()},
                ),
            ),
            (
                "_excluded_source_line",
                "source exclusion",
                lambda: compose_curated.compose_source_line(
                    b"\xff",
                    source_path="batch.jsonl",
                    source_line=1,
                    source_file_sha256="f" * 64,
                ),
            ),
        )
        for binding, message, invocation in cases:
            with self.subTest(binding=binding):
                self._assert_facade_seam(binding, message, invocation)

    def test_coding_lane_curator_resolves_through_the_facade(self):
        def passthrough(current, *_args, **_kwargs):
            return current

        with (
            mock.patch.object(
                compose_curated,
                "_compose_identity_stage",
                return_value=({}, None),
            ),
            mock.patch.object(
                compose_curated,
                "_compose_bridge_stage",
                side_effect=passthrough,
            ),
            mock.patch.object(
                compose_curated,
                "_compose_preferences_stage",
                side_effect=passthrough,
            ),
            mock.patch.object(
                compose_curated,
                "_coding_lane_curator",
                side_effect=FacadeSentinel("coding curator"),
            ),
        ):
            with self.assertRaisesRegex(FacadeSentinel, "coding curator"):
                compose_curated.compose_record(
                    {},
                    source_path="batch.jsonl",
                    source_line=1,
                    source_sha256="e" * 64,
                )

    def test_dedup_identity_helpers_resolve_through_the_facade(self):
        decision = compose_curated.ComposeDecision(
            compose_curated.ACTION_RETAINED,
            {"id": "record"},
            (),
            ({"lane": "identity", "detail": {}},),
            None,
            "record",
        )
        with mock.patch.object(
            compose_curated,
            "_identity_stage_detail_of",
            side_effect=FacadeSentinel("identity detail"),
        ):
            with self.assertRaisesRegex(FacadeSentinel, "identity detail"):
                compose_curated._deduplicate_curated_record(
                    decision,
                    source_path="batch.jsonl",
                    source_line=1,
                    seen_curated_semantics={},
                )

    @staticmethod
    def _restored_helper_graph_cases(retained):
        return (
            (
                "_container_calibration_id_candidates",
                "calibration container",
                lambda: list(compose_curated._owner_calibration_id_candidates({})),
            ),
            (
                "_identity_owner",
                "identity owner",
                lambda: compose_curated._strip_assigned_ids(
                    {"nested": {"id": "record"}},
                    {
                        "id_mappings": [
                            {"owner_path": "/nested", "output_id": "record"}
                        ]
                    },
                ),
            ),
            (
                "_json_pointer_tokens",
                "pointer tokens",
                lambda: compose_curated._pop_json_pointer({}, "/id"),
            ),
            (
                "_original_id_paths",
                "original id paths",
                lambda: compose_curated._mapped_legacy_id_paths({}),
            ),
            (
                "_semantic_identity_owners",
                "semantic owners",
                lambda: compose_curated._strip_provenance_labels({}),
            ),
            (
                "_strip_assigned_ids",
                "assigned ids",
                lambda: compose_curated._post_transform_semantic_sha256(retained),
            ),
        )

    def test_restored_helper_graph_uses_live_facade_nodes(self):
        retained = compose_curated.ComposeDecision(
            compose_curated.ACTION_RETAINED,
            {"id": "record"},
            (),
            ({"lane": "identity", "detail": {}},),
            None,
            "record",
        )
        cases = self._restored_helper_graph_cases(retained)
        for binding, message, invocation in cases:
            with self.subTest(binding=binding):
                self._assert_facade_seam(binding, message, invocation)

    def test_preference_dispatch_uses_the_live_facade_branch(self):
        with (
            mock.patch.object(compose_curated, "is_preference_record", return_value=True),
            mock.patch.object(
                compose_curated,
                "preference_side_kinds",
                return_value=("thalamic", "thalamic"),
            ),
            mock.patch.object(compose_curated, "_is_same_state_pair", return_value=True),
            mock.patch.object(
                compose_curated,
                "_compose_same_state_preference",
                side_effect=FacadeSentinel("same-state branch"),
            ),
        ):
            with self.assertRaisesRegex(FacadeSentinel, "same-state branch"):
                compose_curated._compose_preferences_stage(
                    {}, [], source_path="batch.jsonl", source_line=1
                )

    def test_bridge_coding_dispatch_uses_the_live_facade_helper(self):
        with (
            mock.patch.object(
                compose_curated, "_coding_lane_curator", return_value=None
            ),
            mock.patch.object(compose_curated, "is_bridge_record", return_value=True),
            mock.patch.object(
                compose_curated,
                "_bridge_view_trajectory",
                side_effect=FacadeSentinel("bridge trajectory"),
            ),
        ):
            with self.assertRaisesRegex(FacadeSentinel, "bridge trajectory"):
                compose_curated._compose_coding_stage(
                    {},
                    None,
                    [],
                    source_path="batch.jsonl",
                    source_line=1,
                    source_sha256="0" * 64,
                )

    def test_run_helpers_use_the_live_facade_graph(self):
        class Finding:
            reason_codes = ("foreign_mill",)

            @staticmethod
            def as_dict():
                return {"classification": "foreign_mill"}

        cases = (
            (
                "compact_audit_report",
                "compact audit",
                lambda: compose_curated._audit_records(Path("."), 0),
            ),
            (
                "_jsonl_physical_lines",
                "physical lines",
                lambda: compose_curated.jsonl_physical_lines(b"{}\n"),
            ),
            (
                "_stage",
                "mill stage",
                lambda: compose_curated.mill_quarantined_decision(Finding()),
            ),
            (
                "parse_args",
                "CLI parser",
                lambda: compose_curated.main(["missing", "destination"]),
            ),
        )
        for binding, message, invocation in cases:
            with self.subTest(binding=binding):
                self._assert_facade_seam(binding, message, invocation)


if __name__ == "__main__":
    unittest.main()
