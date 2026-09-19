"""Source identity and protocol constants for oracle adapters."""

import math
import re
import shutil
import subprocess  # nosec B404 -- fixed argv invokes the local git executable only
from pathlib import Path

from . import source_snapshot

PROTOCOL = "sf-oracle/1"
REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_SLUG = "rmems/synthetic-factory"
DEFAULT_TIMEOUT_S = 60
MAX_PROTOCOL_STDOUT_BYTES = 8 * 1024 * 1024
MAX_PROTOCOL_STDERR_BYTES = 1024 * 1024
PROTOCOL_READ_BYTES = 64 * 1024

# The code whose identity a measurement depends on: the simulators, adapters,
# family wiring, scenario RNG, and canonical form. `record.py` is excluded
# because it validates records and never produces a measurement. Editing any
# captured source changes `oracle.module_digest` and invalidates stale fixtures.
IMPLEMENTATION_SOURCES = source_snapshot.SOURCE_NAMES
MODULE_PATH = "pipelines/oracle_grounded"

_IMPLEMENTATION_SNAPSHOT = source_snapshot.loaded_snapshot(__package__)
_SOURCE_COMMIT_CACHE = {}
RUNTIME_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
SOURCE_COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class OracleError(RuntimeError):
    """A bound oracle could not produce an authoritative result."""


def _reject_json_constant(value):
    raise ValueError(f"non-finite JSON token {value}")


def _parse_finite_json_float(text):
    """parse_constant only sees the bare NaN/Infinity tokens; a numeric
    literal that merely overflows to inf (1e400) must be refused here."""
    parsed = float(text)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON numeric literal is not finitely representable: {text}")
    return parsed


def _reject_duplicate_object_keys(pairs):
    """``object_pairs_hook`` that fails closed on an ambiguous JSON object.

    Python's default decoder applies last-key-wins to a duplicate key, but a
    bound runtime is an external process: silently picking one interpretation
    of an ambiguous response could stamp a value into provenance that another
    conforming JSON reader would have read differently.
    """
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key {key!r}")
        value[key] = item
    return value


def module_digest():
    """Identify the immutable source bytes compiled for this measurement process."""
    return source_snapshot.snapshot_digest(_IMPLEMENTATION_SNAPSHOT)


def env_key(runtime):
    """Environment variable that binds a named runtime to this pipeline."""
    return "SF_ORACLE_" + str(runtime).upper().replace("-", "_").replace(".", "_") + "_CMD"


def is_runtime_commit(value):
    """Whether ``value`` is a resolved hexadecimal source revision."""
    return isinstance(value, str) and RUNTIME_COMMIT_RE.fullmatch(value) is not None


def is_source_commit(value):
    """Whether ``value`` is a fully resolved canonical source revision."""
    return isinstance(value, str) and SOURCE_COMMIT_RE.fullmatch(value) is not None


_UNRESOLVED = object()  # git could not answer; never reaches the cache


def _commit_answer(resolved, value):
    """The exact commit id a finished ``rev-parse`` answered, else ``None``."""
    if resolved.returncode != 0:
        return None
    canonical = resolved.stdout.strip()
    if canonical != value:
        return None
    if not is_source_commit(canonical):
        return None
    return canonical


def _ask_git(root, value):
    """Query git once. ``_UNRESOLVED`` marks a transient miss, never cached."""
    git = shutil.which("git")
    if git is None:
        return _UNRESOLVED
    try:
        resolved = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603 -- fixed git argv, no shell
            [git, "-C", str(root), "rev-parse", "--verify", f"{value}^{{commit}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return _UNRESOLVED
    return _commit_answer(resolved, value)


def resolve_source_commit(value, repo_root=None):
    """Return the canonical commit object id, or ``None`` when it is absent.

    Syntax alone is not provenance.  A full-length hexadecimal string is only
    a resolved source revision when the repository can prove that exact object
    exists and is a commit.
    """
    if not is_source_commit(value):
        return None
    root = Path(repo_root or REPO_ROOT)
    key = (str(root.resolve()), value)
    if key in _SOURCE_COMMIT_CACHE:
        return _SOURCE_COMMIT_CACHE[key]
    resolved = _ask_git(root, value)
    if resolved is _UNRESOLVED:
        return None
    # A definitive miss (git ran and said no) is cached too, so repeated
    # queries for the same absent commit cost one subprocess per process,
    # not one per record. Transient failures above are never cached.
    _SOURCE_COMMIT_CACHE[key] = resolved
    return resolved


def resolve_commit(repo_root=None):
    """(commit, dirty) for the working tree, or ('unknown', None) without git.

    ``unknown`` is rejected by ``record.validate_record``: a record whose code
    provenance cannot be established is not accepted.
    """
    root = Path(repo_root or REPO_ROOT)
    git = shutil.which("git")
    if git is None:
        return "unknown", None
    try:
        head = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603 -- fixed git argv, no shell
            [git, "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        if head.returncode != 0:
            return "unknown", None
        status = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603 -- fixed git argv, no shell
            [git, "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown", None
    dirty = bool(status.stdout.strip()) if status.returncode == 0 else None
    commit = head.stdout.strip()
    return (resolve_source_commit(commit, root) or "unknown"), dirty
