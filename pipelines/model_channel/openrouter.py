"""OpenRouter distillable-catalog discovery. Membership is the authority.

The seed pilot list is not an allow-list. A model is distillable for a batch
only when it appears in the generation-time ``?distillable=true`` snapshot.
Aliases, ``:free``/``:batch`` suffixes, and provider fallbacks fail closed.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from ._contract import bind_import_twin, freeze, load_strict_json

DISTILLABLE_URL = "https://openrouter.ai/api/v1/models?distillable=true"
_ALIAS_MARKERS = ("~", ":free", ":batch")


class OpenRouterError(ValueError):
    """Distillable discovery or generation-time evidence failed closed."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_alias_id(model_id: str) -> bool:
    if model_id.startswith("~") or "~" in model_id:
        return True
    return any(marker in model_id for marker in (":free", ":batch"))


def _read_snapshot(path: Path) -> tuple[bytes, dict]:
    try:
        raw = path.read_bytes()
        payload = load_strict_json(raw.decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise OpenRouterError(f"distillable snapshot unreadable or invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise OpenRouterError("distillable snapshot must be a JSON object")
    return raw, payload


def _snapshot_data(payload: Mapping) -> tuple:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise OpenRouterError("distillable snapshot data must be a non-empty list")
    return freeze(data)


def load_snapshot(path: Path) -> Mapping[str, Any]:
    """Load exact bytes of a generation-time distillable catalog snapshot."""
    raw, payload = _read_snapshot(path)
    return MappingProxyType({
        "retrieved_at": payload.get("retrieved_at"),
        "source_url": payload.get("source_url", DISTILLABLE_URL),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "data": _snapshot_data(payload),
    })


def _require_model_id(model_id: str) -> None:
    if not isinstance(model_id, str) or not model_id.strip():
        raise OpenRouterError("OpenRouter model id must be an exact non-empty tag")
    if model_id != model_id.strip():
        raise OpenRouterError("OpenRouter model id must be an exact non-empty tag")
    if _is_alias_id(model_id):
        raise OpenRouterError(f"refusing OpenRouter alias or variant identity: {model_id!r}")


def _matching_entries(snapshot: Mapping, model_id: str) -> list[Mapping]:
    return [item for item in snapshot["data"] if isinstance(item, Mapping) and item.get("id") == model_id]


def catalog_entry(snapshot: Mapping[str, Any], model_id: str) -> Mapping[str, Any]:
    """Return the exact catalog object for model_id or fail closed."""
    _require_model_id(model_id)
    matches = _matching_entries(snapshot, model_id)
    if any(item.get("distillable") is False for item in matches):
        raise OpenRouterError(f"{model_id!r} is present but distillable is not true")
    if not matches:
        raise OpenRouterError(f"{model_id!r} is absent from the distillable catalog snapshot")
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


def _canonical_slug(entry: Mapping, model_id: str) -> str:
    canonical = entry.get("canonical_slug")
    return canonical if isinstance(canonical, str) and canonical else model_id


@dataclass(frozen=True, kw_only=True)
class EvidenceOptions:
    terms_sha256: str
    underlying_license_sha256: str
    generated_at: str | None = None


def evidence(*, model_id: str, snapshot: Mapping[str, Any], entry: Mapping[str, Any], **kwargs) -> dict[str, str]:
    """Generation-time OpenRouter rights/provenance evidence for one batch."""
    options = EvidenceOptions(**kwargs)
    retrieved = snapshot.get("retrieved_at")
    if not isinstance(retrieved, str) or not retrieved.strip():
        raise OpenRouterError("distillable snapshot must record retrieved_at")
    return {
        "openrouter_model_id": model_id,
        "canonical_slug": _canonical_slug(entry, model_id),
        "provider_route": "openrouter_api",
        "is_trainable_text": "distillable_catalog_membership",
        "catalog_retrieved_at": retrieved,
        "catalog_sha256": str(snapshot["sha256"]),
        "openrouter_terms_sha256": options.terms_sha256,
        "underlying_license_sha256": options.underlying_license_sha256,
        "generated_at": options.generated_at or _utc_now(),
        "source_url": str(snapshot.get("source_url") or DISTILLABLE_URL),
    }


bind_import_twin(__name__)
