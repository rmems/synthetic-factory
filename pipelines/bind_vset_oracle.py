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
from dataclasses import dataclass
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


@dataclass(frozen=True)
class _BindingContext:
    record: Mapping[str, Any]
    payload: Any
    reference: list[str]
    hidden: list[str]
    pack: Path
    snapshot: str
    patch: Mapping[str, Any]


class _Unbound(Exception):
    def __init__(self, reason: str, **fields: Any) -> None:
        super().__init__(reason)
        self.reason = reason
        self.fields = fields


def _hash(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _env_digest(env: Mapping[str, Any]) -> str:
    payload = json.dumps(
        env, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )
    return _hash(payload.encode("utf-8"))


def _valid_suite_item(item: Any) -> str | None:
    if not isinstance(item, str) or not item.strip():
        return None
    path = PurePosixPath(item)
    if path.is_absolute() or ".." in path.parts or not item.endswith(".py"):
        return None
    return path.as_posix()


def _declared_suites(value: Any) -> list[str] | None:
    if not isinstance(value, list) or not value:
        return None
    result = [_valid_suite_item(item) for item in value]
    if any(item is None for item in result):
        return None
    return [item for item in result if item is not None]


def _decode_output(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value or ""


def _clean_output(work: Path, value: str) -> str:
    # Temporary-copy paths are process noise. Normalizing them keeps the suite
    # result hash stable for the same pack, patch, code, and interpreter.
    return value.replace(str(work), "<pack>")


def _completed_suite(completed: subprocess.CompletedProcess[str], work: Path) -> dict[str, Any]:
    return {
        "exit_code": completed.returncode,
        "timed_out": False,
        "stdout": _clean_output(work, completed.stdout),
        "stderr": _clean_output(work, completed.stderr),
    }


def _timed_out_suite(exc: subprocess.TimeoutExpired, work: Path) -> dict[str, Any]:
    return {
        "exit_code": None,
        "timed_out": True,
        "stdout": _clean_output(work, _decode_output(exc.stdout)),
        "stderr": _clean_output(work, _decode_output(exc.stderr)),
    }


def _run_suite_process(work: Path, modules: list[str], timeout: float) -> dict[str, Any]:
    argv = [sys.executable, "-m", "unittest", *modules]
    try:
        completed = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603
            argv,
            cwd=work,
            env=dict(CHILD_ENV),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        outcome = _completed_suite(completed, work)
    except subprocess.TimeoutExpired as exc:
        outcome = _timed_out_suite(exc, work)
    outcome["command"] = argv
    return outcome


def _suite_result(work: Path, suites: list[str], timeout: float) -> dict[str, Any]:
    modules = [path[:-3].replace("/", ".") for path in suites]
    started = time.monotonic()
    outcome = _run_suite_process(work, modules, timeout)
    command = outcome.pop("command")
    combined = json.dumps(
        {"command": command, **outcome},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "ok": outcome["exit_code"] == 0 and not outcome["timed_out"],
        **outcome,
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


def _require_actor(oracle_actor: Any) -> None:
    valid = isinstance(oracle_actor, Mapping) and all(
        isinstance(oracle_actor.get(key), str) and oracle_actor[key].strip()
        for key in ("model", "version", "run_id")
    )
    if not valid:
        raise _Unbound("invalid oracle actor identity")


def _record_envelopes(
    record: Any,
) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Any]:
    if not isinstance(record, Mapping):
        raise _Unbound("record must be an object")
    oracle = record.get("oracle")
    env = record.get("environment")
    if not isinstance(oracle, Mapping) or not isinstance(env, Mapping):
        raise _Unbound("missing oracle or environment envelope")
    if oracle.get("status") == "invalid":
        raise _Unbound("invalid records are not executed")
    return record, oracle, env, record.get("payload")


def _require_declared_suites(oracle: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    reference = _declared_suites(oracle.get("reference_tests"))
    hidden = _declared_suites(oracle.get("hidden_tests"))
    if reference is None or hidden is None:
        raise _Unbound("explicit reference_tests and hidden_tests are required")
    return reference, hidden


def _require_pack(pack_dir: Path | str | None, env: Mapping[str, Any]) -> tuple[Path, str]:
    if pack_dir is None or not Path(pack_dir).is_dir():
        raise _Unbound("repo pack is missing")
    pack = Path(pack_dir).resolve()
    try:
        snapshot = pack_snapshot_hash(pack)
    except (OSError, ValueError) as exc:
        raise _Unbound("repo pack snapshot cannot be read") from exc
    if env.get("repo_snapshot_hash") != snapshot:
        raise _Unbound("repo snapshot hash mismatch", pack_snapshot_hash=snapshot)
    return pack, snapshot


def _require_patch(
    record: Mapping[str, Any], pack: Path, declared: set[str], snapshot: str
) -> Mapping[str, Any]:
    if any(not (pack / relative).is_file() for relative in declared):
        raise _Unbound("declared suite is missing from pack", pack_snapshot_hash=snapshot)
    patch = record_patch(record)
    if not isinstance(patch, Mapping):
        raise _Unbound("record patch is missing", pack_snapshot_hash=snapshot)
    return patch


def _require_executable_task(
    record: Mapping[str, Any], payload: Any, oracle_actor: Mapping[str, str], snapshot: str
) -> None:
    conflated = _conflated_role(record, oracle_actor)
    if conflated is not None:
        raise _Unbound(
            f"oracle actor identity is conflated with {conflated}",
            pack_snapshot_hash=snapshot,
        )
    if isinstance(payload, Mapping) and payload.get("outcome") == "impossible":
        raise _Unbound("impossible task is not executed", pack_snapshot_hash=snapshot)


def _binding_context(
    record: Any, pack_dir: Path | str | None, oracle_actor: Mapping[str, str]
) -> _BindingContext:
    _require_actor(oracle_actor)
    record_map, oracle, env, payload = _record_envelopes(record)
    reference, hidden = _require_declared_suites(oracle)
    pack, snapshot = _require_pack(pack_dir, env)
    declared = set(reference + hidden)
    patch = _require_patch(record_map, pack, declared, snapshot)
    _require_executable_task(record_map, payload, oracle_actor, snapshot)
    return _BindingContext(record_map, payload, reference, hidden, pack, snapshot, patch)


def _copy_pack_trees(root: Path, pack: Path, snapshot: str) -> tuple[Path, Path]:
    before_tree = root / "before"
    after_tree = root / "after"
    shutil.copytree(pack, before_tree)
    shutil.copytree(pack, after_tree)
    copied = (pack_snapshot_hash(before_tree), pack_snapshot_hash(after_tree))
    if copied != (snapshot, snapshot):
        raise _Unbound("copied pack snapshot mismatch", pack_snapshot_hash=snapshot)
    return before_tree, after_tree


def _oracle_environment_digest() -> str:
    return _env_digest(
        {
            "python": sys.executable,
            "version": sys.version,
            "platform": sys.platform,
            "child": CHILD_ENV,
        }
    )


def _suite_pair(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "before": before,
        "after": after,
        "result_hash": _suite_pair_result_hash(before, after),
    }


def _execute_binding(context: _BindingContext, timeout: float) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="vset-bind-") as tmp:
        before_tree, after_tree = _copy_pack_trees(Path(tmp), context.pack, context.snapshot)
        before_p2p = _suite_result(before_tree, context.reference, timeout)
        before_f2p = _suite_result(before_tree, context.hidden, timeout)
        apply_patch(after_tree, context.patch, protected=set(context.reference + context.hidden))
        after_p2p = _suite_result(after_tree, context.reference, timeout)
        after_f2p = _suite_result(after_tree, context.hidden, timeout)
        return {
            "patched_tree_hash": _tree_hash(after_tree),
            "env_digest": _oracle_environment_digest(),
            "pass_to_pass": _suite_pair(before_p2p, after_p2p),
            "fail_to_pass": _suite_pair(before_f2p, after_f2p),
        }


def _transition_status(evidence: Mapping[str, Any]) -> tuple[str, str | None]:
    pairs = (evidence["pass_to_pass"], evidence["fail_to_pass"])
    runs = [pair[side] for pair in pairs for side in ("before", "after")]
    if any(run["timed_out"] for run in runs):
        return "unbound", "declared suite execution timed out"
    p2p = evidence["pass_to_pass"]
    f2p = evidence["fail_to_pass"]
    if (
        p2p["before"]["ok"]
        and p2p["after"]["ok"]
        and not f2p["before"]["ok"]
        and f2p["after"]["ok"]
    ):
        return "provisional", None
    return "failed", "F2P/P2P pre/post transition did not satisfy the binder contract"


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
    try:
        context = _binding_context(record, pack_dir, oracle_actor)
    except _Unbound as refusal:
        base.update(refusal.fields)
        base["reason"] = refusal.reason
        return base

    base.update(pack_snapshot_hash=context.snapshot, oracle_actor=dict(oracle_actor))
    try:
        evidence = _execute_binding(context, timeout)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, _Unbound) as exc:
        base["reason"] = f"cannot execute or apply patch: {exc}"
        return base

    base.update(evidence)
    status, reason = _transition_status(evidence)
    base["status_supported"] = status
    if reason is not None:
        base["reason"] = reason
    return base


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)


__all__ = ["CHILD_ENV", "bind_vset_oracle"]
