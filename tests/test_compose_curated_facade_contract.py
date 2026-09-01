#!/usr/bin/env python3
"""Historical API and patch-through contracts for ``compose_curated``."""

from __future__ import annotations

import inspect
import importlib
import sys
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest import mock

if __package__:
    from .compose_curated_facade_contract_data import (
        BASE_ALL,
        BASE_COMPATIBILITY_EXPORTS,
        HISTORICAL_BINDINGS,
        HISTORICAL_SIGNATURES,
    )
else:
    from compose_curated_facade_contract_data import (
        BASE_ALL,
        BASE_COMPATIBILITY_EXPORTS,
        HISTORICAL_BINDINGS,
        HISTORICAL_SIGNATURES,
    )


REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
_ORIGINAL_SYS_PATH = list(sys.path)
compose_curated = importlib.import_module("pipelines.compose_curated")
export_hf = importlib.import_module("pipelines.export_hf")
sys.path[:] = _ORIGINAL_SYS_PATH


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

    def test_all_and_compatibility_exports_match_the_base_exactly(self):
        self.assertEqual(compose_curated.__all__, BASE_ALL)
        expected = tuple(getattr(compose_curated, name) for name in BASE_COMPATIBILITY_EXPORTS)
        self.assertEqual(compose_curated._COMPATIBILITY_EXPORTS, expected)

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

    def test_historical_implementation_bindings_interpose_at_call_time(self):
        cases = (
            (
                "_compose_record_impl",
                lambda: compose_curated.compose_record(
                    {},
                    source_path="factory/batch.jsonl",
                    source_line=1,
                    source_sha256="a" * 64,
                ),
            ),
            (
                "_compose_source_line_impl",
                lambda: compose_curated.compose_source_line(
                    b"{}",
                    source_path="factory/batch.jsonl",
                    source_line=1,
                    source_file_sha256="b" * 64,
                ),
            ),
            (
                "_compose_record_from_context",
                lambda: compose_curated.compose_source_line(
                    b"{}",
                    source_path="factory/batch.jsonl",
                    source_line=1,
                    source_file_sha256="c" * 64,
                ),
            ),
            (
                "_only_identity_shape_details",
                lambda: compose_curated._is_bridge_order_only_rejection({}),
            ),
        )
        for binding, invocation in cases:
            with self.subTest(binding=binding):
                self._assert_facade_seam(binding, f"live {binding}", invocation)

    def test_nested_preference_and_coding_helpers_use_live_facade_nodes(self):
        def side_failure():
            return compose_curated._compose_same_state_preference(
                {}, ("thalamic", "thalamic"), [], source_path="batch.jsonl", source_line=1
            )

        def episode():
            return compose_curated._compose_episode_preference(
                {}, ("episode", "episode"), [], source_path="batch.jsonl", source_line=1
            )

        def append_stage():
            return compose_curated._append_coding_lane_stage(
                [], compose_curated.curate_coding, {}, {"action": "retained"}
            )

        def bridge_hidden():
            return compose_curated._compose_bridge_view_coding(
                {"language_view": {"trajectory": {"inner_monologue": "secret"}}},
                {"inner_monologue": "secret"},
                [],
                source_path="batch.jsonl",
                source_line=1,
            )

        cases = (
            ("_side_curation_failed_decision", side_failure, (None, {}, [], False)),
            ("_trajectory_preference", episode, ({}, {}, [], False)),
            ("_stage", append_stage, None),
            ("_strip_hidden_only_side", bridge_hidden, None),
        )
        for binding, invocation, side_result in cases:
            with self.subTest(binding=binding):
                side_patch = (
                    mock.patch.object(
                        compose_curated,
                        "_curate_trajectory_sides",
                        return_value=side_result,
                    )
                    if side_result is not None
                    else nullcontext()
                )
                with side_patch:
                    self._assert_facade_seam(binding, f"nested {binding}", invocation)

        coding_binding = mock.Mock()
        coding_binding.steps_path.side_effect = FacadeSentinel("coding binding")
        with mock.patch.object(compose_curated, "curate_coding", coding_binding):
            with self.assertRaisesRegex(FacadeSentinel, "coding binding"):
                bridge_hidden()

    def test_side_curation_evidence_rejects_duplicate_keyword_overrides(self):
        reason = compose_curated.REASON_TRAJECTORY_SIDE_INVALID
        with self.assertRaisesRegex(
            TypeError, "multiple values for keyword argument 'reason_codes'"
        ):
            compose_curated._side_curation_failed_decision(
                [],
                {},
                ["side_invalid"],
                False,
                side_kinds=("episode", "episode"),
                classification="side_failure",
                reason_codes=["overwritten"],
            )
        decision = compose_curated._side_curation_failed_decision(
            [],
            {},
            [reason, "side_invalid", "side_invalid"],
            False,
            side_kinds=("episode", "episode"),
            classification="side_failure",
        )
        self.assertEqual(decision.reason_codes, (reason, "side_invalid"))
        self.assertEqual(tuple(decision.stages[-1]["reason_codes"]), decision.reason_codes)

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
                    lambda: compose_curated.compose_run(root, root / "destination"),
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
                    {"id_mappings": [{"owner_path": "/nested", "output_id": "record"}]},
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
            mock.patch.object(compose_curated, "_coding_lane_curator", return_value=None),
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
