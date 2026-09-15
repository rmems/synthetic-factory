"""OpenRouter distillable-catalog discovery. Membership is the authority.

The seed pilot list is not an allow-list. A model is distillable for a batch
only when it appears in the generation-time ``?distillable=true`` snapshot.
Aliases, ``:free``/``:batch`` suffixes, and provider fallbacks fail closed.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from ._contract import bind_import_twin, load_strict_json

DISTILLABLE_URL = "https://openrouter.ai/api/v1/models?distillable=true"
_ALIAS_MARKERS = ("~", ":free", ":batch")


class OpenRouterError(ValueError):
    """Distillable discovery or generation-time evidence failed closed."""


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_alias_id(model_id: str) -> bool:
    if model_id.startswith("~") or "~" in model_id:
        return True
    return any(marker in model_id for marker in (":free", ":batch"))


def load_snapshot(path: Path) -> Mapping[str, Any]:
    """Load a generation-time distillable catalog snapshot from disk."""
    try:
        raw = path.read_bytes()
        payload = load_strict_json(raw.decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise OpenRouterError(f"distillable snapshot unreadable or invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise OpenRouterError("distillable snapshot must be a JSON object")
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise OpenRouterError("distillable snapshot data must be a non-empty list")
    frozen = {
        "retrieved_at": payload.get("retrieved_at"),
        "source_url": payload.get("source_url", DISTILLABLE_URL),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "data": _freeze(data),
    }
    return MappingProxyType(frozen)


def catalog_entry(snapshot: Mapping[str, Any], model_id: str) -> Mapping[str, Any]:
    """Return the exact catalog object for ``model_id`` or fail closed."""
    if not isinstance(model_id, str) or not model_id.strip() or model_id != model_id.strip():
        raise OpenRouterError("OpenRouter model id must be an exact non-empty tag")
    if _is_alias_id(model_id):
        raise OpenRouterError(
            f"refusing OpenRouter alias or variant identity: {model_id!r}"
        )
    matches = []
    for item in snapshot["data"]:
        if not isinstance(item, Mapping):
            continue
        if item.get("id") != model_id:
            continue
        if item.get("distillable") is False:
            raise OpenRouterError(
                f"{model_id!r} is present but distillable is not true"
            )
        matches.append(item)
    if not matches:
        raise OpenRouterError(
            f"{model_id!r} is absent from the distillable catalog snapshot"
        )
    if len(matches) != 1:
        raise OpenRouterError(f"{model_id!r} is duplicated in the distillable snapshot")
    return matches[0]


def refuse_fallback(requested_model: str, response_model: object) -> None:
    """Never accept a different served identity under a distillable request."""
    if response_model != requested_model:
        raise OpenRouterError(
            "OpenRouter response model "
            f"{response_model!r} does not match requested {requested_model!r}; "
            "refusing provider fallback"
        )


def provider_extra() -> dict[str, Any]:
    """Request body fragment that disables non-distillable provider fallback."""
    return {"provider": {"allow_fallbacks": False}}


def evidence(
    *,
    model_id: str,
    snapshot: Mapping[str, Any],
    entry: Mapping[str, Any],
    terms_sha256: str,
    underlying_license_sha256: str,
    generated_at: str | None = None,
) -> dict[str, str]:
    """Generation-time OpenRouter rights/provenance evidence for one batch."""
    retrieved = snapshot.get("retrieved_at")
    if not isinstance(retrieved, str) or not retrieved.strip():
        raise OpenRouterError("distillable snapshot must record retrieved_at")
    canonical = entry.get("canonical_slug")
    if not isinstance(canonical, str) or not canonical:
        canonical = model_id
    return {
        "openrouter_model_id": model_id,
        "canonical_slug": canonical,
        "provider_route": "openrouter_api",
        "is_trainable_text": "distillable_catalog_membership",
        "catalog_retrieved_at": retrieved,
        "catalog_sha256": str(snapshot["sha256"]),
        "openrouter_terms_sha256": terms_sha256,
        "underlying_license_sha256": underlying_license_sha256,
        "generated_at": generated_at or _utc_now(),
        "source_url": str(snapshot.get("source_url") or DISTILLABLE_URL),
    }


bind_import_twin(__name__)
