#!/usr/bin/env python3
"""Execute simulator replay against authenticated private files, never cached modules."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_simulator_process")
    from .curate_identity_json import IdentityCurationError
    from .curate_identity_registry_sources import simulator_source_snapshot
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_simulator_process"
    )
    from curate_identity_json import IdentityCurationError
    from curate_identity_registry_sources import simulator_source_snapshot

_WORKER = Path(__file__).with_name("curate_identity_simulator_worker.py")
_MAX_RESULT_BYTES = 1_048_576
_REPLAY_TIMEOUT = 60


def _materialize(root, snapshot):
    for relative, payload in snapshot.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def _run_worker(root, coordinates):
    seed, index, stamp = coordinates
    command = [sys.executable, "-I", str(_WORKER), str(root / "pipelines"),
               str(seed), str(index), stamp]
    with tempfile.TemporaryFile(dir=root) as output, tempfile.TemporaryFile(dir=root) as errors:
        completed = subprocess.run(
            command, stdout=output, stderr=errors, check=False,
            timeout=_REPLAY_TIMEOUT, cwd=root, env={"TMPDIR": str(root)},
        )
        if completed.returncode:
            raise IdentityCurationError("isolated fault-recovery replay refused")
        output.seek(0)
        payload = output.read(_MAX_RESULT_BYTES + 1)
    if len(payload) > _MAX_RESULT_BYTES:
        raise IdentityCurationError("isolated fault-recovery replay result exceeds its bound")
    return json.loads(payload)


def replay_coordinate(coordinates):
    snapshot = simulator_source_snapshot()
    try:
        with tempfile.TemporaryDirectory(prefix="simulator-replay-") as temporary:
            root = Path(temporary)
            _materialize(root, snapshot)
            return _run_worker(root, coordinates)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise IdentityCurationError(f"isolated fault-recovery replay failed: {exc}") from exc


if __package__:
    _expose_package_sibling(__name__)
