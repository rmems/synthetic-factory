"""Focused invariants extracted from family_credit.py."""

from itertools import pairwise

from . import canon, sim
from .family_common import _measurement_matches


class CreditChecks:
    def _stage_is_reference(self, record, suffix):
        """Whether the named chain stage was run by the in-repo reference.

    Anything other than an explicit named-runtime claim is treated as the
    reference implementation, so a malformed stage list keeps the reference
    reruns (fail closed) rather than skipping them.
    """
        for stage in record['oracle'].get('stages') or ():
            if isinstance(stage, dict) and str(stage.get('stage', '')).endswith(f':{suffix}'):
                return stage.get('implementation') != 'named-runtime'
        return True

    def _credit_critic_findings(self, record, critic):
        """(findings, critic_factors) for the critic stage.

    The documented boundary leaves agreement with the named runtimes
    unverified: only a reference critic stage is authenticated by rerunning
    the reference. The returned factors are the modulator levels the executed
    critic stage actually reported -- for a reference critic the recomputed
    values, so a forged retained level cannot feed the plasticity checks.
    """
        if not self._stage_is_reference(record, 'critic'):
            return ([], critic)
        findings = []
        outcome = record['scenario']['outcome']
        critic_config = record['oracle']['configuration']['critic']
        expected_critic = sim.run_critic(outcome, critic_config)
        for field in ('reward_prediction_error', 'dopamine_phasic', 'dopamine', 'serotonin', 'acetylcholine', 'norepinephrine', 'valence'):
            if not _measurement_matches(critic.get(field), expected_critic[field]):
                findings.append(f'critic.{field} does not match the value derived from the scenario outcome and critic configuration')
        return (findings, expected_critic)

    def _credit_rule_findings(self, index, factors, findings):
        """Bind one weight's retained delta and after-weight to the update rule."""
        start, end, delta, bound_trace, critic_factors, plasticity, plasticity_config = factors
        raw_delta = plasticity_config['learning_rate'] * bound_trace * critic_factors['dopamine_phasic'] * plasticity['modulatory_gain']
        derived_after = sim.clamp(start + raw_delta, plasticity_config['w_min'], plasticity_config['w_max'])
        derived_delta = derived_after - start
        if not _measurement_matches(delta, derived_delta):
            findings.append(f'weight {index} delta does not match learning_rate * eligibility * dopamine_phasic * modulatory_gain with configured bounds')
        if not _measurement_matches(end, start + derived_delta):
            findings.append(f'weight {index} does not satisfy after = before + delta derived from the retained learning rule')
        return derived_delta

    def _credit_update_findings(self, record, plasticity, critic_factors):
        """(findings, derived_deltas, expected_pre, expected_post) for the update.

    A named plasticity stage owns its spike timing, so its retained
    eligibility is the factor the update rule is checked against; only a
    reference stage is additionally compared against the recomputed STDP
    traces and circuit replays.
    """
        findings = []
        before = plasticity['weights_before']
        after = plasticity['weights_after']
        deltas = plasticity['weight_deltas']
        scenario_circuit = record['scenario']['circuit']
        initial_weights = scenario_circuit['initial_weights']
        if before != initial_weights:
            findings.append('plasticity.weights_before does not match scenario.initial_weights')
        vector_lengths = (len(before), len(after), len(deltas), len(plasticity['eligibility']), len(initial_weights), len(scenario_circuit['pre_spike_times_ms']))
        derived_deltas = []
        expected_pre = None
        expected_post = None
        if len(set(vector_lengths)) != 1 or vector_lengths[0] != scenario_circuit['pre_neuron_count']:
            findings.append('plasticity weight vectors have inconsistent lengths')
            return (findings, derived_deltas, expected_pre, expected_post)
        plasticity_config = record['oracle']['configuration']['plasticity']
        eligibility = plasticity['eligibility']
        pre_spikes = scenario_circuit['pre_spike_times_ms']
        plasticity_is_reference = self._stage_is_reference(record, 'plasticity')
        if plasticity_is_reference:
            expected_pre = sim._plasticity_circuit(before, pre_spikes, plasticity_config)
            expected_traces = sim.eligibility_traces(before, pre_spikes, expected_pre['spike_times_ms'], plasticity_config)
        else:
            expected_traces = None
        for index, (start, end, delta, trace) in enumerate(zip(before, after, deltas, eligibility, strict=True)):
            if expected_traces is None:
                bound_trace = trace
            else:
                bound_trace = expected_traces[index]
                if not _measurement_matches(trace, expected_traces[index]):
                    findings.append(f'weight {index} eligibility does not match the STDP trace derived from the pre-synaptic trains and pre-update spikes')
            factors = (start, end, delta, bound_trace, critic_factors, plasticity, plasticity_config)
            derived_deltas.append(self._credit_rule_findings(index, factors, findings))
        if plasticity_is_reference:
            expected_post = sim._plasticity_circuit(after, pre_spikes, plasticity_config)
        return (findings, derived_deltas, expected_pre, expected_post)

    def _credit_behavior_summary_findings(self, name, behavior, recomputed, duration_ms):
        findings = []
        times = behavior['spike_times_ms']
        if any((later < earlier for earlier, later in pairwise(times))):
            findings.append(f'plasticity.{name}.spike_times_ms is not ordered')
        if any((time_ms < 0 or time_ms >= duration_ms for time_ms in times)):
            findings.append(f'plasticity.{name}.spike_times_ms leaves the simulated duration')
        expected_summary = {'spike_count': len(times), 'first_spike_ms': times[0] if times else None, 'output_rate_hz': len(times) / (duration_ms / 1000.0)}
        for field, expected in expected_summary.items():
            if not _measurement_matches(behavior.get(field), expected):
                findings.append(f'plasticity.{name}.{field} does not match spike_times_ms')
        if recomputed is not None:
            summary_keys = ('spike_count', 'spike_times_ms', 'first_spike_ms', 'output_rate_hz')
            retained = {key: behavior.get(key) for key in summary_keys}
            measured = {key: recomputed.get(key) for key in summary_keys}
            if canon.normalize(retained) != canon.normalize(measured):
                findings.append(f'plasticity.{name} does not match a re-run of the circuit at the retained weights')
        return findings

    def _credit_behavior_delta_findings(self, plasticity, pre, post):
        findings = []
        expected_behavior_delta = {'spike_count_delta': post['spike_count'] - pre['spike_count'], 'output_rate_delta_hz': post['output_rate_hz'] - pre['output_rate_hz'], 'first_spike_shift_ms': sim._optional_delta(post['first_spike_ms'], pre['first_spike_ms'])}
        behavior_delta = plasticity.get('behavior_delta')
        if not isinstance(behavior_delta, dict):
            findings.append('plasticity.behavior_delta must be an object')
            return findings
        for field, expected in expected_behavior_delta.items():
            if not _measurement_matches(behavior_delta.get(field), expected):
                findings.append(f'plasticity.behavior_delta.{field} does not match the pre/post behavior')
        return findings

    def _credit_behavior_findings(self, plasticity, plasticity_config, expected_pre, expected_post):
        """Findings on the retained pre/post circuit behaviour summaries."""
        if 'post_update_behavior' not in plasticity or 'pre_update_behavior' not in plasticity:
            return ['plasticity must report behaviour before and after the update']
        pre = plasticity['pre_update_behavior']
        post = plasticity['post_update_behavior']
        duration_ms = plasticity_config['duration_ms']
        findings = self._credit_behavior_summary_findings('pre_update_behavior', pre, expected_pre, duration_ms)
        findings.extend(self._credit_behavior_summary_findings('post_update_behavior', post, expected_post, duration_ms))
        findings.extend(self._credit_behavior_delta_findings(plasticity, pre, post))
        return findings

    def _credit_scenario_findings(self, record):
        circuit = record['scenario']['circuit']
        findings = []
        for index, times in enumerate(circuit['pre_spike_times_ms']):
            if any((later < earlier for earlier, later in pairwise(times))):
                findings.append(f'scenario pre-synaptic spike train {index} is not ordered')
            if any((time_ms < 0 or time_ms >= circuit['duration_ms'] for time_ms in times)):
                findings.append(f'scenario pre-synaptic spike train {index} leaves the circuit duration')
        return findings

    def _credit_update_metadata_findings(self, plasticity, plasticity_config, critic_factors, derived_deltas):
        expected_gain = 1.0 + plasticity_config['modulatory_gain_ach'] * critic_factors['acetylcholine'] + plasticity_config['modulatory_gain_ne'] * critic_factors['norepinephrine']
        findings = []
        if not _measurement_matches(plasticity['modulatory_gain'], expected_gain):
            findings.append('plasticity.modulatory_gain does not match critic modulators')
        if plasticity['update_rule'] != 'dw = lr * eligibility * dopamine_phasic * modulatory_gain':
            findings.append('plasticity.update_rule does not name the executed update')
        deltas_complete = len(derived_deltas) == len(plasticity['weight_deltas'])
        applied = deltas_complete and any((abs(delta) > sim.WEIGHT_UPDATE_EPS for delta in derived_deltas))
        if plasticity['update_applied'] != applied:
            findings.append('plasticity.update_applied disagrees with the weight deltas')
        return findings

    def _credit_checks(self, record):
        measured = record['result']['measured']
        critic = measured.get('critic')
        plasticity = measured.get('plasticity')
        if not isinstance(critic, dict) or not isinstance(plasticity, dict):
            return ['result.measured must carry both a critic and a plasticity stage']
        findings, critic_factors = self._credit_critic_findings(record, critic)
        update = self._credit_update_findings(record, plasticity, critic_factors)
        update_findings, derived_deltas, expected_pre, expected_post = update
        findings.extend(update_findings)
        findings.extend(self._credit_scenario_findings(record))
        plasticity_config = record['oracle']['configuration']['plasticity']
        findings.extend(self._credit_update_metadata_findings(plasticity, plasticity_config, critic_factors, derived_deltas))
        findings.extend(self._credit_behavior_findings(plasticity, plasticity_config, expected_pre, expected_post))
        return findings
