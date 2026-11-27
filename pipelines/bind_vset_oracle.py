"""Bind VSET patch evidence to a pinned pack and declared test suites.

This execution surface is deliberately separate from ``validate_vset``'s
legacy claimed-oracle check. It returns evidence that can support
``provisional``; it never changes a record or asserts ``validated``.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess  # nosec B404
import sys
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("bind_vset_oracle")
    from .vset_constants import pack_snapshot_hash
    from .vset_patch import apply_patch, record_patch
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "bind_vset_oracle"
    )
    from vset_constants import pack_snapshot_hash
    from vset_patch import apply_patch, record_patch


# Oracle packs are input data, not trusted local code. Their test processes get
# this fixed environment rather than the operator environment, which can carry
# credentials or machine-local Python overrides. ``PYTHONPATH`` is relative to
# the suite subprocess working directory (the copied pack root).
CHILD_ENV = {
    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "PYTHONPATH": "src",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "LC_ALL": "C.UTF-8",
}


def _hash(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _env_digest(env: Mapping[str, Any]) -> str:
    payload = json.dumps(
        env, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )
    return _hash(payload.encode("utf-8"))


def _declared_suites(value: Any) -> list[str] | None:
    if not isinstance(value, list) or not value:
        return None
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return None
        path = PurePosixPath(item)
        if path.is_absolute() or ".." in path.parts or not item.endswith(".py"):
            return None
        result.append(path.as_posix())
    return result


def _decode_output(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value or ""


def _clean_output(work: Path, value: str) -> str:
    # Temporary-copy paths are process noise. Normalizing them keeps the suite
    # result hash stable for the same pack, patch, code, and interpreter.
    return value.replace(str(work), "<pack>")


def _suite_result(work: Path, suites: list[str], timeout: float) -> dict[str, Any]:
    modules = [path[:-3].replace("/", ".") for path in suites]
    command = [sys.executable, "-m", "unittest", *modules]
    started = time.monotonic()
    try:
        completed = subprocess.run(  # nosec B603 - fixed interpreter/module argv, no shell
            command,
            cwd=work,
            env=dict(CHILD_ENV),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        stdout = _clean_output(work, completed.stdout)
        stderr = _clean_output(work, completed.stderr)
        exit_code = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = _clean_output(work, _decode_output(exc.stdout))
        stderr = _clean_output(work, _decode_output(exc.stderr))
        exit_code = None
        timed_out = True
    combined = json.dumps(
        {
            "command": command,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "stdout": stdout,
            "stderr": stderr,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "ok": exit_code == 0 and not timed_out,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "duration_seconds": round(time.monotonic() - started, 6),
        "result_hash": _hash(combined),
        "env_digest": _env_digest(CHILD_ENV),
    }


def _tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        rows.append(f"{path.relative_to(root).as_posix()}:{_hash(path.read_bytes())}")
    return _hash("\n".join(rows).encode("utf-8"))


def _actor_identity(actor: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    return tuple(actor.get(key) for key in ("model", "version", "run_id"))


def _conflated_role(record: Mapping[str, Any], oracle_actor: Mapping[str, str]) -> str | None:
    identity = _actor_identity(oracle_actor)
    for role in ("task_author", "solver"):
        other = record.get(role)
        if isinstance(other, Mapping) and _actor_identity(other) == identity:
            return role
    return None


def _suite_pair_result_hash(before: Mapping[str, Any], after: Mapping[str, Any]) -> str:
    pair = before["result_hash"] + after["result_hash"]
    return _hash(pair.encode("utf-8"))


def bind_vset_oracle(
    record: Mapping[str, Any],
    pack_dir: Path | str | None,
    *,
    oracle_actor: Mapping[str, str],
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Run declared suites before and after the record patch, failing closed.

    The binder only reads pack content and record patch/suite declarations. In
    particular it never consults ``solver.outcome`` or any solver-upgrade flag.
    """

    base: dict[str, Any] = {"schema_version": "oracle_bind_v1", "status_supported": "unbound"}
    if not isinstance(record, Mapping):
        base["reason"] = "record must be an object"
        return base
    if not isinstance(oracle_actor, Mapping) or any(
        not isinstance(oracle_actor.get(key), str) or not oracle_actor[key].strip()
        for key in ("model", "version", "run_id")
    ):
        base["reason"] = "invalid oracle actor identity"
        return base

    oracle = record.get("oracle")
    env = record.get("environment")
    payload = record.get("payload")
    if not isinstance(oracle, Mapping) or not isinstance(env, Mapping):
        base["reason"] = "missing oracle or environment envelope"
        return base
    if oracle.get("status") == "invalid":
        base["reason"] = "invalid records are not executed"
        return base

    reference = _declared_suites(oracle.get("reference_tests"))
    hidden = _declared_suites(oracle.get("hidden_tests"))
    if reference is None or hidden is None:
        base["reason"] = "explicit reference_tests and hidden_tests are required"
        return base
    if pack_dir is None or not Path(pack_dir).is_dir():
        base["reason"] = "repo pack is missing"
        return base

    pack = Path(pack_dir).resolve()
    try:
        snapshot = pack_snapshot_hash(pack)
    except (OSError, ValueError):
        base["reason"] = "repo pack snapshot cannot be read"
        return base
    if env.get("repo_snapshot_hash") != snapshot:
        base.update(pack_snapshot_hash=snapshot, reason="repo snapshot hash mismatch")
        return base

    declared = set(reference + hidden)
    if any(not (pack / relative).is_file() for relative in declared):
        base.update(pack_snapshot_hash=snapshot, reason="declared suite is missing from pack")
        return base
    patch = record_patch(record)
    if not isinstance(patch, Mapping):
        base.update(pack_snapshot_hash=snapshot, reason="record patch is missing")
        return base

    base.update(pack_snapshot_hash=snapshot, oracle_actor=dict(oracle_actor))
    conflated = _conflated_role(record, oracle_actor)
    if conflated is not None:
        base["reason"] = f"oracle actor identity is conflated with {conflated}"
        return base
    if isinstance(payload, Mapping) and payload.get("outcome") == "impossible":
        base["reason"] = "impossible task is not executed"
        return base

    try:
        with tempfile.TemporaryDirectory(prefix="vset-bind-") as tmp:
            root = Path(tmp)
            before_tree = root / "before"
            after_tree = root / "after"
            shutil.copytree(pack, before_tree)
            shutil.copytree(pack, after_tree)
            copied = (pack_snapshot_hash(before_tree), pack_snapshot_hash(after_tree))
            if copied != (snapshot, snapshot):
                base["reason"] = "copied pack snapshot mismatch"
                return base

            before_p2p = _suite_result(before_tree, reference, timeout)
            before_f2p = _suite_result(before_tree, hidden, timeout)
            apply_patch(after_tree, patch, protected=declared)
            after_p2p = _suite_result(after_tree, reference, timeout)
            after_f2p = _suite_result(after_tree, hidden, timeout)
            base.update(
                patched_tree_hash=_tree_hash(after_tree),
                env_digest=_env_digest(
                    {
                        "python": sys.executable,
                        "version": sys.version,
                        "platform": sys.platform,
                        "child": CHILD_ENV,
                    }
                ),
                pass_to_pass={
                    "before": before_p2p,
                    "after": after_p2p,
                    "result_hash": _suite_pair_result_hash(before_p2p, after_p2p),
                },
                fail_to_pass={
                    "before": before_f2p,
                    "after": after_f2p,
                    "result_hash": _suite_pair_result_hash(before_f2p, after_f2p),
                },
            )

            runs = (before_p2p, before_f2p, after_p2p, after_f2p)
            if any(run["timed_out"] for run in runs):
                base["status_supported"] = "unbound"
                base["reason"] = "declared suite execution timed out"
            elif (
                before_p2p["ok"]
                and after_p2p["ok"]
                and not before_f2p["ok"]
                and after_f2p["ok"]
            ):
                base["status_supported"] = "provisional"
            else:
                base["status_supported"] = "failed"
                base["reason"] = "F2P/P2P pre/post transition did not satisfy the binder contract"
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        base["status_supported"] = "unbound"
        base["reason"] = f"cannot execute or apply patch: {exc}"
    return base


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)


__all__ = ["CHILD_ENV", "bind_vset_oracle"]
