"""Code identity for measurements: module digest and commit resolution.

A record's authority rests on knowing exactly which code measured it. Two
identities matter: ``module_digest`` (a content hash over every source file
that can influence a measurement) and the repository commit (resolved through
git, never trusted from a string). Both fail closed: an unresolvable commit
is reported as ``unknown`` and rejected downstream by ``record``.
"""

import re
import shutil
import subprocess
from pathlib import Path

from . import canon

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_SLUG = "rmems/synthetic-factory"

# The code whose identity a measurement depends on: the simulators, the
# adapters, the family wiring that turns a stored scenario back into an oracle
# request, the scenario RNG, and the canonical form the numbers are stored in.
# Each split responsibility module is listed alongside its facade because the
# digest hashes file bytes, not import graphs. `record.py` and
# `schema_validation.py` are excluded because they validate records and never
# produce a measurement. Editing anything listed here changes
# `oracle.module_digest` and so invalidates every golden fixture that claims
# to have come from it.
IMPLEMENTATION_SOURCES = (
    "canon.py",
    "families.py",
    "family_common.py",
    "family_encoder.py",
    "family_neuron.py",
    "family_mesh.py",
    "family_credit.py",
    "family_memory.py",
    "generators.py",
    "gen_signals.py",
    "gen_encoder.py",
    "gen_neuron.py",
    "gen_mesh.py",
    "gen_credit.py",
    "gen_memory.py",
    "oracles.py",
    "oracle_protocol.py",
    "oracle_provenance.py",
    "oracle_adapters.py",
    "oracle_binding.py",
    "rng.py",
    "sim.py",
    "sim_core.py",
    "sim_encoder.py",
    "sim_neuron.py",
    "sim_mesh.py",
    "sim_credit.py",
    "sim_memory.py",
)
MODULE_PATH = "pipelines/oracle_grounded"

_MODULE_DIGEST_CACHE = {}
_SOURCE_COMMIT_CACHE = {}
RUNTIME_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
SOURCE_COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def module_digest():
    """sha256 over the oracle implementation sources, cached per process."""
    key = "implementation"
    if key not in _MODULE_DIGEST_CACHE:
        here = Path(__file__).resolve().parent
        _MODULE_DIGEST_CACHE[key] = canon.digest_files(
            str(here / name) for name in IMPLEMENTATION_SOURCES
        )
    return _MODULE_DIGEST_CACHE[key]


def is_runtime_commit(value):
    """Whether ``value`` is a resolved hexadecimal source revision."""
    return isinstance(value, str) and RUNTIME_COMMIT_RE.fullmatch(value) is not None


def is_source_commit(value):
    """Whether ``value`` is a fully resolved canonical source revision."""
    return isinstance(value, str) and SOURCE_COMMIT_RE.fullmatch(value) is not None


def _git_executable():
    return shutil.which("git")


def _rev_parse_commit(root, value):
    """Ask git to verify the object; ``None`` on any transient failure."""
    git = _git_executable()
    if git is None:
        return None
    try:
        return subprocess.run(
            [git, "-C", str(root), "rev-parse", "--verify", f"{value}^{{commit}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _canonical_commit_or_none(resolved, value):
    """The verified commit id, or ``None`` when git definitively said no."""
    canonical = resolved.stdout.strip()
    if resolved.returncode != 0:
        return None
    if canonical != value:
        return None
    if not is_source_commit(canonical):
        return None
    return canonical


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
    resolved = _rev_parse_commit(root, value)
    if resolved is None:
        return None
    # A definitive miss (git ran and said no) is cached too, so repeated
    # queries for the same absent commit cost one subprocess per process,
    # not one per record. Transient failures above are never cached.
    canonical = _canonical_commit_or_none(resolved, value)
    _SOURCE_COMMIT_CACHE[key] = canonical
    return canonical


def resolve_commit(repo_root=None):
    """(commit, dirty) for the working tree, or ('unknown', None) without git.

    ``unknown`` is rejected by ``record.validate_record``: a record whose code
    provenance cannot be established is not accepted.
    """
    root = Path(repo_root or REPO_ROOT)
    git = _git_executable()
    if git is None:
        return "unknown", None
    try:
        head = subprocess.run(
            [git, "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        if head.returncode != 0:
            return "unknown", None
        status = subprocess.run(
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
