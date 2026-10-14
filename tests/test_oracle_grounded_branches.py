"""Per-invariant findings of the five oracle-grounded family checks.

Each case copies one accepted reference record, edits a single retained value
under ``result.measured``, re-hashes the result, and asserts that
``record.validate_record`` reports the exact finding the family check emits
today. Two groups of family-check lines are not driven because an earlier gate
decides first: any scenario edit fails the generator-seed reproduction check, and
any edit that breaks the family JSON schema (a negative latency, a missing
control, an unknown response or neuron id, a non-object stage) is reported by
the schema validator before the family checks run.
"""

import copy
import unittest

from tests.test_oracle_grounded_record import accepted_reference, families, result_findings

_REFERENCES = {}


def _reference(family):
    if family not in _REFERENCES:
        _REFERENCES[family] = accepted_reference(family)
    return copy.deepcopy(_REFERENCES[family])


def _parent(item, path):
    node = item["result"]["measured"]
    for key in path[:-1]:
        node = node[key]
    return node


def _put(path, value):
    def edit(item):
        _parent(item, path)[path[-1]] = copy.deepcopy(value)

    return edit


def _shift(path, by):
    def edit(item):
        _parent(item, path)[path[-1]] += by

    return edit


def _drop(path):
    def edit(item):
        del _parent(item, path)[path[-1]]

    return edit


def _append(path, value):
    def edit(item):
        _parent(item, path)[path[-1]].append(value)

    return edit


def _pop(path):
    def edit(item):
        _parent(item, path)[path[-1]].pop()

    return edit


def _reverse(path):
    def edit(item):
        _parent(item, path)[path[-1]].reverse()

    return edit


BASE = ("baseline",)
CRITIC = ("critic",)
PLASTIC = ("plasticity",)
PRE = PLASTIC + ("pre_update_behavior",)
DEPENDENCE = ("temporal_dependence",)
BEFORE = ("before",)
DELTA_DERIVED = "does not match the value derived from before/after states"
SUMMARY_DERIVED = "does not match the summary derived from spike_times_ms and the retained duration"
ENCODING_A = ("encoding_a",)
EXCERPT0 = ENCODING_A + ("representation_excerpt", 0)

# (label, edit(record), finding the memory checks must report)
MEMORY_CASES = (
    ("measured delay", _shift(("delay_ms",), 1.0),
     "result.measured.delay_ms does not match the scenario delay"),
    ("response vs counts", _put(BASE + ("response",), "A"),
     "baseline.response does not match output_spike_counts"),
    ("response vs latency", _put(BASE + ("response",), "A"),
     "baseline.response and response_latency_ms disagree"),
    ("ambiguity vs counts", _put(BASE + ("response_ambiguous",), True),
     "baseline.response_ambiguous does not match output_spike_counts"),
    ("ambiguous response", _put(BASE + ("response_ambiguous",), True),
     "baseline has an ambiguous response"),
    ("late latency", _put(BASE + ("response_latency_ms",), 1.0e6),
     "baseline.response_latency_ms leaves the response window"),
    ("spike budget", _put(BASE + ("spike_budget_exhausted",), True),
     "baseline hit the spike budget; the trajectory is truncated"),
    ("latch window", _put(BASE + ("latch_last_spike_ms",), {"MA": None, "MB": 1.0e6}),
     "baseline.latch_last_spike_ms leaves the retained probe window"),
    ("energy", _shift(BASE + ("energy_pJ",), 1.0),
     "baseline.energy_pJ does not match total_spikes"),
    ("duration", _shift(BASE + ("duration_ms",), 1.0),
     "baseline.duration_ms does not match the task configuration"),
    ("retention", _put(BASE + ("state_retained_at_probe",), True),
     "baseline.state_retained_at_probe does not match latch_last_spike_ms"),
    ("dependence flag", _put(DEPENDENCE + ("demonstrated",), False),
     "temporal_dependence.demonstrated does not match the ablation responses"),
    ("dependence controls", _put(DEPENDENCE + ("changed_by",), []),
     "temporal_dependence.changed_by does not match the changed controls"),
    ("control set", _drop(("probes", "reset_ablation")),
     "memory control probes do not match the scenario controls"),
    ("distractor control", _put(("distractor_invariant",), False),
     "distractor_invariant does not match the distractor control"),
)

# (label, edit(record), finding the credit-assignment checks must report)
CREDIT_CASES = (
    ("critic level", _shift(CRITIC + ("dopamine",), 0.5),
     ("critic.dopamine does not match the value derived from the scenario outcome and critic "
      "configuration")),
    ("weight delta", _shift(PLASTIC + ("weight_deltas", 0), 0.1),
     ("weight 0 delta does not match learning_rate * eligibility * dopamine_phasic * "
      "modulatory_gain with configured bounds")),
    ("weight after", _shift(PLASTIC + ("weights_after", 0), 0.1),
     "weight 0 does not satisfy after = before + delta derived from the retained learning rule"),
    ("weights before", _shift(PLASTIC + ("weights_before", 0), 0.1),
     "plasticity.weights_before does not match scenario.initial_weights"),
    ("vector lengths", _put(PLASTIC + ("eligibility",), [1.0]),
     "plasticity weight vectors have inconsistent lengths"),
    ("eligibility", _shift(PLASTIC + ("eligibility", 0), 0.5),
     ("weight 0 eligibility does not match the STDP trace derived from the pre-synaptic trains "
      "and pre-update spikes")),
    ("spike order", _reverse(PRE + ("spike_times_ms",)),
     "plasticity.pre_update_behavior.spike_times_ms is not ordered"),
    ("spike summary", _shift(PRE + ("spike_count",), 1),
     "plasticity.pre_update_behavior.spike_count does not match spike_times_ms"),
    ("delta value", _shift(PLASTIC + ("behavior_delta", "spike_count_delta"), 1),
     "plasticity.behavior_delta.spike_count_delta does not match the pre/post behavior"),
    ("modulatory gain", _shift(PLASTIC + ("modulatory_gain",), 0.1),
     "plasticity.modulatory_gain does not match critic modulators"),
    ("update rule", _put(PLASTIC + ("update_rule",), "dw = 0"),
     "plasticity.update_rule does not name the executed update"),
    ("update flag", _put(PLASTIC + ("update_applied",), False),
     "plasticity.update_applied disagrees with the weight deltas"),
)

# (label, edit(record), finding the mesh-propagation checks must report)
MESH_CASES = (
    ("source", _put(BEFORE + ("source",), "N9"), "before.source does not match scenario.source"),
    ("sink", _put(BEFORE + ("sink",), "N9"), "before.sink does not match scenario.sink"),
    ("arrival nodes", _put(BEFORE + ("first_arrival_ms", "N9"), None),
     "before.first_arrival_ms keys do not match scenario.nodes"),
    ("count nodes", _put(BEFORE + ("spike_counts", "N9"), 0),
     "before.spike_counts keys do not match scenario.nodes"),
    ("unknown firing node", _append(BEFORE + ("firing_order",), "N9"),
     "before.firing_order names unknown nodes: ['N9']"),
    ("arrival without spikes", _put(BEFORE + ("first_arrival_ms", "N3"), 40.0),
     "before.first_arrival_ms[N3] disagrees with spike_counts"),
    ("arrival after duration", _put(BEFORE + ("first_arrival_ms", "N1"), 1.0e6),
     "before.first_arrival_ms[N1] lies outside the simulated duration"),
    ("firing order", _reverse(BEFORE + ("firing_order",)),
     "before.firing_order does not match first_arrival_ms"),
    ("activation", _put(BEFORE + ("downstream_activation",), []),
     "before.downstream_activation does not match spike_counts"),
    ("total spikes", _shift(BEFORE + ("total_spikes",), 1),
     "before.total_spikes does not match spike_counts"),
    ("energy", _shift(BEFORE + ("energy_pJ",), 1.0),
     "before.energy_pJ does not match total_spikes"),
    ("sink reached", _put(BEFORE + ("sink_reached",), True),
     "before.sink_reached disagrees with first_arrival_ms[N5]"),
    ("spike budget", _put(BEFORE + ("spike_budget_exhausted",), True),
     "before hit the spike budget; the trajectory is truncated"),
    ("propagation delay", _put(BEFORE + ("propagation_delay_ms",), 5.0),
     "before.propagation_delay_ms does not match sink minus source arrival"),
    ("delay delta", _put(BEFORE + ("propagation_delay_ms",), 5.0),
     "delta.propagation_delay_delta_ms does not match the before/after delays"),
    ("derived delta", _put(("delta", "firing_order_changed"), False),
     f"delta.firing_order_changed {DELTA_DERIVED}"),
)

# (label, edit(record), finding the neuron-intervention checks must report)
NEURON_CASES = (
    ("trace length", _pop(BEFORE + ("v_trace",)),
     "before.v_trace length does not match v_trace_stride_ms and duration_ms"),
    ("spike order", _reverse(BEFORE + ("spike_times_ms",)),
     "before.spike_times_ms is not non-decreasing"),
    ("spike window", _put(BEFORE + ("spike_times_ms", -1), 1.0e6),
     "before.spike_times_ms contains an event outside the simulated duration"),
    ("summary", _shift(BEFORE + ("spike_count",), 1), f"before.spike_count {SUMMARY_DERIVED}"),
    ("voltage bounds", _put(BEFORE + ("v_min",), 2.0), "before.v_min is greater than v_max"),
    ("mean voltage", _put(BEFORE + ("v_mean",), 5.0),
     "before.v_mean does not lie between v_min and v_max"),
    ("trace floor", _put(BEFORE + ("v_trace", 0), -5.0),
     "before.v_trace[0] is below the recorded v_min"),
    ("trace ceiling", _put(BEFORE + ("v_trace", 0), 5.0),
     "before.v_trace[0] is above the recorded v_max"),
)

# (label, edit(record), finding the encoder-comparison checks must report)
ENCODER_CASES = (
    ("encoding pair", _put(ENCODING_A + ("encoding",), "rate"),
     "encoding_a.encoding 'rate' does not match scenario.encoding_pair ('temporal')"),
    ("excerpt channel", _put(EXCERPT0 + ("channel",), "rate_on"),
     "encoding_a.representation_excerpt[0] names an unknown channel"),
    ("excerpt time", _put(EXCERPT0 + ("t_ms",), 1.0e6),
     "encoding_a.representation_excerpt[0].t_ms lies outside the encoded signal window"),
    ("excerpt truncation", _put(ENCODING_A + ("representation_excerpt_truncated",), False),
     ("encoding_a.representation_excerpt_truncated does not match spike_count and the retained "
      "excerpt")),
    ("retention margin", _shift(("retention_margin",), 0.5),
     "retention_margin does not match the two measured retentions"),
    ("energy margin", _shift(("energy_margin_pJ",), 5.0),
     "energy_margin_pJ does not match the two measured energies"),
    ("winner basis", _put(("winner_basis",), "tie"),
     ("winner_basis 'tie' does not match the measured retention and spike counts "
      "('information_retention')")),
    ("winner outside pair", _put(("winner",), "burst"),
     "winner 'burst' is not one of the compared encodings ['temporal', 'rate']"),
)


FAMILY_CASES = {
    families.MEMORY_FAMILY: MEMORY_CASES,
    families.CREDIT_FAMILY: CREDIT_CASES,
    families.MESH_FAMILY: MESH_CASES,
    families.NEURON_FAMILY: NEURON_CASES,
    families.ENCODER_FAMILY: ENCODER_CASES,
}


class FamilyInvariantFindings(unittest.TestCase):
    def _assert_findings(self, family, cases):
        for label, edit, expected in cases:
            with self.subTest(family=family, case=label):
                item = _reference(family)
                edit(item)
                self.assertIn(expected, result_findings(item))

    def test_reference_records_start_clean(self):
        for family in FAMILY_CASES:
            with self.subTest(family):
                self.assertEqual(result_findings(_reference(family)), [])

    def test_each_family_reports_each_edited_invariant(self):
        for family, cases in FAMILY_CASES.items():
            self._assert_findings(family, cases)


if __name__ == "__main__":
    unittest.main()
