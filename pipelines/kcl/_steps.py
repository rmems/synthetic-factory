"""Step and record primitives shared by the KCL leftover episode scripts.

``step`` refuses a ``decision_basis`` without a reviewed prefix or a step with
an empty observation or reflection; ``episode_record`` appends provenance
``meta`` and refuses any record carrying a banned key or ``sim_or_real: real``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ._contract import (
    BANNED_KEYS,
    FACTORY,
    FINDING_BANNED,
    FINDING_USAGE,
    GENERATOR,
    bind_import_twin,
    refuse_when,
)

BASIS_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
BASIS_LIMIT = 240

__all__ = [
    "BASIS_LIMIT",
    "BASIS_PREFIXES",
    "Scene",
    "assert_clean",
    "bash",
    "clip",
    "edit",
    "episode_record",
    "read",
    "step",
]


def clip(text: str) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= BASIS_LIMIT:
        return compact
    return compact[: BASIS_LIMIT - 1].rstrip() + "…"


def step(
    n: int,
    basis: str,
    tool_call: dict[str, Any],
    observation: str,
    reflection: str,
) -> dict[str, Any]:
    clipped = clip(basis)
    refuse_when(
        not clipped.startswith(BASIS_PREFIXES),
        FINDING_USAGE,
        f"step {n} decision_basis prefix: {basis!r}",
    )
    refuse_when(not observation.strip() or not reflection.strip(), FINDING_USAGE, f"step {n} empty")
    return {
        "n": n,
        "decision_basis": clipped,
        "tool_call": tool_call,
        "observation": observation,
        "reflection": reflection,
    }


def bash(n: int, basis: str, cmd: str, obs: str, reflection: str) -> dict[str, Any]:
    return step(n, basis, {"name": "bash", "args": {"command": cmd}}, obs, reflection)


def read(n: int, basis: str, path: str, obs: str, reflection: str) -> dict[str, Any]:
    return step(n, basis, {"name": "read", "args": {"path": path}}, obs, reflection)


def edit(n: int, basis: str, args: dict[str, str], obs: str, reflection: str) -> dict[str, Any]:
    """``args`` is the edit tool's own ``{"path", "old", "new"}`` argument mapping."""

    return step(n, basis, {"name": "edit", "args": args}, obs, reflection)


def assert_clean(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        _assert_clean_mapping(obj, path)
        return
    if isinstance(obj, list):
        for index, item in enumerate(obj):
            assert_clean(item, f"{path}[{index}]")


def _assert_clean_mapping(obj: Mapping[str, Any], path: str) -> None:
    for key, val in obj.items():
        refuse_when(key in BANNED_KEYS, FINDING_BANNED, f"banned key {key} at {path}")
        refuse_when(
            key == "sim_or_real" and val == "real",
            FINDING_BANNED,
            f"sim_or_real real at {path}",
        )
        assert_clean(val, f"{path}.{key}")


def episode_record(
    episode: Mapping[str, Any], *, round_n: int, mill_id: str, plant_id: str
) -> dict[str, Any]:
    """``episode`` carries the record's own fields in order: id, goal, plan, steps,
    outcome, reward. Provenance ``meta`` is appended from the plant and round."""

    record = {
        **episode,
        "reward": dict(episode["reward"]),
        "meta": {
            "catalog_id": "kcl-plants-v1",
            "designed": True,
            "factory": FACTORY,
            "generator": GENERATOR,
            "kind": "episode",
            "mill_id": mill_id,
            "plant_id": plant_id,
            "round": round_n,
        },
    }
    assert_clean(record)
    return record


@dataclass(frozen=True)
class Scene:
    """The live names one episode's commands and observations interpolate."""

    ns: str
    app: str
    chart: str
    rs: str
    field: str


bind_import_twin(__name__)
