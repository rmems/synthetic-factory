#!/usr/bin/env python3
"""Pin the payload-kind finding for rmems/multi-agent-ouroboros-swarm.

Issue #75 reports PAYLOAD_KIND_MISMATCH: the public card advertises
multi-agent swarm trajectories, but every published JSONL row is a
thalamic-gate wrap (``state`` / ``proposed_action`` / ``safety_decision`` /
``executed_action`` / ``future_outcome`` / ``reward_components`` / ``meta``).

The dataset is a Fable-5 Hub repository.  Its card is maintained outside this
repository and its raw tree (``outputs/raw/``) is gitignored, so this module
splits the evidence in two:

``CommittedCensusContract``
    Always runs.  It checks the committed census artifact against itself and
    against the release verifier, so the finding stays pinned in a checkout
    that has no raw tree.  This is what keeps CI honest.

``RawCorpusCensusFidelity``
    Runs only where the gitignored raw tree exists.  It re-derives the census
    from first principles and requires an exact match, so the committed
    artifact can never silently drift from the payload it describes.
"""

import hashlib
import json
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
CENSUS_PATH = DOCS / "ouroboros-swarm-payload-kind.json"
ANALYSIS_PATH = DOCS / "ouroboros-swarm-payload-kind.md"
CARD_PATH = DOCS / "ouroboros-swarm-payload-kind.card.md"
RAW_SWARM = REPO / "outputs" / "raw" / "2026-08-17" / "multi-agent-ouroboros-swarm"
DATASET_REPO = "rmems/multi-agent-ouroboros-swarm"

sys.path.insert(0, str(REPO / "pipelines"))
import verify_hf_release  # noqa: E402

# The seven top-level keys shared by every thalamic-gate wrap, as published by
# rmems/thalamic-relay-trajectories and by the 16 gate rows on
# rmems/agentic-coding-trajectories.
GATE_WRAP_KEYS = (
    "executed_action",
    "future_outcome",
    "meta",
    "proposed_action",
    "reward_components",
    "safety_decision",
    "state",
)

# Structural entries mixed into the published ``state.agents`` mappings.  They
# describe the coordination protocol, not participants.
AGENT_METADATA_KEYS = frozenset({"protocol", "quorum_rule"})

# A swarm trajectory is a content-bearing exchange between distinct actors,
# not merely a record that happens to carry a key such as ``task`` or
# ``agents``.  Search these recognized dialogue containers recursively so a
# real exchange inside ``state.multi_agent`` or another envelope is found.
SWARM_TURN_CONTAINER_KEYS = frozenset(
    {"conversation", "messages", "transcript", "turns"}
)
TURN_ACTOR_KEYS = ("agent", "agent_id", "author", "from", "role", "sender", "speaker")
TURN_CONTENT_KEYS = ("content", "message", "text", "utterance")
SWARM_TRAJECTORY_DEFINITION = (
    "a recursively discovered conversation/messages/transcript/turns array "
    "with at least two content-bearing turns from distinct actors"
)

# ``state`` sub-keys that carry a multi-actor scenario framing.  Their presence
# does not make a record a swarm trajectory -- the record is still one gate
# adjudication -- but it is the honest half of the card's multi-agent claim.
MULTI_ACTOR_STATE_KEYS = ("agents", "fleet", "multi_agent", "orchestrator")


def _agent_ids(agents):
    """Return sorted participant ids for whichever shape ``agents`` uses."""

    if isinstance(agents, dict):
        return sorted(
            identifier
            for identifier in agents
            if identifier.casefold().replace("-", "_").replace(" ", "_")
            not in AGENT_METADATA_KEYS
        )
    if isinstance(agents, list):
        ids = []
        for entry in agents:
            if isinstance(entry, dict):
                ids.append(entry.get("name") or entry.get("role") or entry.get("id"))
            else:
                ids.append(str(entry))
        return sorted(identifier for identifier in ids if identifier)
    return []


def _turn_actor(turn):
    """Return one normalized actor label from a structured dialogue turn."""

    for key in TURN_ACTOR_KEYS:
        actor = turn.get(key)
        if isinstance(actor, str) and actor.strip():
            return actor.strip()
        if isinstance(actor, dict):
            for nested_key in ("id", "name", "role"):
                nested = actor.get(nested_key)
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
    return None


def _has_turn_content(turn):
    """Return whether a turn carries rendered dialogue content."""

    for key in TURN_CONTENT_KEYS:
        content = turn.get(key)
        if isinstance(content, str) and content.strip():
            return True
        if isinstance(content, (dict, list)) and content:
            return True
    return False


def _is_multi_actor_turn_sequence(value):
    if not isinstance(value, list):
        return False
    actors = [
        actor
        for turn in value
        if isinstance(turn, dict) and _has_turn_content(turn)
        if (actor := _turn_actor(turn)) is not None
    ]
    return len(actors) >= 2 and len(set(actors)) >= 2


def _swarm_trajectory_paths(value, path=""):
    """Return paths to recursively nested, genuine multi-actor exchanges."""

    paths = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else key
            if key.casefold() in SWARM_TURN_CONTAINER_KEYS and (
                _is_multi_actor_turn_sequence(item)
            ):
                paths.append(child_path)
            paths.extend(_swarm_trajectory_paths(item, child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_swarm_trajectory_paths(item, f"{path}[{index}]"))
    return sorted(set(paths))


def census_from_raw(root: Path) -> dict:
    """Derive the payload-kind census from the immutable raw tree, read-only."""

    files = []
    records = []
    parse_failures = 0
    for path in sorted(root.glob("*.jsonl")):
        payload = path.read_bytes()
        in_file = 0
        for line_number, line in enumerate(payload.decode("utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            in_file += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                parse_failures += 1
                continue
            keys = set(record)
            state = record.get("state") if isinstance(record.get("state"), dict) else {}
            proposed = (
                record.get("proposed_action")
                if isinstance(record.get("proposed_action"), dict)
                else {}
            )
            decision = (
                record.get("safety_decision")
                if isinstance(record.get("safety_decision"), dict)
                else {}
            )
            meta = record.get("meta") if isinstance(record.get("meta"), dict) else {}
            reward = (
                record.get("reward_components")
                if isinstance(record.get("reward_components"), dict)
                else {}
            )
            weights = reward.get("weights") if isinstance(reward.get("weights"), dict) else {}
            swarm_trajectory_paths = _swarm_trajectory_paths(record)
            records.append(
                {
                    "id": f"{path.name}#L{line_number}",
                    "round": meta.get("round"),
                    "meta_factory": meta.get("factory"),
                    "payload_kind": (
                        "thalamic-gate-wrap"
                        if tuple(sorted(keys)) == GATE_WRAP_KEYS
                        else "other"
                    ),
                    "top_level_keys": sorted(keys),
                    "swarm_trajectory_paths": swarm_trajectory_paths,
                    "safety_decision": decision.get("decision"),
                    "multi_actor_state_keys": [
                        key for key in MULTI_ACTOR_STATE_KEYS if key in state
                    ],
                    "state_agent_ids": _agent_ids(state.get("agents")),
                    "hidden_supervision_field": (
                        "internal_reasoning"
                        if "internal_reasoning" in proposed
                        else "internal_reasoning_verbatim"
                        if "internal_reasoning_verbatim" in proposed
                        else None
                    ),
                    "public_decision_basis": "decision_basis" in proposed,
                    "reward_weight_vocabulary": sorted(weights),
                }
            )
        files.append(
            {
                "path": path.name,
                "bytes": len(payload),
                "records": in_file,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    decisions: dict[str, int] = {}
    for record in records:
        key = record["safety_decision"]
        decisions[key] = decisions.get(key, 0) + 1

    return {
        "jsonl_files": len(files),
        "records": len(records),
        "parse_failures": parse_failures,
        "total_jsonl_bytes": sum(entry["bytes"] for entry in files),
        "gate_wrap_records": sum(
            1 for record in records if record["payload_kind"] == "thalamic-gate-wrap"
        ),
        "swarm_trajectory_records": sum(
            1 for record in records if record["swarm_trajectory_paths"]
        ),
        "swarm_trajectory_definition": SWARM_TRAJECTORY_DEFINITION,
        "distinct_top_level_key_sets": len(
            {tuple(record["top_level_keys"]) for record in records}
        ),
        "safety_decisions": dict(sorted(decisions.items())),
        "records_with_multi_actor_state": sum(
            1 for record in records if record["multi_actor_state_keys"]
        ),
        "records_with_state_agents": sum(
            1 for record in records if "agents" in record["multi_actor_state_keys"]
        ),
        "records_with_public_decision_basis": sum(
            1 for record in records if record["public_decision_basis"]
        ),
        "files": files,
        "records_detail": records,
    }


class CommittedCensusContract(unittest.TestCase):
    """Guard the committed finding without needing the gitignored raw tree."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.census = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))
        cls.derived = cls.census["derived"]
        cls.card = CARD_PATH.read_text(encoding="utf-8")
        cls.analysis = ANALYSIS_PATH.read_text(encoding="utf-8")

    def test_every_published_record_is_a_gate_wrap(self) -> None:
        self.assertEqual(self.derived["records"], 14)
        self.assertEqual(self.derived["jsonl_files"], 13)
        self.assertEqual(self.derived["parse_failures"], 0)
        self.assertEqual(self.derived["gate_wrap_records"], 14)
        self.assertEqual(self.derived["swarm_trajectory_records"], 0)
        self.assertEqual(
            self.derived["swarm_trajectory_definition"],
            SWARM_TRAJECTORY_DEFINITION,
        )
        self.assertTrue(
            all(not row["swarm_trajectory_paths"] for row in self.derived["records_detail"])
        )
        self.assertEqual(self.derived["distinct_top_level_key_sets"], 1)

    def test_participant_ids_exclude_agent_mapping_metadata(self) -> None:
        rows = {row["id"]: row for row in self.derived["records_detail"]}
        self.assertEqual(
            rows["batch-r04.jsonl#L1"]["state_agent_ids"],
            ["BS-1", "CC-1", "PO-1", "RC-1", "TG-1"],
        )
        self.assertEqual(
            rows["batch-r05.jsonl#L1"]["state_agent_ids"],
            ["CREW-D", "DER-A", "F1-A", "F2-A", "SUB-A", "TG-2"],
        )
        self.assertEqual(
            _agent_ids(
                {
                    "A-1": {"role": "planner"},
                    "TG-1": {"role": "gate"},
                    "protocol": "consensus",
                    "quorum_rule": {"minimum": 2},
                }
            ),
            ["A-1", "TG-1"],
        )

    def test_swarm_classifier_requires_a_multi_actor_turn_exchange(self) -> None:
        self.assertEqual(_swarm_trajectory_paths({"task": "plan only"}), [])
        self.assertEqual(
            _swarm_trajectory_paths(
                {
                    "state": {
                        "multi_agent": {
                            "turns": [
                                {"role": "planner", "content": "proposal"},
                                {"speaker": "critic", "message": "challenge"},
                            ]
                        }
                    }
                }
            ),
            ["state.multi_agent.turns"],
        )

    def test_census_totals_agree_with_the_per_record_rows(self) -> None:
        rows = self.derived["records_detail"]
        self.assertEqual(len(rows), self.derived["records"])
        self.assertEqual(
            sum(entry["records"] for entry in self.derived["files"]),
            self.derived["records"],
        )
        self.assertEqual(
            sum(entry["bytes"] for entry in self.derived["files"]),
            self.derived["total_jsonl_bytes"],
        )
        self.assertEqual(
            sum(self.derived["safety_decisions"].values()), self.derived["records"]
        )
        self.assertEqual(
            {row["payload_kind"] for row in rows}, {"thalamic-gate-wrap"}
        )
        self.assertEqual(
            {row["meta_factory"] for row in rows}, {"multi-agent-ouroboros-swarm"}
        )
        self.assertEqual(len({row["id"] for row in rows}), self.derived["records"])

    def test_hidden_supervision_is_on_every_record_and_never_public(self) -> None:
        rows = self.derived["records_detail"]
        self.assertTrue(all(row["hidden_supervision_field"] for row in rows))
        self.assertEqual(self.derived["records_with_public_decision_basis"], 0)

    def test_committed_digests_match_the_published_raw_snapshot(self) -> None:
        """The census describes exactly the bytes the Hub declares immutable."""

        published = {
            entry["path"]: entry["sha256"]
            for entry in self.census["hub_raw_snapshot"]["files"]
        }
        derived = {
            f"data/raw/{entry['path']}": entry["sha256"]
            for entry in self.derived["files"]
        }
        self.assertEqual(derived, published)

    def test_operator_card_states_the_corrected_payload_kind(self) -> None:
        # Normalize the way the verifier does, so line wrapping in the card
        # cannot break the assertion.
        normalize = verify_hf_release._normalized_text
        card = normalize(self.card)
        for marker in verify_hf_release.REQUIRED_PAYLOAD_DISCLOSURE[DATASET_REPO]:
            self.assertIn(normalize(marker), card)
        self.assertIn(
            normalize(verify_hf_release.REQUIRED_PURPOSE_TEXT[DATASET_REPO]), card
        )
        self.assertNotIn(normalize("14 raw multi-agent records"), card)

    def test_operator_card_passes_the_release_verifier_card_contract(self) -> None:
        """The text we hand the operator must satisfy the repo's own verifier."""

        self.assertEqual(
            verify_hf_release._card_section_errors(self.card, DATASET_REPO), []
        )
        self.assertEqual(
            verify_hf_release._front_matter(self.card).get("license"), "apache-2.0"
        )

    def test_verifier_rejects_obsolete_claims_even_with_new_disclosures(self) -> None:
        cards = (
            (
                self.card.replace(
                    "## Intended model target",
                    "Synthetic multi-agent trajectories for delegation, critique, "
                    "conflict resolution.\n\n## Intended model target",
                    1,
                ),
                "Synthetic multi-agent trajectories for delegation, critique, "
                "conflict resolution",
            ),
            (
                self.card.replace(
                    "The release contains 14 raw records",
                    "The release contains 14 raw multi-agent records",
                    1,
                ),
                "14 raw multi-agent records",
            ),
            (
                self.card.replace(
                    "## Intended model target",
                    "Synthetic multi-agent trajectories for delegation, "
                    "**critique**, conflict resolution.\n\n## Intended model target",
                    1,
                ),
                "Synthetic multi-agent trajectories for delegation, critique, "
                "conflict resolution",
            ),
        )
        for card, obsolete_claim in cards:
            with self.subTest(obsolete_claim=obsolete_claim):
                self.assertIn(
                    f"README retains obsolete payload-kind claim: {obsolete_claim}",
                    verify_hf_release._card_section_errors(card, DATASET_REPO),
                )

    def test_payload_disclosure_in_an_html_comment_does_not_count(self) -> None:
        card = self.card.replace(
            "thalamic-gate wrap schema",
            "gate-wrap schema <!-- thalamic-gate wrap schema -->",
            1,
        )
        self.assertIn(
            "README missing payload-kind disclosure: thalamic-gate wrap schema",
            verify_hf_release._card_section_errors(card, DATASET_REPO),
        )

    def test_verifier_no_longer_pins_the_mislabelled_purpose(self) -> None:
        self.assertNotIn(
            "delegation, critique, conflict resolution",
            verify_hf_release.REQUIRED_PURPOSE_TEXT[DATASET_REPO],
        )
        self.assertIn(
            "safety-gate adjudication",
            verify_hf_release.REQUIRED_PURPOSE_TEXT[DATASET_REPO],
        )

    def test_the_live_card_still_fails_until_the_operator_republishes(self) -> None:
        """The published card is the defect; the fix is a Hub write we cannot do."""

        live = self.census["live_card_at_audit"]["published_purpose_sentence"]
        self.assertNotIn(
            verify_hf_release.REQUIRED_PURPOSE_TEXT[DATASET_REPO],
            " ".join(live.split()),
        )

    def test_analysis_records_that_the_hub_write_is_not_ours(self) -> None:
        self.assertIn("cannot be written from this repository", self.analysis)


@unittest.skipUnless(
    RAW_SWARM.is_dir(),
    "raw multi-agent-ouroboros-swarm corpus not present in this checkout "
    "(gitignored); the payload census is re-derived only where it exists",
)
class RawCorpusCensusFidelity(unittest.TestCase):
    """Re-derive the committed census from the immutable raw tree."""

    def test_committed_census_matches_a_fresh_raw_scan(self) -> None:
        committed = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))["derived"]
        self.assertEqual(census_from_raw(RAW_SWARM), committed)


if __name__ == "__main__":
    unittest.main()
