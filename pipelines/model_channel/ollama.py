"""Pinned local Ollama launch and served-identity contract.

Ollama is the first admitted local generator runtime. A loopback base URL is
necessary but never sufficient: admission requires the served model name to
match the pinned tag and the Ollama manifest digest to match the sealed row.
Cloud tags (``*-cloud``) and non-loopback endpoints fail closed.
"""
from __future__ import annotations

import http.client
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from ._contract import bind_import_twin, load_strict_json
from . import source_policy as policy

DEFAULT_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 11434
DEFAULT_TIMEOUT_S = 60
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_CLOUD_TAG_SUFFIX = "-cloud"
_REQUIRED_RUNTIME_FIELDS = ("ollama_version", "device", "ollama_model_digest")


class OllamaSpecError(ValueError):
    """A local Ollama launch or provenance claim is incomplete or unsafe."""


def _check_scheme(parsed, base_url: str) -> None:
    if parsed.scheme != "http":
        raise OllamaSpecError(
            f"local_ollama endpoint must be plain http loopback: {base_url!r}"
        )


def _check_host(parsed) -> str:
    host = parsed.hostname or ""
    if host.lower() not in _LOOPBACK_HOSTS:
        raise OllamaSpecError(f"local_ollama endpoint must be loopback, got {host!r}")
    return host


def _check_path(parsed) -> str:
    path = parsed.path.rstrip("/") or ""
    if path and path != "/v1":
        raise OllamaSpecError(f"unexpected Ollama base path: {path!r}")
    return path


def _loopback_parts(base_url: str) -> tuple[str, int]:
    parsed = urlparse(base_url)
    _check_scheme(parsed, base_url)
    host = _check_host(parsed)
    _check_path(parsed)
    return host, parsed.port or 80


def _exact_tag(row: Mapping[str, Any]) -> str:
    tag = row["runtime_tag"]
    text = tag.strip() if isinstance(tag, str) else ""
    if not text or text != tag:
        raise OllamaSpecError("ollama runtime_tag must be an exact non-empty tag")
    return tag


def _local_tag(row: Mapping[str, Any]) -> str:
    tag = _exact_tag(row)
    if tag.endswith(_CLOUD_TAG_SUFFIX):
        raise OllamaSpecError(f"refusing cloud-backed Ollama tag: {tag!r}")
    return tag


def _manifest_digest(row: Mapping[str, Any]) -> str:
    revision = row["model_revision"]
    if not isinstance(revision, str) or not revision.startswith("sha256:"):
        raise OllamaSpecError(
            "ollama row must pin model_revision to the manifest digest (sha256:...)"
        )
    return revision


def _require_ollama_row(row: Mapping[str, Any], path_id: str) -> None:
    if row["channel"] != "local_ollama":
        raise OllamaSpecError(f"{path_id} is not a local ollama factory")
    _local_tag(row)
    _manifest_digest(row)


@dataclass(frozen=True, kw_only=True)
class LaunchOptions:
    ollama_version: str
    device: str
    num_ctx: int | None = None


def _check_identity(options: LaunchOptions) -> None:
    if not options.ollama_version.strip() or not options.device.strip():
        raise OllamaSpecError("ollama_version and device identity are required")


def _check_ctx(options: LaunchOptions) -> None:
    if options.num_ctx is not None and options.num_ctx <= 0:
        raise OllamaSpecError("num_ctx must be positive")


def launch_spec(path_id: str, **kwargs) -> dict[str, Any]:
    """Return the verified local launch contract; keyword options follow LaunchOptions."""
    options = LaunchOptions(**kwargs)
    row = policy.reviewed_row(path_id)
    _require_ollama_row(row, path_id)
    _check_identity(options)
    _check_ctx(options)
    spec = {
        "path_id": path_id,
        "model_id": row["model_id"],
        "model_revision": row["model_revision"],
        "runtime": "ollama",
        "ollama_version": options.ollama_version,
        "model_tag": row["runtime_tag"],
        "device": options.device,
        "base_url": DEFAULT_BASE_URL,
        "host": DEFAULT_HOST,
        "port": DEFAULT_PORT,
        "require_tool_parser": False,
        "require_reasoning_parser": False,
        "pull_command": ["ollama", "pull", row["runtime_tag"]],
        "serve_command": ["ollama", "serve"],
    }
    if options.num_ctx is not None:
        spec["num_ctx"] = options.num_ctx
    return spec


def _read_response(conn, path: str) -> bytes:
    try:
        conn.request("GET", path, headers={"Accept": "application/json"})
        response = conn.getresponse()
        raw = response.read()
        if not 200 <= response.status < 300:
            raise OllamaSpecError(f"Ollama HTTP {response.status}: {raw[:200]!r}")
        return raw
    finally:
        conn.close()


def _decode(raw: bytes) -> dict[str, Any]:
    try:
        decoded = load_strict_json(raw.decode("utf-8"))
    except ValueError as exc:
        raise OllamaSpecError(f"Ollama response is not JSON: {exc}") from exc
    if not isinstance(decoded, dict):
        raise OllamaSpecError("Ollama response must be a JSON object")
    return decoded


def _get_json(hostname: str, port: int, path: str) -> dict[str, Any]:
    conn = http.client.HTTPConnection(hostname, port, timeout=DEFAULT_TIMEOUT_S)
    return _decode(_read_response(conn, path))


def _normalize_digest(value: object) -> str:
    digest = value if isinstance(value, str) else ""
    return digest if digest.startswith("sha256:") else f"sha256:{digest}"


def _is_served_match(item: object, expected_tag: str) -> bool:
    if not isinstance(item, Mapping):
        return False
    name = item.get("name")
    return name == expected_tag and not str(name).endswith(_CLOUD_TAG_SUFFIX)


def _models_list(listing: Mapping[str, Any]) -> list:
    models = listing.get("models")
    if not isinstance(models, list):
        raise OllamaSpecError("Ollama /api/tags response must contain a models list")
    return models


def _served_entry(listing: Mapping[str, Any], expected_tag: str) -> Mapping:
    matches = [
        item for item in _models_list(listing)
        if _is_served_match(item, expected_tag)
    ]
    if not matches:
        raise OllamaSpecError(
            f"{expected_tag!r} is not served by the local Ollama instance"
        )
    if len(matches) != 1:
        raise OllamaSpecError(f"{expected_tag!r} is duplicated in /api/tags")
    return matches[0]


def _check_served_digest(served: Mapping, revision: str) -> None:
    if _normalize_digest(served.get("digest")) != revision:
        raise OllamaSpecError(
            f"served digest {served.get('digest')!r} does not match the "
            f"pinned manifest digest {revision!r}"
        )


def verify_served_identity(base_url: str, row: Mapping[str, Any]) -> dict[str, Any]:
    """Proof the loopback server actually serves the pinned local artifact.

    Queries the native ``/api/tags`` listing, requires exactly one entry whose
    name matches the sealed tag, and compares the manifest digest. Refusing
    ``-cloud`` tags here keeps a cloud-backed Ollama route from borrowing the
    local lane's identity.
    """
    _require_ollama_row(row, row["path_id"])
    hostname, port = _loopback_parts(base_url)
    expected_tag = row["runtime_tag"]
    revision = row["model_revision"]
    served = _served_entry(_get_json(hostname, port, "/api/tags"), expected_tag)
    _check_served_digest(served, revision)
    return {
        "ollama_model_tag": expected_tag,
        "ollama_model_digest": revision,
        "served_name": served.get("model") or served.get("name"),
    }


def _require_runtime_fields(runtime: Mapping[str, Any]) -> None:
    missing = [key for key in _REQUIRED_RUNTIME_FIELDS if not runtime.get(key)]
    if missing:
        raise OllamaSpecError(f"runtime provenance missing: {missing}")


def _require_runtime_kind(runtime: Mapping[str, Any]) -> None:
    if runtime.get("runtime") not in (None, "ollama"):
        raise OllamaSpecError("runtime provenance must declare runtime 'ollama'")


def _require_runtime_digest(row: Mapping[str, Any], runtime: Mapping[str, Any]) -> None:
    if _normalize_digest(runtime["ollama_model_digest"]) != row["model_revision"]:
        raise OllamaSpecError(
            "runtime ollama_model_digest does not match the pinned manifest digest"
        )


def require_runtime_provenance(row: Mapping[str, Any], runtime: Mapping[str, Any] | None) -> None:
    """Generation-time runtime claims must carry the pinned Ollama identity."""
    if not isinstance(runtime, Mapping):
        raise OllamaSpecError(
            "local_ollama generation requires a --runtime-json provenance object"
        )
    _require_runtime_fields(runtime)
    _require_runtime_kind(runtime)
    _require_runtime_digest(row, runtime)


bind_import_twin(__name__)
