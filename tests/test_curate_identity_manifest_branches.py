"""Pin the provenance-emission checks behind identity-manifest validation.

``curate_identity_manifest.validate_manifest_provenance`` proves that every
sealed provenance mapping targets an emitted owner whose payload carries the
canonical provenance it declares, that owner coverage is complete, and that the
targets match the source replay. Each case starts from a real curation result,
changes one property, re-seals the mappings, and asserts the refusal verbatim.
"""

from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any, NamedTuple

TESTS = Path(__file__).resolve().parent
for entry in (TESTS, TESTS.parent / "pipelines"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import curate_identity as identity
import curate_identity_checks as identity_checks
import curate_identity_evidence as evidence
import curate_identity_json as identity_json
import curate_identity_manifest as manifest
import curate_identity_provenance as provenance
from refusal_case_support import RefusalCaseAssertions

IdentityTreeError = manifest.IdentityTreeError
_THALAMIC = "thalamic-trajectory-factory"
_FFPC = "failure-as-fuel-preference-cascade"
_EPISODE = "agentic-coding-trajectory-factory"
_PROVENANCE_DEPS = provenance.ProvenanceDependencies(map_claim=provenance.map_claim)
_DEPS = evidence.ManifestDependencies(
    resolve_provenance=lambda owner, state: provenance.resolve_provenance(
        owner, state, _PROVENANCE_DEPS
    ),
    check_dependencies=lambda: None,
    strict_json_loads=identity_json.strict_json_loads,
    is_json_whitespace=identity_json._is_json_whitespace,
    canonical_json=identity_json.canonical_json,
    sha256_bytes=lambda payload: hashlib.sha256(payload).hexdigest(),
)
_WHERE = "IDENTITY-MANIFEST.json[0].provenance_mappings[0]"
_ITEM = "IDENTITY-MANIFEST.json[0]"


def _thalamic(claim: str, factory: str = _THALAMIC, record_id: str = "legacy") -> dict:
    return {
        "state": {"sim_or_real": claim, "episode_id": "legacy-episode", "domain": "fixture"},
        "proposed_action": {"action_type": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "bounded"},
        "executed_action": {"action_type": "noop"},
        "future_outcome": {"success": "full"},
        "reward_components": {"task": 1.0, "total": 1.0},
        "meta": {"id": record_id, "factory": factory, "round": 2},
    }


def _episode() -> dict:
    return {
        "goal": "repair a deterministic fixture",
        "steps": [
            {
                "decision_basis": "Observation: deterministic fixture is failing",
                "tool_call": {"name": "inspect", "args": {}},
                "observation": "failing",
            }
        ],
        "outcome": "fixed",
        "reward": {"success": True},
        "meta": {"factory": _EPISODE, "round": 2},
    }


def _pair() -> dict:
    return {
        "chosen": _thalamic("simulation", _FFPC, "chosen-old"),
        "rejected": _thalamic("high-fidelity simulation", _FFPC, "rejected-old"),
        "critique": "same context, better process",
        "meta": {"id": "pair-old", "factory": _FFPC},
    }


_FIXTURES = {
    "thalamic": (lambda: _thalamic("real"), f"{_THALAMIC}/batch-r02.jsonl", ["/"]),
    "episode": (_episode, f"{_EPISODE}/batch-r02.jsonl", ["/"]),
    "pair": (_pair, f"{_FFPC}/batch-r06.jsonl", ["/", "/chosen", "/rejected"]),
}


def _curated(fixture: str):
    build, path, owner_paths = _FIXTURES[fixture]
    result = identity.curate_record(identity.SourceRecord(build(), path, 1))
    return result, list(owner_paths)


def _reseal(mapping: dict, index: int) -> None:
    mappings = mapping["provenance_mappings"]
    mappings[index] = provenance.seal_provenance_mapping(mappings[index])


def _validate(fixture: str, mutate=None, *, owner_paths=None, replay=None):
    """Validate one mutated curation result; ``replay`` defaults to the original mapping.

    Mutations that change a provenance mapping re-seal it themselves, so only the
    digest cases reach the seal check.
    """

    result, default_owner_paths = _curated(fixture)
    mapping = copy.deepcopy(result.mapping)
    record = copy.deepcopy(result.record)
    if mutate is not None:
        mutate(mapping, record)
    expected = mapping if replay == "self" else result.mapping
    check = manifest.ProvenanceCheck(
        identity_checks.ManifestRecord(mapping, record, 0),
        result.mapping["record_kind"],
        owner_paths or default_owner_paths,
        expected,
    )
    manifest.validate_manifest_provenance(check, _DEPS)


def _tamper_mapping(index: int, key: str, value):
    """Change one sealed mapping field without re-sealing it."""

    def mutate(mapping, record):
        mapping["provenance_mappings"][index][key] = value

    return mutate


def _set_mapping(index: int, key: str, value):
    """Change one mapping field and re-seal the mapping."""

    def mutate(mapping, record):
        mapping["provenance_mappings"][index][key] = value
        _reseal(mapping, index)

    return mutate


def _set_record(path: tuple, value):
    def mutate(mapping, record):
        owner = record
        for part in path[:-1]:
            owner = owner[part]
        owner[path[-1]] = value

    return mutate


def _emit_root_canonical(index: int, canonical: dict, **changes):
    """Declare ``canonical`` on mapping ``index`` and emit it on the root owner."""

    def mutate(mapping, record):
        mapping["provenance_mappings"][index].update(canonical=dict(canonical), **changes)
        _reseal(mapping, index)
        record["provenance"] = dict(canonical)

    return mutate


def _replace_mappings(value):
    def mutate(mapping, record):
        mapping["provenance_mappings"] = value

    return mutate


def _repeat_first_mapping(mapping, record):
    mapping["provenance_mappings"].append(copy.deepcopy(mapping["provenance_mappings"][0]))


def _drop_chosen_mapping(mapping, record):
    mapping["provenance_mappings"].pop(0)


def _remove_root_provenance(mapping, record):
    record.pop("provenance")


_STATE_ORIGINAL_SIMULATED = {
    "sim_or_real": {"present": True, "value": "simulation"},
    "state_provenance": {"present": False, "value": None},
    "owner_provenance": {"present": False, "value": None},
}

_SEAL_AND_TARGET_REFUSALS = (
    ("mapping is not an object", _replace_mappings([["/"]]), f"{_WHERE} must be an object"),
    (
        "owner path is not text",
        _set_mapping(0, "owner_path", 3),
        f"{_WHERE}.owner_path does not name an emitted owner",
    ),
    (
        "owner path is not emitted",
        _set_mapping(0, "owner_path", "/meta"),
        f"{_WHERE}.owner_path does not name an emitted owner",
    ),
    (
        "state path is not text",
        _set_mapping(0, "state_path", 4),
        f"{_WHERE}.state_path must be a string",
    ),
    (
        "target repeats",
        _repeat_first_mapping,
        "IDENTITY-MANIFEST.json[0].provenance_mappings[1] repeats a provenance mapping target",
    ),
    (
        "basis is not text",
        _set_mapping(0, "basis", 1),
        f"{_WHERE}.basis must be a non-empty string",
    ),
    ("basis is empty", _set_mapping(0, "basis", ""), f"{_WHERE}.basis must be a non-empty string"),
    (
        "canonical is not an object",
        _set_mapping(0, "canonical", []),
        f"{_WHERE}.canonical must be a provenance object",
    ),
    (
        "canonical lacks a claim",
        _set_mapping(0, "canonical", {"kind": "designed"}),
        f"{_WHERE}.canonical must be a provenance object",
    ),
    (
        "unknown kind outside an aggregate",
        _set_mapping(0, "canonical", {"kind": "unknown", "claimed": "real"}),
        f"{_WHERE}.canonical.kind is invalid",
    ),
)

_STATE_EMISSION_REFUSALS = (
    (
        "state path names another container",
        _set_mapping(0, "state_path", "/meta"),
        f"{_WHERE}.state_path does not belong to owner_path",
    ),
    (
        "emitted state is not an object",
        _set_record(("state",), "state"),
        f"{_WHERE}.state_path must name an object",
    ),
    (
        "canonical differs from the state provenance",
        _set_mapping(0, "canonical", {"kind": "designed", "claimed": "other"}),
        f"{_WHERE}.canonical does not match emitted state provenance",
    ),
    (
        "owner claim differs",
        _set_record(("provenance", "claimed"), "other"),
        f"{_WHERE}.canonical does not match its emitted owner",
    ),
    (
        "owner provenance missing",
        _remove_root_provenance,
        f"{_WHERE}.canonical does not match its emitted owner",
    ),
    (
        "state claim kind differs",
        _set_record(("state", "sim_or_real"), "simulated"),
        f"{_WHERE}.canonical does not match its emitted owner",
    ),
    (
        "original resolves elsewhere",
        _set_mapping(0, "original", _STATE_ORIGINAL_SIMULATED),
        f"{_WHERE}.original does not resolve to its canonical provenance",
    ),
)

_PREFERENCE_SHAPE = {
    "kind": "designed",
    "claimed": None,
    "basis": "synthetic_factory_preference_shape",
}
_EPISODE_SHAPE_CLAIMED = {
    "kind": "designed",
    "claimed": "x",
    "basis": "synthetic_factory_episode_shape",
}

_OWNER_EMISSION_REFUSALS = (
    (
        "owner provenance differs",
        _set_record(("provenance", "claimed"), "x"),
        f"{_WHERE}.canonical does not match emitted owner provenance",
    ),
    (
        "basis differs from the canonical basis",
        _set_mapping(0, "basis", "synthetic_factory_preference_shape"),
        f"{_WHERE}.basis does not match canonical provenance",
    ),
    (
        "another kind's shape basis",
        _emit_root_canonical(0, _PREFERENCE_SHAPE, basis="synthetic_factory_preference_shape"),
        f"{_WHERE}.canonical does not match the shape contract",
    ),
    (
        "shape canonical claims something",
        _emit_root_canonical(0, _EPISODE_SHAPE_CLAIMED),
        f"{_WHERE}.canonical does not match the shape contract",
    ),
)


class _Refusal(NamedTuple):
    """One mutated curation result and the refusal it must raise."""

    label: str
    fixture: str
    mutate: Any
    message: str
    owner_paths: list | None = None
    replay: str | None = None


def _refusals(fixture: str, cases) -> tuple:
    return tuple(_Refusal(label, fixture, mutate, message) for label, mutate, message in cases)


_DIGEST_INVALID = f"{_WHERE} provenance mapping digest is invalid"
_DIGEST_REFUSALS = _refusals(
    "thalamic",
    (
        ("digest is not text", _tamper_mapping(0, "mapping_sha256", 5), _DIGEST_INVALID),
        (
            "digest is not lowercase hex",
            _tamper_mapping(0, "mapping_sha256", "A" * 64),
            _DIGEST_INVALID,
        ),
        ("digest is stale", _tamper_mapping(0, "basis", "other"), _DIGEST_INVALID),
    ),
)
_OWNER_PATH_SCALAR = _Refusal(
    "owner path names a scalar",
    "thalamic",
    _set_mapping(0, "owner_path", "/meta/round"),
    f"{_WHERE}.owner_path must name an object",
    owner_paths=["/", "/meta/round"],
)


def _validate_case(case: _Refusal) -> None:
    _validate(case.fixture, case.mutate, owner_paths=case.owner_paths, replay=case.replay)


class _RefusalAssertions(RefusalCaseAssertions):
    """Mixin: each ``_Refusal`` must raise exactly its message."""

    def _assert_refusals(self, refusals) -> None:
        rows = ((case.label, case, case.message) for case in refusals)
        self.assert_each_refuses(IdentityTreeError, _validate_case, rows)


class ManifestFieldRefusals(_RefusalAssertions, unittest.TestCase):
    def test_curated_results_validate_unchanged(self):
        for fixture in _FIXTURES:
            with self.subTest(fixture):
                self.assertIsNone(_validate(fixture))

    def test_seal_and_target_refusals(self):
        self._assert_refusals(
            (
                *_refusals("thalamic", _SEAL_AND_TARGET_REFUSALS),
                *_DIGEST_REFUSALS,
                _OWNER_PATH_SCALAR,
            )
        )

    def test_state_emission_refusals(self):
        self._assert_refusals(_refusals("thalamic", _STATE_EMISSION_REFUSALS))

    def test_owner_emission_refusals(self):
        self._assert_refusals(_refusals("episode", _OWNER_EMISSION_REFUSALS))


_NESTED_MISMATCH = "canonical does not match nested provenance"
_AGGREGATE_UNKNOWN = {"kind": "unknown", "claimed": ["simulation", "high-fidelity simulation"]}


def _chosen_as_aggregate_owner(mapping, record):
    chosen = mapping["provenance_mappings"][0]
    chosen.pop("state_path")
    chosen.update(
        basis="nested_trajectory_aggregate",
        original={"owner_provenance": {"present": False, "value": None}},
    )
    _reseal(mapping, 0)


_AGGREGATE_REFUSALS = _refusals(
    "pair",
    (
        (
            "aggregate claims one side",
            _emit_root_canonical(2, {"kind": "simulated", "claimed": "simulation"}),
            f"{_ITEM}.provenance_mappings[2].{_NESTED_MISMATCH}",
        ),
        (
            "aggregate declares an unknown kind",
            _emit_root_canonical(2, _AGGREGATE_UNKNOWN),
            f"{_ITEM}.provenance_mappings[2].{_NESTED_MISMATCH}",
        ),
        (
            "aggregate basis on a side owner",
            _chosen_as_aggregate_owner,
            f"{_WHERE}.{_NESTED_MISMATCH}",
        ),
    ),
)


class AggregateProvenanceRefusals(_RefusalAssertions, unittest.TestCase):
    def test_aggregate_must_match_the_nested_owners_at_the_root(self):
        self._assert_refusals(_AGGREGATE_REFUSALS)


_OWNER_STATE_BASIS = "state.sim_or_real"
_UNBOUND_CANONICAL = {"kind": "designed", "claimed": "real"}
_BOUND_CANONICAL = {**_UNBOUND_CANONICAL, "basis": _OWNER_STATE_BASIS}


def _add_root_owner_mapping(canonical: dict, *, basis: str = _OWNER_STATE_BASIS, keep_state=True):
    """Add a root owner mapping beside (or instead of) the thalamic state mapping."""

    def mutate(mapping, record):
        owner = provenance.seal_provenance_mapping(
            {
                "owner_path": "/",
                "basis": basis,
                "original": {"owner_provenance": {"present": False, "value": None}},
                "canonical": dict(canonical),
            }
        )
        kept = mapping["provenance_mappings"] if keep_state else []
        mapping["provenance_mappings"] = [*kept, owner]
        record["provenance"] = dict(canonical)

    return mutate


_NON_EMPTY = f"{_ITEM}.provenance_mappings must be a non-empty list"
_UNCOVERED = f"{_ITEM}.provenance_mappings owner paths do not match emitted provenance owners"
_COVERAGE_REFUSALS = (
    _Refusal("mappings are not a list", "thalamic", _replace_mappings({}), _NON_EMPTY),
    _Refusal("mappings are empty", "thalamic", _replace_mappings([]), _NON_EMPTY),
    _Refusal("a side owner is uncovered", "pair", _drop_chosen_mapping, _UNCOVERED),
    _Refusal("an extra emitted owner", "thalamic", None, _UNCOVERED, owner_paths=["/", "/state"]),
    _Refusal(
        "targets differ from the replay",
        "thalamic",
        _add_root_owner_mapping(_UNBOUND_CANONICAL),
        f"{_ITEM} provenance mapping targets do not match the hash-verified source replay",
    ),
)

_UNBOUND = f"{_ITEM} owner provenance basis is not bound to its original state resolution"
_BINDING_REFUSALS = (
    _Refusal(
        "canonical lacks the basis",
        "thalamic",
        _add_root_owner_mapping(_UNBOUND_CANONICAL),
        _UNBOUND,
        replay="self",
    ),
    _Refusal(
        "basis differs from the state",
        "thalamic",
        _add_root_owner_mapping({**_BOUND_CANONICAL, "basis": "owner.claim"}, basis="owner.claim"),
        _UNBOUND,
        replay="self",
    ),
    _Refusal(
        "state mapping absent",
        "thalamic",
        _add_root_owner_mapping(_BOUND_CANONICAL, keep_state=False),
        _UNBOUND,
        replay="self",
    ),
)


class ManifestCoverageAndReplay(_RefusalAssertions, unittest.TestCase):
    def test_coverage_and_replayed_target_refusals(self):
        self._assert_refusals(_COVERAGE_REFUSALS)

    def test_owner_basis_must_bind_to_its_state_resolution(self):
        self._assert_refusals(_BINDING_REFUSALS)

    def test_bound_owner_basis_validates(self):
        mutate = _add_root_owner_mapping(_BOUND_CANONICAL)
        self.assertIsNone(_validate("thalamic", mutate, replay="self"))

    def test_replayed_mapping_content_must_match(self):
        result, owner_paths = _curated("thalamic")
        replay = copy.deepcopy(result.mapping)
        replay["provenance_mappings"][0]["mapping_sha256"] = "0" * 64
        check = manifest.ProvenanceCheck(
            identity_checks.ManifestRecord(result.mapping, result.record, 0),
            "thalamic",
            owner_paths,
            replay,
        )
        with self.assertRaises(IdentityTreeError) as caught:
            manifest.validate_manifest_provenance(check, _DEPS)
        self.assertEqual(
            str(caught.exception),
            f"{_ITEM} provenance mapping for ('/', '/state') does not match the "
            "hash-verified source replay",
        )


def _replay(action: str, mapping: dict, record) -> SimpleNamespace:
    return SimpleNamespace(
        source=None, result=SimpleNamespace(action=action, mapping=mapping, record=record)
    )


class ManifestIdEarlyRefusals(unittest.TestCase):
    def setUp(self):
        result, _owner_paths = _curated("thalamic")
        self.mapping = result.mapping
        self.record = result.record

    def _refusal(self, item_mapping: dict, replay: SimpleNamespace) -> str:
        item = identity_checks.ManifestRecord(item_mapping, self.record, 0)
        with self.assertRaises(IdentityTreeError) as caught:
            manifest.validate_manifest_ids(item, None, replay, _DEPS)
        return str(caught.exception)

    def test_output_for_a_replayed_exclusion_is_refused(self):
        self.assertEqual(
            self._refusal(self.mapping, _replay("exclude", self.mapping, None)),
            f"{_ITEM} has output for a replayed exclusion",
        )

    def test_id_evidence_must_match_the_replay(self):
        cases = (
            ("original_ids", f"{_ITEM}.original_ids"),
            ("id_mappings", f"{_ITEM}.id_mappings"),
        )
        for field_name, where in cases:
            changed = {**self.mapping, field_name: []}
            with self.subTest(field_name):
                self.assertEqual(
                    self._refusal(changed, _replay("retained", self.mapping, self.record)),
                    f"{where} does not match the hash-verified source replay",
                )

    def test_preserved_kinds_must_replay_exactly(self):
        preserved = {**self.mapping, "record_kind": "fault_recovery"}
        self.assertEqual(
            self._refusal(self.mapping, _replay("retained", preserved, self.record)),
            "procedural identity mapping does not match the hash-verified source replay",
        )


if __name__ == "__main__":
    unittest.main()
