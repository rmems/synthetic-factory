#!/usr/bin/env python3
"""Per-record signal observers for the corpus training audit.

Each ``_observe_*`` axis tallies one facet of a decoded record: identity and
root-id coverage, exact-duplicate content, provenance labels, gate decisions
and errors, preference-pair purity, reward/tag vocabulary, agentic decision
basis, embedded episode errors, and unignored warnings. Facade seams are
resolved through ``self.api`` so the ``training_audit`` module keeps owning
patchable names.
"""

from __future__ import annotations

import hashlib
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("training_audit_axes")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_axes"
    )


class AuditAxes:
    """Record-level observations accumulated onto a corpus audit object."""

    def _observe_embedded_episodes(self, obj, kind, where):
        readers = self.api._record_audit.EmbeddedEpisodeReaders(
            self.api.wrapped_agentic_episodes,
            self.api.shape_check,
            self.api.check_episode,
        )
        self.record_errors.extend(
            self.api._record_audit.embedded_episode_errors(obj, kind, where, readers)
        )

    def _observe_warnings(self, warnings):
        ignored = (
            "missing canonical record id",
            "missing top-level id",
            "missing sim_or_real",
            "non-training provenance",
            "uses legacy 'thought'",
        )
        self.unresolved_record_warnings.extend(
            warning for warning in warnings if not any(item in warning for item in ignored)
        )

    def _observe_identity(self, obj, checked_id, where):
        record_id = checked_id or self.api.canonical_record_id(obj)
        if record_id is None:
            self.missing_ids.append(where)
        else:
            self.canonical_id_records += 1
            if record_id in self.ids:
                self.duplicate_ids.append(
                    {"id": record_id, "first": self.ids[record_id], "again": where}
                )
            else:
                self.ids[record_id] = where

        root_id = self.api.root_record_id(obj)
        if root_id is None:
            self.missing_root_ids.append(where)
        else:
            self.root_id_records += 1
            self.root_ids.setdefault(root_id, where)

    def _observe_duplicate(self, obj, where):
        digest = hashlib.sha256(self.api.canonical_blob(obj).encode("utf-8")).hexdigest()
        if digest in self.content_seen:
            self.exact_duplicates.append({"first": self.content_seen[digest], "again": where})
        else:
            self.content_seen[digest] = where

    def _observe_provenance(self, obj, kind, where):
        for state_path, state in self.api.expected_states(obj, kind):
            value = state.get("sim_or_real") if isinstance(state, dict) else None
            if value is None:
                label = "missing"
            elif value in self.api.ALLOWED_PROVENANCE:
                label = str(value)
            else:
                label = "non_training"
            self.provenance[label] += 1
            if len(self.provenance_examples[label]) < 5:
                self.provenance_examples[label].append(f"{where}:{state_path}={value!r}")

    def _observe_gates(self, obj, kind, where):
        for role, trajectory in self.api.thalamic_views(obj, kind):
            decision = self.api.dict_field(trajectory, "safety_decision")
            label = decision.get("decision")
            if isinstance(label, str):
                self.gate_by_role[role][label] += 1
            error_type = self.api.dict_field(trajectory, "meta").get("supervisor_error_type")
            if decision.get("correctness") == "incorrect" or error_type:
                self._observe_gate_error(error_type, where, role)

    def _observe_gate_error(self, error_type, where, role):
        self.gate_errors["marked"] += 1
        self.gate_errors[str(error_type) if error_type else "unspecified"] += 1
        if len(self.gate_error_examples) < 5:
            self.gate_error_examples.append(f"{where}:{role}")

    def _observe_preference(self, obj, kind):
        if kind != "preference":
            return
        self.preference["pairs"] += 1
        chosen = self.api.dict_field(obj, "chosen")
        rejected = self.api.dict_field(obj, "rejected")
        purity = self.api.preference_context_purity(obj, chosen, rejected)
        self.preference["episode_pairs"] += int(purity["episode_pair"])
        self.preference["thalamic_pairs"] += int(not purity["episode_pair"])
        self.preference["same_context"] += int(purity["pure"])
        if purity["same_state"] is not None:
            self.preference["same_state"] += int(purity["same_state"])
            self.preference["same_proposal"] += int(purity["same_proposal"])
        if purity["same_goal"] is not None:
            self.preference["same_goal"] += int(purity["same_goal"])
        decision = self.api.dict_field(chosen, "safety_decision").get("decision")
        if isinstance(decision, str):
            self.chosen_decisions[decision] += 1

    def _observe_vocabulary(self, obj):
        for _path, reward in self.api.walk_key(obj, "reward_components"):
            self._observe_reward(reward)
        for _path, values in self.api.walk_key(obj, "tags"):
            self._observe_tags(values)

    def _observe_reward(self, reward):
        if isinstance(reward, dict):
            self.reward_keys.update(reward.keys())
        self.reward_shapes[self.api.reward_shape(reward)] += 1

    def _observe_tags(self, values):
        if isinstance(values, list):
            self.tags.update(value for value in values if isinstance(value, str))

    def _observe_agentic(self, obj, kind, where):
        self.episodes["episodes"] += int(kind == "episode")
        for hidden_path in self.api.hidden_thought_paths(obj):
            self._observe_hidden_thought(hidden_path, where)
        for turn in self.api.agentic_turns(obj, kind):
            self._observe_agentic_turn(turn)

    def _observe_hidden_thought(self, hidden_path, where):
        self.episodes["hidden_thought_fields"] += 1
        if len(self.hidden_thought_examples) < 10:
            self.hidden_thought_examples.append(f"{where}:{hidden_path}")

    def _observe_agentic_turn(self, turn):
        if not isinstance(turn, dict):
            return
        has_basis = self.api.has_observable_decision_basis(turn)
        self.episodes["steps"] += 1
        self.episodes["decision_basis_steps"] += int(has_basis)
        self.episodes["missing_decision_basis_steps"] += int(not has_basis)
        self.episodes["legacy_thought_only_steps"] += int(
            "thought" in turn and "decision_basis" not in turn
        )


if __package__:
    _expose_package_sibling(__name__)
