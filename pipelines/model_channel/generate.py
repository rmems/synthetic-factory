"""Bounded OpenAI-compatible generation of candidate episode records.

The model emits candidates only. This module never self-certifies oracle or
execution truth, never writes ``training_ready``, and strips reasoning traces
and hidden-thought keys before a record is accepted.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ._contract import bind_import_twin, dumps_exact_json, is_under_raw, load_strict_json
from . import openai_client
from . import openrouter
from . import source_policy as policy
from . import vllm as vllm_spec

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
FORBIDDEN_KEYS = frozenset({
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "internal_reasoning",
    "internal_reasoning_verbatim",
    "reasoning",
    "reasoning_content",
    "training_ready",
    "oracle_pass",
    "oracle_verified",
    "execution_verified",
    "training_eligible",
})
FORBIDDEN_PREFIXES = ("internal_reasoning", "oracle_")
SELF_CERTIFY_KEYS = frozenset({
    "training_ready",
    "oracle_pass",
    "oracle_verified",
    "execution_verified",
    "training_eligible",
})


class GenerateError(ValueError):
    """A model-channel generation request or candidate failed closed."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _strip_think(text: str) -> str:
    return THINK_RE.sub("", text).strip()


def _is_forbidden_key(key: object) -> bool:
    if not isinstance(key, str):
        return False
    if key in FORBIDDEN_KEYS:
        return True
    return any(key.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)


def strip_untrainable(value: Any) -> Any:
    """Drop reasoning traces and self-certification keys from a candidate."""
    if isinstance(value, dict):
        return {
            key: strip_untrainable(item)
            for key, item in value.items()
            if not _is_forbidden_key(key)
        }
    if isinstance(value, list):
        return [strip_untrainable(item) for item in value]
    if isinstance(value, str):
        return _strip_think(value)
    return value


def _contains_self_certify(value: Any) -> bool:
    if isinstance(value, dict):
        if SELF_CERTIFY_KEYS.intersection(value):
            return True
        return any(_contains_self_certify(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_self_certify(item) for item in value)
    return False


def _unfence(text: str) -> str:
    """Read the first complete fence without regex backtracking on model output."""
    _, opening, tail = text.partition("```")
    body, closing, _ = tail.partition("```")
    if not opening or not closing:
        return text
    if body[:4].lower() == "json":
        body = body[4:]
    return body.strip()


def _extract_json_object(content: str) -> dict[str, Any]:
    text = _unfence(_strip_think(content))
    try:
        payload = load_strict_json(text)
    except ValueError as exc:
        raise GenerateError(f"model output is not strict JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise GenerateError("model output must be a JSON object")
    return payload


def _first_message(response: Mapping[str, Any]) -> dict:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise GenerateError("completion is missing choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise GenerateError("completion is missing message")
    return message


def _assistant_content(response: Mapping[str, Any]) -> str:
    content = _first_message(response).get("content")
    if not isinstance(content, str) or not content.strip():
        raise GenerateError("completion content is empty")
    return content


def _require_episode_shape(record: Mapping[str, Any]) -> None:
    steps = record.get("steps")
    if not isinstance(steps, list) or not steps:
        raise GenerateError("candidate episode steps must be a non-empty list")
    reward = record.get("reward")
    if not isinstance(reward, dict) or not isinstance(reward.get("success"), bool):
        raise GenerateError("candidate episode reward.success must be a boolean")


def _require_episode(record: Mapping[str, Any]) -> None:
    for key in ("goal", "steps", "outcome", "reward"):
        if key not in record:
            raise GenerateError(f"candidate episode missing {key!r}")
    _require_episode_shape(record)


def _task_hash(task: Mapping[str, Any]) -> str:
    encoded = json.dumps(dict(task), sort_keys=True, allow_nan=False, ensure_ascii=False)
    return _sha256_text(encoded)


def _usage(response: Mapping[str, Any]) -> dict[str, Any]:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        return {}
    kept = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = usage.get(key)
        if isinstance(value, int):
            kept[key] = value
    return kept


@dataclass(frozen=True)
class ProvenanceContext:
    task: Mapping[str, Any]
    generated_at: str
    runtime: Mapping[str, Any]
    openrouter_evidence: Mapping[str, str] | None


def _attach_provenance(record: dict[str, Any], row: Mapping[str, Any], context: ProvenanceContext) -> dict[str, Any]:
    meta = dict(record.get("meta") or {})
    meta.update(
        factory=row["path_id"],
        generator=row["generator"],
        generator_version=row["generator_version"],
        provider=row["provider"],
        channel=row["channel"],
        model_id=row["model_id"],
        model_revision=row["model_revision"],
        generation_surface=row["generation_surface"],
        runtime_tag=row["runtime_tag"],
        prompt_task_sha256=_task_hash(context.task),
        generated_at=context.generated_at,
        candidate_only=True,
    )
    meta.update({f"runtime_{key}": value for key, value in context.runtime.items()})
    if context.openrouter_evidence is not None:
        meta.update(context.openrouter_evidence)
    record["meta"] = meta
    return record


def _messages(task: Mapping[str, Any]) -> list[dict[str, str]]:
    goal = task.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        raise GenerateError("task.goal must be a nonempty string")
    schema = task.get("schema")
    schema_text = ""
    if schema is not None:
        schema_text = "\nSchema:\n" + json.dumps(schema, allow_nan=False)
    return [
        {
            "role": "system",
            "content": (
                "Return one JSON episode object only. Include goal, steps with "
                "tool_call, observation, and decision_basis, plus outcome and "
                "reward.success. Do not include thought, reasoning, <think> "
                "traces, oracle verdicts, or training_ready."
            ),
        },
        {"role": "user", "content": f"Task:\n{goal.strip()}{schema_text}"},
    ]


@dataclass(frozen=True, kw_only=True)
class GenerationOptions:
    endpoint: str
    api_key: str | None = None
    runtime: Mapping[str, Any] | None = None
    openrouter_snapshot: Path | None = None
    generated_at: str | None = None


def _openrouter_evidence(row: Mapping, options: GenerationOptions, stamp: str) -> dict:
    if options.openrouter_snapshot is None:
        raise GenerateError("OpenRouter generation requires a distillable snapshot")
    snapshot = openrouter.load_snapshot(options.openrouter_snapshot)
    entry = openrouter.catalog_entry(snapshot, row["model_id"])
    license_evidence = row["source_license_evidence"]
    return openrouter.evidence(
        model_id=row["model_id"], snapshot=snapshot, entry=entry,
        terms_sha256=license_evidence["openrouter_terms_sha256"],
        underlying_license_sha256=license_evidence["license_sha256"], generated_at=stamp,
    )


def _route_evidence(row: Mapping, options: GenerationOptions, stamp: str) -> dict | None:
    if row["channel"] == "openrouter_api":
        return _openrouter_evidence(row, options, stamp)
    if row["channel"] == "local_vllm":
        vllm_spec.require_plain_generation(options.runtime or {"require_tool_parser": False})
    return None


def _completion(row: Mapping, task: Mapping, options: GenerationOptions) -> dict:
    remote = row["channel"] == "openrouter_api"
    response = openai_client.chat_completions(
        options.endpoint,
        row["runtime_tag"] if row["channel"] == "local_vllm" else row["model_id"],
        _messages(task), api_key=options.api_key,
        extra=openrouter.provider_extra() if remote else None,
    )
    if remote:
        openrouter.refuse_fallback(row["model_id"], response.get("model"))
    return response


def _accepted_record(response: Mapping) -> dict:
    record = _extract_json_object(_assistant_content(response))
    if _contains_self_certify(record):
        raise GenerateError("candidate attempted to self-certify oracle or training truth")
    record = strip_untrainable(record)
    _require_episode(record)
    return record


def generate_candidate(path_id: str, task: Mapping[str, Any], **kwargs) -> dict[str, Any]:
    """Call one reviewed generator; keyword options follow GenerationOptions."""
    options = GenerationOptions(**kwargs)
    row = policy.reviewed_row(path_id)
    stamp = options.generated_at or _utc_now()
    evidence = _route_evidence(row, options, stamp)
    response = _completion(row, task, options)
    context = ProvenanceContext(task, stamp, dict(options.runtime or {}), evidence)
    attached = _attach_provenance(_accepted_record(response), row, context)
    attached["_generation"] = {"usage": _usage(response), "response_model": response.get("model")}
    return attached


@dataclass(frozen=True, kw_only=True)
class RunOutput:
    path_id: str
    records: list[Mapping[str, Any]]
    attempted: int
    rejected: list[str]
    produced_at: str


def write_run(out_dir: Path, **kwargs) -> dict[str, Any]:
    """Write accepted candidates to a brand-new destination outside outputs/raw."""
    output = RunOutput(**kwargs)
    destination = Path(out_dir)
    if is_under_raw(destination):
        raise GenerateError(f"{destination} names or aliases the raw tree")
    if destination.exists():
        raise GenerateError(f"{destination} already exists")
    destination.mkdir(parents=True)
    accepted = []
    for record in output.records:
        payload = dict(record)
        payload.pop("_generation", None)
        accepted.append(payload)
    candidates = destination / "candidates.jsonl"
    with candidates.open("w", encoding="utf-8") as handle:
        for record in accepted:
            handle.write(dumps_exact_json(record) + "\n")
    summary = {
        "format": "model-channel-run/1",
        "path_id": output.path_id,
        "produced_at": output.produced_at,
        "attempted": output.attempted,
        "accepted": len(accepted),
        "rejected": len(output.rejected),
        "rejected_reasons": output.rejected,
        "candidate_only": True,
        "self_certified_oracle": False,
    }
    (destination / "RUN.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return summary


bind_import_twin(__name__)
