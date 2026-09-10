#!/usr/bin/env python3
"""Lineage, structural groups and the split policy of the code-repair catalog.

A program's lineage is its identity; its group joins every program that must
never be separated by a split: programs extracted from the same upstream file,
programs whose canonical structure is identical (identifiers renamed, docstring
removed, constants kept), and programs linked as each other's reference. The
split of a group is assigned before any variant exists, with the consumer's
own bucket function (Agoge's ``sha256-atomic-bucket-v1``: SHA-256 over the
algorithm, seed, salt and anchor, modulo the total weight) so the factory's
assignment and the consumer's re-derivation agree. The policy is pinned in the
catalog by digest; a drift is a catalog finding.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, oc

SPLIT_ALGORITHM = "sha256-atomic-bucket-v1"
SPLITS = ("train", "validation", "held_out")
_DROPPED_FIELDS = frozenset({"annotation", "returns", "type_comment", "type_params"})

__all__ = [
    "SPLITS", "SPLIT_ALGORITHM", "SplitPolicy", "anchor_for", "bucket_split", "canonical_ast",
    "group_ids", "structure_digest",
]


@dataclass(frozen=True)
class SplitPolicy:
    """The consumer's bucket policy, as pinned in ``CATALOG.json``."""

    algorithm: str
    seed: int
    salt: str
    train: int
    validation: int
    held_out: int

    @property
    def total(self) -> int:
        return self.train + self.validation + self.held_out

    @property
    def weights(self) -> dict[str, int]:
        return {"train": self.train, "validation": self.validation, "held_out": self.held_out}

    def as_json(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm, "seed": self.seed, "salt": self.salt,
            "weights": {
                "train": self.train, "validation": self.validation, "held_out": self.held_out,
            },
        }

    @property
    def sha256(self) -> str:
        return hashlib.sha256(oc.canonical_json(self.as_json()).encode("utf-8")).hexdigest()

    @classmethod
    def from_json(cls, payload: Any) -> SplitPolicy:
        cv.refuse_when(
            not isinstance(payload, dict) or not isinstance(payload.get("weights"), dict),
            cv.FINDING_SPLIT_POLICY_INVALID, "split_policy must be an object with weights",
        )
        weights = payload["weights"]
        fields = (
            payload.get("algorithm"), payload.get("seed"), payload.get("salt"),
            weights.get("train"), weights.get("validation"), weights.get("held_out"),
        )
        policy = cls(*fields)
        cv.refuse_when(
            not _policy_is_sound(policy), cv.FINDING_SPLIT_POLICY_INVALID,
            f"split_policy must name {SPLIT_ALGORITHM}, an integer seed, a string salt and "
            "non-negative integer weights with a positive total",
        )
        return policy


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _weights_are_sound(policy: SplitPolicy) -> bool:
    weights = (policy.train, policy.validation, policy.held_out)
    return all(_is_int(w) and w >= 0 for w in weights) and sum(weights) > 0


def _policy_is_sound(policy: SplitPolicy) -> bool:
    if policy.algorithm != SPLIT_ALGORITHM or not isinstance(policy.salt, str):
        return False
    return _is_int(policy.seed) and _weights_are_sound(policy)


def anchor_for(group_id: str | None, lineage_id: str) -> str:
    """The consumer's component anchor: the group when there is one, else the lineage."""

    return f"group:{group_id}" if group_id else f"lineage:{lineage_id}"


def bucket_split(anchor: str, policy: SplitPolicy) -> str:
    """Agoge's ``sha256-atomic-bucket-v1``, verbatim, so both sides derive the same split."""

    material = f"{policy.algorithm}\0{policy.seed}\0{policy.salt}\0{anchor}".encode("utf-8")
    bucket = int(hashlib.sha256(material).hexdigest(), 16) % policy.total
    if bucket < policy.train:
        return "train"
    if bucket < policy.train + policy.validation:
        return "validation"
    return "held_out"


# --- canonical structure ---------------------------------------------------------


class _Namer:
    """Identifiers renamed by order of first appearance, so renamed copies collapse."""

    def __init__(self) -> None:
        self._names: dict[str, str] = {}

    def __call__(self, name: str) -> str:
        return self._names.setdefault(name, f"v{len(self._names)}")


def _strip_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    if not body or not isinstance(body[0], ast.Expr):
        return body
    value = body[0].value
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return body[1:]
    return body


_RENAMED_FIELDS = ("id", "arg", "name", "asname")


def _field_value(node: ast.AST, name: str, namer: _Namer) -> Any:
    """One field of a node: docstrings stripped from bodies, identifiers renamed."""

    value = getattr(node, name, None)
    if isinstance(node, ast.alias) and name == "asname" and value is None:
        # A plain import binds its API name just like an explicit alias. A dotted
        # import without an alias instead binds the root package, so keep that
        # distinct from an alias that binds the imported submodule itself.
        if "." not in node.name and node.name != "*":
            return namer(node.name)
    if name == "body" and isinstance(value, list):
        return _strip_docstring(value)
    if _is_identifier(node, name, value):
        return namer(value)
    return value


def _is_identifier(node: ast.AST, name: str, value: Any) -> bool:
    """A renamable identifier; a keyword argument's name is the callee's API, not one
    (CodeAnt on #202): ``f(x=1)`` and ``f(y=1)`` are different structures."""

    if name not in _RENAMED_FIELDS or not isinstance(value, str):
        return False
    return not isinstance(node, ast.keyword) and not (isinstance(node, ast.alias) and name == "name")


def _serialise_node(node: ast.AST, namer: _Namer) -> list:
    kept = [name for name in node._fields if name not in _DROPPED_FIELDS]
    fields = [[name, _serialise(_field_value(node, name, namer), namer)] for name in kept]
    return [type(node).__name__, fields]


def _serialise(node: Any, namer: _Namer) -> Any:
    if isinstance(node, ast.AST):
        return _serialise_node(node, namer)
    if isinstance(node, list):
        return [_serialise(item, namer) for item in node]
    return [type(node).__name__, repr(node)]


def canonical_ast(text: str) -> str:
    """A canonical, interpreter-independent serialisation of the module's structure."""

    return oc.canonical_json(_serialise(ast.parse(text), _Namer()))


def structure_digest(text: str) -> str:
    return hashlib.sha256(canonical_ast(text).encode("utf-8")).hexdigest()


# --- groups ------------------------------------------------------------------------


@dataclass(frozen=True)
class Member:
    """What the union-find needs about one program."""

    program_id: str
    upstream_path: str
    structure: str
    links: tuple[str, ...] = ()


def _union(parent: dict[str, str], left: str, right: str) -> None:
    root_left, root_right = _find(parent, left), _find(parent, right)
    if root_left != root_right:
        parent[max(root_left, root_right)] = min(root_left, root_right)


def _find(parent: dict[str, str], item: str) -> str:
    while parent[item] != item:
        parent[item] = parent[parent[item]]
        item = parent[item]
    return item


def _join_shared_keys(parent: dict[str, str], members: tuple[Member, ...]) -> None:
    """Programs from one upstream file or with one structure digest join one component."""

    by_key: dict[tuple[str, str], str] = {}
    for member in members:
        for key in (("file", member.upstream_path), ("structure", member.structure)):
            _union(parent, by_key.setdefault(key, member.program_id), member.program_id)


def _join_links(parent: dict[str, str], members: tuple[Member, ...]) -> None:
    """A program and the catalog program it names as its reference join one component."""

    for member in members:
        for link in (link for link in member.links if link in parent):
            _union(parent, member.program_id, link)


def _group_digest(program_ids: list[str]) -> str:
    return "g-" + hashlib.sha256("\n".join(sorted(program_ids)).encode("utf-8")).hexdigest()[:32]


def group_ids(members: tuple[Member, ...]) -> dict[str, str]:
    """``program_id -> group_id`` over same file, same structure and reference links."""

    parent = {m.program_id: m.program_id for m in members}
    _join_shared_keys(parent, members)
    _join_links(parent, members)
    roots: dict[str, list[str]] = {}
    for member in members:
        roots.setdefault(_find(parent, member.program_id), []).append(member.program_id)
    digests = {root: _group_digest(ids) for root, ids in roots.items()}
    return {m.program_id: digests[_find(parent, m.program_id)] for m in members}


bind_import_twin(__name__)
