"""Pinned local vLLM launch contract for open-weight generators.

Bulk generation talks to an OpenAI-compatible endpoint. Tool and reasoning
parsers are optional operator configuration, never a requirement.
"""
from __future__ import annotations

from typing import Any, Mapping

from ._contract import bind_import_twin
from . import source_policy as policy

DEFAULT_BASE_URL = "http://127.0.0.1:8000/v1"
DEFAULT_MAX_MODEL_LEN = 8192
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


class VLLMSpecError(ValueError):
    """A local vLLM launch or provenance claim is incomplete or unsafe."""


def launch_spec(
    path_id: str,
    *,
    runtime_version: str,
    served_model_name: str | None = None,
    max_model_len: int = DEFAULT_MAX_MODEL_LEN,
    device: str,
    container_image: str | None = None,
    container_digest: str | None = None,
    reasoning_parser: str | None = None,
    tool_parser: str | None = None,
) -> dict[str, Any]:
    """Return the reproducible native/Docker vLLM contract for one factory."""
    row = policy.reviewed_row(path_id)
    if row["channel"] != "local_vllm":
        raise VLLMSpecError(f"{path_id} is not a local vLLM factory")
    if max_model_len < 1 or max_model_len > DEFAULT_MAX_MODEL_LEN:
        raise VLLMSpecError(
            f"max_model_len must be in [1, {DEFAULT_MAX_MODEL_LEN}] for workstation use"
        )
    if not runtime_version.strip() or not device.strip():
        raise VLLMSpecError("runtime_version and device identity are required")
    if container_image and not container_digest:
        raise VLLMSpecError("Docker vLLM requires a pinned container digest")
    served = served_model_name or row["runtime_tag"]
    if served != row["runtime_tag"] and served != row["model_id"]:
        raise VLLMSpecError("served_model_name must match the pinned runtime tag or model_id")
    spec = {
        "path_id": path_id,
        "model_id": row["model_id"],
        "model_revision": row["model_revision"],
        "runtime": "vllm",
        "runtime_version": runtime_version,
        "served_model_name": served,
        "max_model_len": max_model_len,
        "device": device,
        "base_url": DEFAULT_BASE_URL,
        "host": DEFAULT_HOST,
        "port": DEFAULT_PORT,
        "require_tool_parser": False,
        "require_reasoning_parser": False,
        "native_command": [
            "vllm",
            "serve",
            row["model_id"],
            "--served-model-name",
            served,
            "--max-model-len",
            str(max_model_len),
            "--host",
            DEFAULT_HOST,
            "--port",
            str(DEFAULT_PORT),
        ],
    }
    if container_image:
        spec["container_image"] = container_image
        spec["container_digest"] = container_digest
    if reasoning_parser:
        spec["reasoning_parser"] = reasoning_parser
    if tool_parser:
        spec["tool_parser"] = tool_parser
    return spec


def require_plain_generation(spec: Mapping[str, Any]) -> None:
    """Ordinary bulk generation must not require tool or reasoning parsers."""
    if spec.get("require_tool_parser") or spec.get("require_reasoning_parser"):
        raise VLLMSpecError(
            "bulk generation must not require tool or reasoning parsers"
        )


bind_import_twin(__name__)
