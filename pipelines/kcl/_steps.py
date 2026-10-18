"""Step and record primitives shared by the KCL leftover episode scripts.

``step`` refuses a ``decision_basis`` without a reviewed prefix or a step with
an empty observation or reflection; ``episode_record`` appends provenance
``meta`` and refuses any record carrying a banned key or ``sim_or_real: real``.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any, NamedTuple

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
    "Observed",
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


class Observed(NamedTuple):
    """What a step's tool call returned and the agent's conclusion from it."""

    observation: str
    reflection: str


def step(n: int, basis: str, tool_call: dict[str, Any], observed: Observed) -> dict[str, Any]:
    observation, reflection = observed
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


def bash(n: int, basis: str, cmd: str, observed: Observed) -> dict[str, Any]:
    return step(n, basis, {"name": "bash", "args": {"command": cmd}}, observed)


def read(n: int, basis: str, path: str, observed: Observed) -> dict[str, Any]:
    return step(n, basis, {"name": "read", "args": {"path": path}}, observed)


def edit(n: int, basis: str, args: dict[str, str], observed: Observed) -> dict[str, Any]:
    """``args`` is the edit tool's own ``{"path", "old", "new"}`` argument mapping."""

    return step(n, basis, {"name": "edit", "args": args}, observed)


def assert_clean(obj: Any, path: str = "") -> None:
    # The walk recurses only here; the generators below run their checks lazily between
    # children, so the refusal order and one frame per nesting level match the original.
    for child, child_path in _clean_children(obj, path):
        assert_clean(child, child_path)


def _clean_children(obj: Any, path: str) -> Iterable[tuple[Any, str]]:
    if isinstance(obj, dict):
        return _checked_items(obj, path)
    if isinstance(obj, list):
        return ((item, f"{path}[{index}]") for index, item in enumerate(obj))
    return ()


def _checked_items(obj: Mapping[str, Any], path: str) -> Iterator[tuple[Any, str]]:
    """Each value with its path, after refusing a banned key or real-world provenance."""

    for key, val in obj.items():
        refuse_when(key in BANNED_KEYS, FINDING_BANNED, f"banned key {key} at {path}")
        refuse_when(
            key == "sim_or_real" and val == "real",
            FINDING_BANNED,
            f"sim_or_real real at {path}",
        )
        yield val, f"{path}.{key}"


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
