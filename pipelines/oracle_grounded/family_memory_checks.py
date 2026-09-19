"""Focused invariants extracted from family_memory.py."""

from itertools import pairwise

from . import canon, sim
from .family_common import _measurement_matches


class MemoryChecks:

    def __init__(self, api):
        self.api = api

    def _memory_delay_findings(self, scenario, measured):
        expected_delay = scenario['probe_ms'] - scenario['cue_ms']
        findings = []
        if not _measurement_matches(scenario['delay_ms'], expected_delay):
            findings.append('scenario.delay_ms does not match probe_ms - cue_ms')
        if not _measurement_matches(measured['delay_ms'], expected_delay):
            findings.append('result.measured.delay_ms does not match the scenario delay')
        return findings

    def _memory_distractor_findings(self, scenario):
        expected_delay = scenario['probe_ms'] - scenario['cue_ms']
        findings = []
        if scenario['distractor_count'] != len(scenario['distractor_ms']):
            findings.append('scenario.distractor_count does not match distractor_ms')
        expected_sparsity = (len(scenario['distractor_ms']) + 1) / max(1.0, expected_delay / 100.0)
        if not _measurement_matches(scenario['event_sparsity'], expected_sparsity):
            findings.append('scenario.event_sparsity does not match the retained events')
        if any((later <= earlier for earlier, later in pairwise(scenario['distractor_ms']))):
            findings.append('scenario.distractor_ms must be strictly increasing')
        if any((time_ms <= scenario['cue_ms'] or time_ms >= scenario['probe_ms'] for time_ms in scenario['distractor_ms'])):
            findings.append('scenario distractors must lie strictly between cue and probe')
        return findings

    def _memory_scenario_findings(self, record):
        scenario = record['scenario']
        findings = self._memory_delay_findings(scenario, record['result']['measured'])
        findings.extend(self._memory_distractor_findings(scenario))
        return findings

    def _response_match_findings(self, name, trial):
        expected_response, expected_ambiguous = sim.memory_response_from_counts(trial['output_spike_counts'])
        findings = []
        if trial['response'] != expected_response:
            findings.append(f'{name}.response does not match output_spike_counts')
        if trial['response_ambiguous'] is not expected_ambiguous:
            findings.append(f'{name}.response_ambiguous does not match output_spike_counts')
        if trial['response'] not in ('A', 'B', 'none'):
            findings.append(f"{name}.response is unexpected: {trial['response']!r}")
        if trial['response_ambiguous']:
            findings.append(f'{name} has an ambiguous response')
        return findings

    def _latency_findings(self, name, trial, configuration):
        latency = trial['response_latency_ms']
        findings = []
        if latency is not None and latency < 0:
            findings.append(f'{name}.response_latency_ms is negative')
        if latency is not None and latency > configuration['response_window_ms']:
            findings.append(f'{name}.response_latency_ms leaves the response window')
        if (trial['response'] == 'none') is not (latency is None):
            findings.append(f'{name}.response and response_latency_ms disagree')
        return findings

    def _memory_response_findings(self, name, trial, configuration):
        findings = self._response_match_findings(name, trial)
        findings.extend(self._latency_findings(name, trial, configuration))
        return findings

    def _memory_replay_findings(self, record, name, trial):
        scenario = record['scenario']
        expected_task = self.api._memory_trial_task(scenario, name)
        if expected_task is None:
            return [f'{name} is not a known memory trial']
        if record['oracle']['implementation'] == 'named-runtime':
            return []
        try:
            replayed = sim.run_memory_task(expected_task, record['oracle']['configuration'])
        except Exception:
            return [f'{name}.response_latency_ms could not be derived from a trial replay']
        findings = []
        if not _measurement_matches(trial['response_latency_ms'], replayed['response_latency_ms']):
            findings.append(f'{name}.response_latency_ms does not match the first readout spike')
        if canon.normalize(trial) != canon.normalize(replayed):
            findings.append(f'{name} does not match the complete reference replay')
        return findings

    def _memory_shape_findings(self, record, name, trial):
        scenario = record['scenario']
        findings = []
        if trial['spike_budget_exhausted']:
            findings.append(f'{name} hit the spike budget; the trajectory is truncated')
        if set(trial['output_spike_counts']) != {'OA', 'OB'}:
            findings.append(f'{name}.output_spike_counts has unexpected neuron ids')
        if set(trial['memory_spike_counts']) != {'MA', 'MB'}:
            findings.append(f'{name}.memory_spike_counts has unexpected neuron ids')
        if set(trial['latch_last_spike_ms']) != {'MA', 'MB'}:
            findings.append(f'{name}.latch_last_spike_ms has unexpected neuron ids')
        if any((time_ms is not None and (not 0 <= time_ms <= scenario['probe_ms']) for time_ms in trial['latch_last_spike_ms'].values())):
            findings.append(f'{name}.latch_last_spike_ms leaves the retained probe window')
        return findings

    def _memory_accounting_findings(self, record, name, trial):
        scenario = record['scenario']
        configuration = record['oracle']['configuration']
        findings = []
        expected_energy = trial['total_spikes'] * sim.ENERGY_PJ_PER_SPIKE
        if not _measurement_matches(trial['energy_pJ'], expected_energy):
            findings.append(f'{name}.energy_pJ does not match total_spikes')
        expected_duration = scenario['probe_ms'] + configuration['response_window_ms'] + 5.0
        if not _measurement_matches(trial['duration_ms'], expected_duration):
            findings.append(f'{name}.duration_ms does not match the task configuration')
        horizon = configuration['loop_delay_ms'] * 1.5
        retained = any((time_ms is not None and scenario['probe_ms'] - horizon <= time_ms <= scenario['probe_ms'] for time_ms in trial['latch_last_spike_ms'].values()))
        if trial['state_retained_at_probe'] is not retained:
            findings.append(f'{name}.state_retained_at_probe does not match latch_last_spike_ms')
        return findings

    def _memory_trial_findings(self, record, name, trial):
        findings = self._memory_response_findings(name, trial, record['oracle']['configuration'])
        findings.extend(self._memory_replay_findings(record, name, trial))
        findings.extend(self._memory_shape_findings(record, name, trial))
        findings.extend(self._memory_accounting_findings(record, name, trial))
        return findings

    def _dependence_findings(self, dependence, differing):
        findings = []
        if dependence.get('demonstrated') != bool(differing):
            findings.append('temporal_dependence.demonstrated does not match the ablation responses')
        if dependence.get('changed_by') != differing:
            findings.append('temporal_dependence.changed_by does not match the changed controls')
        if not differing:
            findings.append('no temporal dependence: removing the earlier events left the measured response and retained latch state unchanged')
        return findings

    def _probe_set_findings(self, scenario, probes):
        expected_probe_names = {'cue_ablation'}
        if scenario['reset_ms'] is not None:
            expected_probe_names.add('reset_ablation')
        if scenario['distractor_ms']:
            expected_probe_names.add('distractor_swap')
        findings = []
        if 'cue_ablation' not in probes:
            findings.append('the cue-ablation control is missing')
        if set(probes) != expected_probe_names:
            findings.append('memory control probes do not match the scenario controls')
        return findings

    def _distractor_invariant_findings(self, probes, baseline, measured):
        expected = probes['distractor_swap']['response'] == baseline['response'] if 'distractor_swap' in probes else None
        if measured.get('distractor_invariant') is not expected:
            return ['distractor_invariant does not match the distractor control']
        return []

    def _memory_control_findings(self, record):
        measured = record['result']['measured']
        baseline = measured['baseline']
        probes = measured['probes']
        differing = sorted((name for name in ('cue_ablation', 'reset_ablation') if name in probes and self.api._memory_ablation_changed(baseline, probes[name])))
        findings = self._dependence_findings(measured['temporal_dependence'], differing)
        findings.extend(self._probe_set_findings(record['scenario'], probes))
        findings.extend(self._distractor_invariant_findings(probes, baseline, measured))
        return findings

    def _memory_checks(self, record):
        measured = record['result']['measured']
        findings = self._memory_scenario_findings(record)
        trials = (('baseline', measured['baseline']), *sorted(measured['probes'].items()))
        for name, trial in trials:
            findings.extend(self._memory_trial_findings(record, name, trial))
        findings.extend(self._memory_control_findings(record))
        return findings
