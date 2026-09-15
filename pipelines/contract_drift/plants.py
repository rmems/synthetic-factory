#!/usr/bin/env python3
"""Plant and pair types for the ACM contract-drift catalog."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from . import _contract

__all__ = ["Pair", "Plant", "plant_from_mapping", "row_from_pair"]


@dataclass(frozen=True)
class Plant:
    """One side of a leftover OpenAPI-drift pair."""

    slug: str
    domain: str
    success: bool
    field: str
    old: str
    new: str
    name: str = ""
    fail_err: str = ""
    vs: str = ""
    fetch1: str = ""
    fetch2: str = ""


@dataclass(frozen=True)
class Pair:
    """Success plant plus the complementary fail/handoff plant."""

    catalog_id: str
    source: str
    kind: str
    success: Plant
    fail: Plant

    @property
    def field(self) -> str:
        return self.success.field


def plant_from_mapping(payload: Mapping[str, Any], *, success: bool | None = None) -> Plant:
    """Build a plant from extracted kwargs or a catalog row half."""

    flag = payload.get("success") if success is None else success
    return Plant(
        slug=str(payload["slug"]),
        domain=str(payload.get("domain") or ""),
        success=bool(flag),
        field=str(payload.get("field") or ""),
        old=str(payload.get("old") or ""),
        new=str(payload.get("new") or ""),
        name=str(payload.get("name") or ""),
        fail_err=str(payload.get("fail_err") or ""),
        vs=str(payload.get("vs") or ""),
        fetch1=str(payload.get("fetch1") or ""),
        fetch2=str(payload.get("fetch2") or ""),
    )


def row_from_pair(pair: Pair) -> dict[str, Any]:
    """One catalog row: identity plus the two slugs and the success surface."""

    return {
        "catalog_id": pair.catalog_id,
        "source": pair.source,
        "kind": pair.kind,
        "success_slug": pair.success.slug,
        "fail_slug": pair.fail.slug,
        "field": pair.success.field,
        "old": pair.success.old,
        "new": pair.success.new,
        "domain": pair.success.domain,
        "fail_err": pair.success.fail_err,
        "vs": pair.success.vs,
        "fetch1": pair.success.fetch1,
        "fetch2": pair.success.fetch2,
    }


_contract.bind_import_twin(__name__)
