"""The oracle boundary: adapters, availability probing, and provenance.

Issue #77 names six ground-truth runtimes (`axon-encoder`, `neuromod`,
`synaptic-mesh`, `limbic-critic`, `plasticity-lab`, and a validated recurrent
SNN). None of them are installed here. This package therefore defines the
boundary rather than pretending to cross it:

* ``ExternalCommandOracle`` speaks a small line protocol (``sf-oracle/1``) over
  stdin/stdout. Point ``SF_ORACLE_AXON_ENCODER_CMD`` at a command that speaks
  it and the real runtime becomes the oracle with no code change here.
* ``ReferenceOracle`` runs the deterministic simulator in ``sim.py`` and stamps
  ``implementation: "reference"`` so no record can pass itself off as output
  from the named runtime.

A bound external oracle never silently degrades to the reference one: if the
command fails, times out, or answers off-protocol, the run raises
``OracleError`` and the record is dropped. Curation fails closed.

The work lives in four responsibility modules; this facade re-exports the
whole surface: ``oracle_protocol`` (the wire protocol and its bounded child
process), ``oracle_provenance`` (module digest and commit resolution),
``oracle_adapters`` (the adapter classes), and ``oracle_binding``
(environment probing and adapter selection).
"""

import shutil  # noqa: F401  (re-exported: tests pin host-PATH probes via oracles.shutil)

from .oracle_adapters import (
    ChainOracle,
    ExternalCommandOracle,
    OracleAdapter,
    OracleIdentity,
    OracleRun,
    ReferenceOracle,
)
from .oracle_binding import availability_report, bind, env_key, probe_runtime
from .oracle_protocol import (
    DEFAULT_TIMEOUT_S,
    MAX_PROTOCOL_STDERR_BYTES,
    MAX_PROTOCOL_STDOUT_BYTES,
    PROTOCOL,
    PROTOCOL_READ_BYTES,
    OracleError,
    _run_protocol_command,
)
from .oracle_provenance import (
    IMPLEMENTATION_SOURCES,
    MODULE_PATH,
    REPO_ROOT,
    REPO_SLUG,
    RUNTIME_COMMIT_RE,
    SOURCE_COMMIT_RE,
    is_runtime_commit,
    is_source_commit,
    module_digest,
    resolve_commit,
    resolve_source_commit,
)

__all__ = [
    "ChainOracle",
    "DEFAULT_TIMEOUT_S",
    "ExternalCommandOracle",
    "IMPLEMENTATION_SOURCES",
    "MAX_PROTOCOL_STDERR_BYTES",
    "MAX_PROTOCOL_STDOUT_BYTES",
    "MODULE_PATH",
    "OracleAdapter",
    "OracleError",
    "OracleIdentity",
    "OracleRun",
    "PROTOCOL",
    "PROTOCOL_READ_BYTES",
    "REPO_ROOT",
    "REPO_SLUG",
    "RUNTIME_COMMIT_RE",
    "ReferenceOracle",
    "SOURCE_COMMIT_RE",
    "_run_protocol_command",
    "availability_report",
    "bind",
    "env_key",
    "is_runtime_commit",
    "is_source_commit",
    "module_digest",
    "probe_runtime",
    "resolve_commit",
    "resolve_source_commit",
    "shutil",
]
