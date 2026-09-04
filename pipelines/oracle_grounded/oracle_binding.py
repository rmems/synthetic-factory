"""Binding named runtimes to adapters through the environment.

Deployment is one environment variable per runtime: point
``SF_ORACLE_<RUNTIME>_CMD`` at a command that speaks ``sf-oracle/1`` and the
real runtime becomes the oracle with no code change. This module derives
those keys, probes what is honestly available, and picks the external or
reference adapter accordingly — loudly, never silently.
"""

import os
import shlex
import shutil

from .oracle_adapters import ExternalCommandOracle, OracleIdentity, ReferenceOracle
from .oracle_protocol import PROTOCOL, OracleError


def env_key(runtime):
    """Environment variable that binds a named runtime to this pipeline."""
    return "SF_ORACLE_" + str(runtime).upper().replace("-", "_").replace(".", "_") + "_CMD"


def probe_runtime(runtime, environ=None):
    """What we can honestly say about a named runtime's availability."""
    env = os.environ if environ is None else environ
    key = env_key(runtime)
    command = env.get(key, "").strip()
    on_path = shutil.which(str(runtime)) is not None
    if command:
        note = f"bound through {key}"
    elif on_path:
        note = (
            f"{runtime} is on PATH but no {PROTOCOL} binding is configured "
            f"({key} is unset); the reference implementation was used instead"
        )
    else:
        note = f"{runtime} is not installed and {key} is unset"
    return {
        "runtime": runtime,
        "binding_env": key,
        "bound": bool(command),
        "on_path": on_path,
        "note": note,
    }


def _parsed_binding(key, command):
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise OracleError(f"{key} contains a malformed command") from exc
    if not argv or not argv[0]:
        raise OracleError(f"{key} contains a command with no executable")
    return argv


def bind(runtime, identity, reference_fn, environ=None):
    """Return the external adapter when bound, else the reference adapter."""
    env = os.environ if environ is None else environ
    key = env_key(runtime)
    command = env.get(key, "").strip()
    if not command:
        return ReferenceOracle(identity, reference_fn, runtime)
    argv = _parsed_binding(key, command)
    external_identity = OracleIdentity(
        oracle_id=runtime,
        oracle_type=identity.oracle_type,
        description=f"{runtime} via {PROTOCOL}",
    )
    return ExternalCommandOracle(external_identity, runtime, argv)


def availability_report(runtimes, environ=None):
    """Environment summary for a record or manifest: what was bound, what was not.

    Deliberately free of interpreter or host details. This block is stored in
    every record and compared byte for byte by the golden fixture test, so it
    must describe the oracle binding and nothing about the machine. The code
    identity that actually matters is ``module_digest``.
    """
    diagnostics = [probe_runtime(runtime, environ) for runtime in runtimes]
    # PATH membership and prose diagnostics describe the current host, not the
    # oracle binding contract.  Keep them available through ``probe_runtime``
    # for operators but exclude them from canonical records and manifests.
    probes = [
        {
            "runtime": probe["runtime"],
            "binding_env": probe["binding_env"],
            "bound": probe["bound"],
        }
        for probe in diagnostics
    ]
    return {
        "protocol": PROTOCOL,
        "runtimes": probes,
        "all_bound": all(probe["bound"] for probe in probes),
        "unbound": [probe["runtime"] for probe in probes if not probe["bound"]],
    }
