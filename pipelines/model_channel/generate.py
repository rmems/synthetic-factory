"""Bounded OpenAI-compatible generation of candidate episode records.

The model emits candidates only. This module never self-certifies oracle or
execution truth, never writes ``training_ready``, and strips reasoning traces
and hidden-thought keys before a record is accepted.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ._contract import bind_import_twin, dumps_exact_json, is_under_raw, load_strict_json
from . import openai_client
from . import openrouter
from . import source_policy as policy
from . import vllm as vllm_spec

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
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
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _extract_json_object(content: str) -> dict[str, Any]:
    text = _strip_think(content)
    fenced = FENCE_RE.search(text)
    if fenced is not None:
        text = fenced.group(1).strip()
    try:
        payload = load_strict_json(text)
    except ValueError as exc:
        raise GenerateError(f"model output is not strict JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise GenerateError("model output must be a JSON object")
    return payload


def _assistant_content(response: Mapping[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise GenerateError("completion is missing choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise GenerateError("completion is missing message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise GenerateError("completion content is empty")
    return content


def _require_episode(record: Mapping[str, Any]) -> None:
    for key in ("goal", "steps", "outcome", "reward"):
        if key not in record:
            raise GenerateError(f"candidate episode missing {key!r}")
    steps = record.get("steps")
    if not isinstance(steps, list) or not steps:
        raise GenerateError("candidate episode steps must be a non-empty list")
    reward = record.get("reward")
    if not isinstance(reward, dict) or not isinstance(reward.get("success"), bool):
        raise GenerateError("candidate episode reward.success must be a boolean")


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


def _attach_provenance(
    record: dict[str, Any],
    *,
    row: Mapping[str, Any],
    task: Mapping[str, Any],
    generated_at: str,
    runtime: Mapping[str, Any],
    openrouter_evidence: Mapping[str, str] | None,
) -> dict[str, Any]:
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
        prompt_task_sha256=_task_hash(task),
        generated_at=generated_at,
        candidate_only=True,
    )
    meta.update({f"runtime_{key}": value for key, value in runtime.items()})
    if openrouter_evidence is not None:
        meta.update(openrouter_evidence)
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


def generate_candidate(
    path_id: str,
    task: Mapping[str, Any],
    *,
    endpoint: str,
    api_key: str | None = None,
    runtime: Mapping[str, Any] | None = None,
    openrouter_snapshot: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Call one reviewed generator and return an accepted candidate or raise."""
    row = policy.reviewed_row(path_id)
    stamp = generated_at or _utc_now()
    extra: dict[str, Any] = {}
    openrouter_evidence = None
    if row["channel"] == "openrouter_api":
        if openrouter_snapshot is None:
            raise GenerateError("OpenRouter generation requires a distillable snapshot")
        snapshot = openrouter.load_snapshot(openrouter_snapshot)
        entry = openrouter.catalog_entry(snapshot, row["model_id"])
        extra.update(openrouter.provider_extra())
        terms = row["source_license_evidence"]["openrouter_terms_sha256"]
        license_hash = row["source_license_evidence"]["license_sha256"]
        openrouter_evidence = openrouter.evidence(
            model_id=row["model_id"],
            snapshot=snapshot,
            entry=entry,
            terms_sha256=terms,
            underlying_license_sha256=license_hash,
            generated_at=stamp,
        )
    elif row["channel"] == "local_vllm":
        vllm_spec.require_plain_generation(runtime or {"require_tool_parser": False})
    response = openai_client.chat_completions(
        endpoint,
        row["runtime_tag"] if row["channel"] == "local_vllm" else row["model_id"],
        _messages(task),
        api_key=api_key,
        extra=extra or None,
    )
    if row["channel"] == "openrouter_api":
        openrouter.refuse_fallback(row["model_id"], response.get("model"))
    record = _extract_json_object(_assistant_content(response))
    if _contains_self_certify(record):
        raise GenerateError("candidate attempted to self-certify oracle or training truth")
    record = strip_untrainable(record)
    _require_episode(record)
    attached = _attach_provenance(
        record,
        row=row,
        task=task,
        generated_at=stamp,
        runtime=dict(runtime or {}),
        openrouter_evidence=openrouter_evidence,
    )
    attached["_generation"] = {
        "usage": _usage(response),
        "response_model": response.get("model"),
    }
    return attached


def write_run(
    out_dir: Path,
    *,
    path_id: str,
    records: list[Mapping[str, Any]],
    attempted: int,
    rejected: list[str],
    produced_at: str,
) -> dict[str, Any]:
    """Write accepted candidates to a brand-new destination outside outputs/raw."""
    destination = Path(out_dir)
    if is_under_raw(destination):
        raise GenerateError(f"{destination} names or aliases the raw tree")
    if destination.exists():
        raise GenerateError(f"{destination} already exists")
    destination.mkdir(parents=True)
    accepted = []
    for record in records:
        payload = dict(record)
        payload.pop("_generation", None)
        accepted.append(payload)
    candidates = destination / "candidates.jsonl"
    with candidates.open("w", encoding="utf-8") as handle:
        for record in accepted:
            handle.write(dumps_exact_json(record) + "\n")
    summary = {
        "format": "model-channel-run/1",
        "path_id": path_id,
        "produced_at": produced_at,
        "attempted": attempted,
        "accepted": len(accepted),
        "rejected": len(rejected),
        "rejected_reasons": rejected,
        "candidate_only": True,
        "self_certified_oracle": False,
    }
    (destination / "RUN.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return summary


bind_import_twin(__name__)
