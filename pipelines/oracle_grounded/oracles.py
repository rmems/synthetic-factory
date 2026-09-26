"""The oracle boundary: authenticated adapters, bindings, and provenance.

The implementation is separated into source identity, process transport,
adapters, and binding policy. This facade preserves the established API.
"""

from . import oracle_core as _core
from . import oracle_protocol as _protocol
from . import oracle_adapters as _adapters
from . import oracle_binding as _binding

PROTOCOL = _core.PROTOCOL
REPO_ROOT = _core.REPO_ROOT
REPO_SLUG = _core.REPO_SLUG
DEFAULT_TIMEOUT_S = _core.DEFAULT_TIMEOUT_S
MAX_PROTOCOL_STDOUT_BYTES = _core.MAX_PROTOCOL_STDOUT_BYTES
MAX_PROTOCOL_STDERR_BYTES = _core.MAX_PROTOCOL_STDERR_BYTES
PROTOCOL_READ_BYTES = _core.PROTOCOL_READ_BYTES
IMPLEMENTATION_SOURCES = _core.IMPLEMENTATION_SOURCES
MODULE_PATH = _core.MODULE_PATH
RUNTIME_COMMIT_RE = _core.RUNTIME_COMMIT_RE
SOURCE_COMMIT_RE = _core.SOURCE_COMMIT_RE
OracleError = _core.OracleError
module_digest = _core.module_digest
env_key = _core.env_key
is_runtime_commit = _core.is_runtime_commit
is_source_commit = _core.is_source_commit
resolve_source_commit = _core.resolve_source_commit
resolve_commit = _core.resolve_commit
OracleRun = _adapters.OracleRun
OracleAdapter = _adapters.OracleAdapter
OracleIdentity = _adapters.OracleIdentity
ReferenceOracle = _adapters.ReferenceOracle
ExternalCommandOracle = _adapters.ExternalCommandOracle
ChainOracle = _binding.ChainOracle
probe_runtime = _binding.probe_runtime
bind = _binding.bind
availability_report = _binding.availability_report
_run_protocol_command = _protocol._run_protocol_command

# Compatibility for focused tests that patch the transport/source modules.
subprocess = _protocol.subprocess
threading = _protocol.threading
time = _protocol.time
select = _protocol.select
os = _protocol.os
signal = _protocol.signal
shutil = _binding.shutil
