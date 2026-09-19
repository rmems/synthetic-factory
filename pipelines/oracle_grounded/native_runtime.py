"""Explicit local Rust executable binding; dataset metadata never chooses commands."""

import hashlib
import os
from pathlib import Path
import shlex
import stat

from . import oracles
from .import_twins import bind_import_twin


def runtime_environ(executable=None, base=None):
    env = dict(os.environ if base is None else base)
    value = executable or env.get('SF_ORACLE_RUST_BIN')
    if not value:
        raise oracles.OracleError('SF_ORACLE_RUST_BIN or --oracle-rust-bin must name a prebuilt executable')
    path = Path(value).resolve()
    try:
        valid = stat.S_ISREG(path.stat().st_mode) and os.access(path, os.X_OK)
    except OSError:
        valid = False
    if not valid:
        raise oracles.OracleError('Rust oracle executable is missing or not executable')
    env['SF_ORACLE_RUST_BIN'] = str(path)
    for runtime in ('axon-encoder', 'neuromod'):
        env[oracles.env_key(runtime)] = shlex.quote(str(path))
    return env


def units_for(profile):
    # Shared with the native executable; checked again on each response.
    if profile == 'axon-stream-v1':
        return {'t_ms': 'millisecond', 'reconstruction': 'normalized signal',
                'spike_count': 'spikes', 'rmse': 'normalized signal'}
    if profile == 'neuromod-lif-v1':
        return {'spikes': 'millisecond', 'v_trace': 'crate membrane units',
                'spike_count': 'spikes', 'spike_count_delta': 'spikes'}
    raise ValueError('unsupported native profile')


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def adapter_source_digest():
    paths = ['Cargo.toml', 'rust/sf-oracle/Cargo.toml', 'rust/sf-oracle/build.rs']
    paths += [f'rust/sf-oracle/src/{name}.rs'
              for name in ('encoder', 'identity', 'main', 'neuron', 'protocol')]
    digest = hashlib.sha256()
    for relative in paths:
        payload = (oracles.REPO_ROOT / relative).read_bytes()
        digest.update(relative.encode('utf-8') + b'\0')
        digest.update(len(payload).to_bytes(8, 'big'))
        digest.update(payload)
    return digest.hexdigest()


class NativeOracle(oracles.ExternalCommandOracle):
    def run(self, family, request):
        try:
            before = file_digest(self.command[0])
            run = super().run(family, request)
            after = file_digest(self.command[0])
            identity = run.measured.get('identity', {})
            if before != after or identity.get('executable_sha256') != before:
                raise oracles.OracleError('Rust executable identity changed or mismatched')
            if identity.get('lock_sha256') != file_digest(oracles.REPO_ROOT / 'Cargo.lock'):
                raise oracles.OracleError('Rust executable was built with a different dependency lock')
            if identity.get('adapter_source_sha256') != adapter_source_digest():
                raise oracles.OracleError('Rust executable was built from different adapter sources')
            if oracles.resolve_source_commit(identity.get('adapter_revision')) is None:
                raise oracles.OracleError('Rust adapter source revision cannot be resolved')
            if run.units != units_for(request['configuration']['profile']):
                raise oracles.OracleError('Rust executable returned incompatible units')
            return run
        except (OSError, ValueError) as exc:
            raise oracles.OracleError('Rust runtime identity could not be verified') from exc


def adapter(runtime, oracle_type, environ=None):
    env = runtime_environ(base=environ)
    return NativeOracle(oracle_id=runtime, oracle_type=oracle_type,
                        description=f'{runtime} crate-native sf-oracle/1',
                        runtime=runtime, command=[env['SF_ORACLE_RUST_BIN']])


bind_import_twin(__name__)
