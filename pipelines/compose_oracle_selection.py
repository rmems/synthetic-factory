"""Explicit training selection over a fully authenticated oracle source run."""

from dataclasses import replace
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling('compose_oracle_selection')
    from .compose_contract import ComposeError
else:
    getattr(sys.modules.get('pipelines'), '_join_package_sibling', lambda name: None)(
        'compose_oracle_selection'
    )
    from compose_contract import ComposeError

NAME = 'oracle-training-selection'
VERSION = 1
MODES = ('all', 'eligible-training')
REASON = 'compose.oracle_training_ineligible'


def require_mode(mode):
    if not isinstance(mode, str) or mode not in MODES:
        raise ComposeError('oracle selection must be all or eligible-training')
    return mode


def descriptor(mode):
    require_mode(mode)
    return {'name': NAME, 'version': VERSION, 'mode': mode}


def _integral_version(version):
    """Whether a declared selection version is a real int, never a bool."""
    return isinstance(version, int) and not isinstance(version, bool)


def published_mode(summary):
    if 'oracle_selection' not in summary:
        return 'all'
    supplied = summary['oracle_selection']
    expected = descriptor('eligible-training')
    if supplied != expected:
        raise ComposeError('COMPOSE.json: invalid oracle selection declaration')
    if not _integral_version(supplied.get('version')):
        raise ComposeError('COMPOSE.json: invalid oracle selection declaration')
    return 'eligible-training'


def require_authenticated_source(mode, members, physical_paths):
    require_mode(mode)
    if mode == 'all':
        return
    if not physical_paths:
        raise ComposeError('oracle training selection requires a complete authenticated oracle run')
    if set(members) != set(physical_paths):
        raise ComposeError('oracle training selection does not cover every source member')


def _fresh_admission(decision):
    identity = next((stage.get('detail', {}) for stage in decision.stages
                     if stage.get('lane') == 'identity'), {})
    authority = identity.get('procedural_authority', {})
    eligible = authority.get('eligible_training_candidate')
    reasons = authority.get('ineligibility_reasons')
    if decision.record is None:
        raise ComposeError('oracle selection requires a valid retained source record')
    if not isinstance(eligible, bool):
        raise ComposeError('oracle selection requires freshly validated identity admission')
    if not isinstance(reasons, list):
        raise ComposeError('oracle selection requires fresh admission reasons')
    return eligible, reasons


def _selection_stage(mode, eligible, reasons):
    return {
        'lane': 'selection', 'transform_name': NAME, 'transform_version': VERSION,
        'action': 'retained' if eligible else 'excluded',
        'reason_codes': [] if eligible else [REASON],
        'detail': {'mode': mode, 'eligible_training_candidate': eligible,
                   'ineligibility_reasons': list(reasons)},
    }


def apply_selection(decision, mode):
    """Consume fresh identity admission evidence, never a record's eligibility claim."""
    if mode == 'all':
        return decision
    require_mode(mode)
    eligible, reasons = _fresh_admission(decision)
    stages = (*decision.stages, _selection_stage(mode, eligible, reasons))
    if eligible:
        return replace(decision, stages=stages)
    return replace(decision, action='excluded', record=None, reason_codes=(REASON,),
                   stages=stages, output_id=None, reward_sidecar=None)


if __package__:
    _expose_package_sibling(__name__)
