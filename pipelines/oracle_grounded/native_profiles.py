"""Versioned crate-native proposals; never relabel reference model physics."""

from . import family_common
from .import_twins import bind_import_twin

PROFILES = {
    family_common.ENCODER_FAMILY: 'axon-stream-v1',
    family_common.NEURON_FAMILY: 'neuromod-lif-v1',
}


def propose_encoder(rng):
    return ({'profile': 'axon-stream-v1',
             'parameters': {'sample_ms': 10.0, 'rate_hz': 100.0,
                            'delta_threshold': 0.1},
             'signal': [rng.uniform(0.0, 1.0) for _ in range(64)]}, None, None)


def propose_neuron(rng):
    scenario = {'profile': 'neuromod-lif-v1',
                'parameters': {'dt_ms': 1.0, 'threshold': rng.uniform(0.3, 0.8),
                               'decay': rng.uniform(0.05, 0.25), 'input_scale': 0.5},
                'signal': [rng.uniform(0.0, 1.0) for _ in range(64)]}
    intervention = {'parameter': rng.choice(['threshold', 'decay', 'input_scale']),
                    'factor': rng.choice([0.5, 1.5])}
    return scenario, intervention, None


def build_request(scenario, intervention):
    return {'configuration': {'profile': scenario['profile'],
                              'parameters': scenario['parameters'],
                              'intervention': intervention},
            'data': {'signal': scenario['signal']}}


def score(_record):
    return None


def spec_for(family, profile):
    from . import native_checks, native_runtime

    if PROFILES.get(family) != profile:
        raise ValueError('unsupported crate-native family/profile combination')
    encoder = family == family_common.ENCODER_FAMILY
    runtime = 'axon-encoder' if encoder else 'neuromod'
    oracle_type = 'spike-encoder' if encoder else 'neuron-simulation'
    return family_common.FamilySpec(
        name=family, runtimes=(runtime,), oracle_type=oracle_type,
        units=native_runtime.units_for(profile),
        propose=propose_encoder if encoder else propose_neuron,
        build_request=build_request,
        build_oracle=lambda environ: native_runtime.adapter(runtime, oracle_type, environ),
        checks=native_checks.checks, score=score,
    )


bind_import_twin(__name__)
