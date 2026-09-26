"""Pinned local vLLM launch contract for open-weight generators.

Bulk generation talks to an OpenAI-compatible endpoint. Tool and reasoning
parsers are optional operator configuration, never a requirement.
"""
from __future__ import annotations

from typing import Any, Mapping
from dataclasses import dataclass

from ._contract import bind_import_twin
from . import source_policy as policy

DEFAULT_BASE_URL = "http://127.0.0.1:8000/v1"
DEFAULT_MAX_MODEL_LEN = 8192
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


class VLLMSpecError(ValueError):
    """A local vLLM launch or provenance claim is incomplete or unsafe."""


@dataclass(frozen=True, kw_only=True)
class LaunchOptions:
    runtime_version: str
    device: str
    served_model_name: str | None = None
    max_model_len: int = DEFAULT_MAX_MODEL_LEN
    container_image: str | None = None
    container_digest: str | None = None
    reasoning_parser: str | None = None
    tool_parser: str | None = None


def _check_options(options: LaunchOptions) -> None:
    if not 1 <= options.max_model_len <= DEFAULT_MAX_MODEL_LEN:
        raise VLLMSpecError(f"max_model_len must be in [1, {DEFAULT_MAX_MODEL_LEN}] for workstation use")
    if not options.runtime_version.strip() or not options.device.strip():
        raise VLLMSpecError("runtime_version and device identity are required")
    _check_container(options)


def _check_container(options: LaunchOptions) -> None:
    if options.container_image and not options.container_digest:
        raise VLLMSpecError("Docker vLLM requires a pinned container digest")


def _served_name(row: Mapping, options: LaunchOptions) -> str:
    served = options.served_model_name or row["runtime_tag"]
    if served not in (row["runtime_tag"], row["model_id"]):
        raise VLLMSpecError("served_model_name must match the pinned runtime tag or model_id")
    return served


def _optional_settings(spec: dict, options: LaunchOptions) -> None:
    if options.container_image:
        spec.update(container_image=options.container_image, container_digest=options.container_digest)
    for key in ("reasoning_parser", "tool_parser"):
        value = getattr(options, key)
        if value:
            spec[key] = value


def launch_spec(path_id: str, **kwargs) -> dict[str, Any]:
    """Return a native/Docker contract; keyword options follow LaunchOptions."""
    options = LaunchOptions(**kwargs)
    row = policy.reviewed_row(path_id)
    if row["channel"] != "local_vllm":
        raise VLLMSpecError(f"{path_id} is not a local vLLM factory")
    _check_options(options)
    served = _served_name(row, options)
    spec = {
        "path_id": path_id,
        "model_id": row["model_id"],
        "model_revision": row["model_revision"],
        "runtime": "vllm",
        "runtime_version": options.runtime_version,
        "served_model_name": served,
        "max_model_len": options.max_model_len,
        "device": options.device,
        "base_url": DEFAULT_BASE_URL,
        "host": DEFAULT_HOST,
        "port": DEFAULT_PORT,
        "require_tool_parser": False,
        "require_reasoning_parser": False,
        "native_command": [
            "vllm",
            "serve",
            row["model_id"],
            "--revision",
            row["model_revision"],
            "--tokenizer-revision",
            row["model_revision"],
            "--served-model-name",
            served,
            "--max-model-len",
            str(options.max_model_len),
            "--host",
            DEFAULT_HOST,
            "--port",
            str(DEFAULT_PORT),
        ],
    }
    _optional_settings(spec, options)
    return spec


def require_plain_generation(spec: Mapping[str, Any]) -> None:
    """Ordinary bulk generation must not require tool or reasoning parsers."""
    if spec.get("require_tool_parser") or spec.get("require_reasoning_parser"):
        raise VLLMSpecError(
            "bulk generation must not require tool or reasoning parsers"
        )


bind_import_twin(__name__)
