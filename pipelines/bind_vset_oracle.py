"""Bind VSET patch evidence to a pinned pack and declared test suites.

This surface delegates suite execution to the reviewed VSET oracle runner:
unittest grading stays in the parent, candidate code answers calls from an
isolated child interpreter, and every declared test id must be observed. The
binder only emits evidence that can support ``provisional``; it never changes
a record or asserts ``validated``.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, cast

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("bind_vset_oracle")
    from .vset_constants import normalize_identity, pack_snapshot_hash
    from .vset_oracle_exec import run_oracle
    from .vset_patch import apply_patch, pre_patches, record_patch
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "bind_vset_oracle"
    )
    from vset_constants import normalize_identity, pack_snapshot_hash
    from vset_oracle_exec import run_oracle
    from vset_patch import apply_patch, pre_patches, record_patch


@dataclass(frozen=True)
class _BindingContext:
    reference: list[str]
    hidden: list[str]
    pack: Path
    snapshot: str
    patch: Mapping[str, Any]
    pre_patch: Mapping[str, Any] | None


class _Unbound(Exception):
    def __init__(self, reason: str, **fields: Any) -> None:
        super().__init__(reason)
        self.reason = reason
        self.fields = fields


def _hash(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _canonical(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )


def _digest_mapping(value: Mapping[str, Any]) -> str:
    return _hash(_canonical(value).encode("utf-8"))


def _require(condition: object, reason: str, **fields: Any) -> None:
    if not condition:
        raise _Unbound(reason, **fields)


def _valid_suite_item(item: Any) -> str | None:
    if not isinstance(item, str):
        return None
    path = PurePosixPath(item)
    checks = (
        bool(item.strip()),
        not path.is_absolute(),
        ".." not in path.parts,
        item.endswith(".py"),
    )
    if not all(checks):
        return None
    return path.as_posix()


def _declared_suites(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    if not value:
        return None
    result = [_valid_suite_item(item) for item in value]
    if any(item is None for item in result):
        return None
    return [item for item in result if item is not None]


def _snapshot_covered(relative: str) -> bool:
    parts = PurePosixPath(relative).parts
    if not parts:
        return False
    if parts[0] in {"tasks", "PACK.json"}:
        return False
    return "__pycache__" not in parts


def _require_snapshot_coverage(suites: list[str], snapshot: str) -> None:
    if any(not _snapshot_covered(relative) for relative in suites):
        raise _Unbound(
            "declared suite is outside the pinned pack snapshot",
            pack_snapshot_hash=snapshot,
        )


def _tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        rows.append(f"{path.relative_to(root).as_posix()}:{_hash(path.read_bytes())}")
    return _hash("\n".join(rows).encode("utf-8"))


def _actor_token(actor: Mapping[str, Any], key: str) -> str:
    return normalize_identity(actor.get(key))


def _valid_actor(actor: Any) -> bool:
    if not isinstance(actor, Mapping):
        return False
    return all(_actor_token(actor, key) for key in ("model", "version", "run_id"))


def _require_actor(oracle_actor: Any) -> None:
    _require(_valid_actor(oracle_actor), "invalid oracle actor identity")


def _record_envelopes(
    record: Any,
) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Any]:
    _require(isinstance(record, Mapping), "record must be an object")
    oracle = record.get("oracle")
    env = record.get("environment")
    _require(isinstance(oracle, Mapping), "missing oracle or environment envelope")
    _require(isinstance(env, Mapping), "missing oracle or environment envelope")
    _require(oracle.get("status") != "invalid", "invalid records are not executed")
    return record, oracle, env, record.get("payload")


def _require_declared_suites(oracle: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    reference = _declared_suites(oracle.get("reference_tests"))
    hidden = _declared_suites(oracle.get("hidden_tests"))
    _require(reference is not None, "explicit reference_tests and hidden_tests are required")
    _require(hidden is not None, "explicit reference_tests and hidden_tests are required")
    return cast(list[str], reference), cast(list[str], hidden)


def _require_pack(pack_dir: Path | str | None, env: Mapping[str, Any]) -> tuple[Path, str]:
    _require(pack_dir is not None, "repo pack is missing")
    pack_input = cast(Path | str, pack_dir)
    _require(Path(pack_input).is_dir(), "repo pack is missing")
    pack = Path(pack_input).resolve()
    try:
        snapshot = pack_snapshot_hash(pack)
    except (OSError, ValueError) as exc:
        raise _Unbound("repo pack snapshot cannot be read") from exc
    _require(
        env.get("repo_snapshot_hash") == snapshot,
        "repo snapshot hash mismatch",
        pack_snapshot_hash=snapshot,
    )
    return pack, snapshot


def _require_patch(
    record: Mapping[str, Any], pack: Path, declared: set[str], snapshot: str
) -> Mapping[str, Any]:
    _require(
        all((pack / relative).is_file() for relative in declared),
        "declared suite is missing from pack",
        pack_snapshot_hash=snapshot,
    )
    patch = record_patch(record)
    _require(isinstance(patch, Mapping), "record patch is missing", pack_snapshot_hash=snapshot)
    return patch


def _role_identity(record: Mapping[str, Any], role: str) -> Mapping[str, Any]:
    actor = record.get(role)
    reason = f"missing or invalid {role} actor identity"
    _require(isinstance(actor, Mapping), reason)
    _require(_valid_actor(actor), reason)
    return actor


def _conflated_role(record: Mapping[str, Any], oracle_actor: Mapping[str, str]) -> str | None:
    oracle_run = _actor_token(oracle_actor, "run_id")
    oracle_key = tuple(_actor_token(oracle_actor, key) for key in ("model", "version", "run_id"))
    for role in ("task_author", "solver"):
        other = _role_identity(record, role)
        other_key = tuple(_actor_token(other, key) for key in ("model", "version", "run_id"))
        if oracle_run == _actor_token(other, "run_id"):
            return role
        if oracle_key == other_key:
            return role
    return None


def _require_executable_task(
    record: Mapping[str, Any], payload: Any, oracle_actor: Mapping[str, str], snapshot: str
) -> None:
    try:
        conflated = _conflated_role(record, oracle_actor)
    except _Unbound as exc:
        raise _Unbound(exc.reason, pack_snapshot_hash=snapshot) from exc
    if conflated is not None:
        raise _Unbound(
            f"oracle actor identity is conflated with {conflated}",
            pack_snapshot_hash=snapshot,
        )
    if not isinstance(payload, Mapping):
        return
    if payload.get("outcome") == "impossible":
        raise _Unbound("impossible task is not executed", pack_snapshot_hash=snapshot)


def _binding_context(
    record: Any, pack_dir: Path | str | None, oracle_actor: Mapping[str, str]
) -> _BindingContext:
    _require_actor(oracle_actor)
    record_map, oracle, env, payload = _record_envelopes(record)
    reference, hidden = _require_declared_suites(oracle)
    pack, snapshot = _require_pack(pack_dir, env)
    declared = set(reference + hidden)
    _require_snapshot_coverage(reference + hidden, snapshot)
    patch = _require_patch(record_map, pack, declared, snapshot)
    _require_executable_task(record_map, payload, oracle_actor, snapshot)
    initial = pre_patches(record_map)
    pre_patch = initial[0] if initial else None
    return _BindingContext(reference, hidden, pack, snapshot, patch, pre_patch)


def _patched_tree_hash(context: _BindingContext) -> str:
    with tempfile.TemporaryDirectory(prefix="vset-bind-tree-") as tmp:
        patched = Path(tmp) / "pack"
        shutil.copytree(context.pack, patched)
        apply_patch(
            patched,
            context.patch,
            protected=set(context.reference + context.hidden),
        )
        return _tree_hash(patched)


def _reference_result(
    pack: Path, suites: list[str], patch: Mapping[str, Any] | None
) -> dict[str, Any]:
    execution = run_oracle(pack, patch=patch, reference_tests=suites, hidden_suite=None)
    return dict(execution["reference"])


def _hidden_result(
    pack: Path, suites: list[str], patch: Mapping[str, Any] | None
) -> dict[str, Any]:
    execution = run_oracle(
        pack,
        patch=patch,
        reference_tests=[],
        hidden_suite={"tests": suites},
    )
    return dict(execution["hidden"])


def _suite_pair_result_hash(before: Mapping[str, Any], after: Mapping[str, Any]) -> str:
    pair = before["result_hash"] + after["result_hash"]
    return _hash(pair.encode("utf-8"))


def _suite_pair(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "before": before,
        "after": after,
        "result_hash": _suite_pair_result_hash(before, after),
    }


def _oracle_environment_digest() -> str:
    return _digest_mapping(
        {
            "python": sys.executable,
            "version": sys.version,
            "platform": sys.platform,
            "runner": "vset_oracle_exec.run_oracle",
            "candidate_execution": "isolated child interpreter",
        }
    )


def _execute_binding(context: _BindingContext) -> dict[str, Any]:
    before_p2p = _reference_result(context.pack, context.reference, context.pre_patch)
    before_f2p = _hidden_result(context.pack, context.hidden, context.pre_patch)
    after_p2p = _reference_result(context.pack, context.reference, context.patch)
    after_f2p = _hidden_result(context.pack, context.hidden, context.patch)
    return {
        "patched_tree_hash": _patched_tree_hash(context),
        "env_digest": _oracle_environment_digest(),
        "pass_to_pass": _suite_pair(before_p2p, after_p2p),
        "fail_to_pass": _suite_pair(before_f2p, after_f2p),
    }


def _transition_status(evidence: Mapping[str, Any]) -> tuple[str, str | None]:
    p2p = evidence["pass_to_pass"]
    f2p = evidence["fail_to_pass"]
    failure = "failed", "F2P/P2P pre/post transition did not satisfy the binder contract"
    if not p2p["before"]["ok"]:
        return failure
    if not p2p["after"]["ok"]:
        return failure
    if f2p["before"]["ok"]:
        return failure
    if not f2p["after"]["ok"]:
        return failure
    return "provisional", None


def bind_vset_oracle(
    record: Mapping[str, Any],
    pack_dir: Path | str | None,
    *,
    oracle_actor: Mapping[str, str],
) -> dict[str, Any]:
    """Run declared suites before and after the record patch, failing closed.

    The reviewed oracle runner enforces its own fixed child-interpreter
    timeout; this binder never consults ``solver.outcome`` or any
    solver-upgrade flag.
    """

    base: dict[str, Any] = {"schema_version": "oracle_bind_v1", "status_supported": "unbound"}
    if isinstance(oracle_actor, Mapping):
        base["oracle_actor"] = dict(oracle_actor)
    try:
        context = _binding_context(record, pack_dir, oracle_actor)
    except _Unbound as refusal:
        base.update(refusal.fields)
        base["reason"] = refusal.reason
        return base

    base.update(pack_snapshot_hash=context.snapshot, oracle_actor=dict(oracle_actor))
    try:
        evidence = _execute_binding(context)
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


__all__ = ["bind_vset_oracle"]
