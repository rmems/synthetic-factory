"""Caller-scoped authority to replay native measurements with a chosen binary.

A record never selects its executable. Pure admission has no active authority,
while explicitly configured compose, validation, and export calls propagate it
through their nested replay and audit operations without mutating os.environ.
"""

from contextlib import contextmanager
from contextvars import ContextVar

from .import_twins import bind_import_twin

_REPLAY_ENV = ContextVar("oracle_native_replay_environment", default=None)


def runtime_environ(executable):
    from .native_runtime import runtime_environ as resolve
    from .oracles import OracleError

    try:
        return resolve(executable, base={})
    except OracleError as exc:
        raise ValueError(str(exc)) from exc


def replay_environ():
    """Return an isolated copy of explicit caller authority, or no authority."""
    active = _REPLAY_ENV.get()
    return None if active is None else dict(active)


@contextmanager
def runtime_gate(executable=None):
    """Activate one explicit binary; default nested operations inherit scope."""
    if executable is None:
        yield
        return
    environment = runtime_environ(executable)
    token = _REPLAY_ENV.set(dict(environment))
    try:
        yield
    finally:
        _REPLAY_ENV.reset(token)


def is_native_record(item):
    from .native_profiles import PROFILES

    scenario = item.get("scenario")
    if not isinstance(scenario, dict):
        return False
    family = item.get("family")
    return family in PROFILES and scenario.get("profile") == PROFILES[family]


bind_import_twin(__name__)
