"""Render the reviewed CSV episode templates without duplicating control flow."""

from typing import Any

from . import steps_templates
from ._contract import (
    CsvRefusal,
    DECISION_BASIS_LIMIT,
    DECISION_BASIS_PREFIXES,
    FINDING_DECISION_BASIS,
    bind_import_twin,
)


def _render(value: str | dict[str, str], context: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: text.format_map(context) for key, text in value.items()}
    return value.format_map(context)


def _step(index: int, template: tuple, context: dict[str, str]) -> dict[str, Any]:
    kind, text, name, args, observation, reflection = template
    if kind not in DECISION_BASIS_PREFIXES:
        raise CsvRefusal(FINDING_DECISION_BASIS, f"bad decision_basis prefix: {kind!r}")
    return {
        "n": index,
        "decision_basis": f"{kind}: {_render(text, context)}"[:DECISION_BASIS_LIMIT],
        "tool_call": {"name": name, "args": _render(args, context)},
        "observation": _render(observation, context),
        "reflection": _render(reflection, context),
    }


def make_steps(pair: dict[str, str], *, success: bool) -> list[dict[str, Any]]:
    module = pair["mod"] if success else pair["drop"]
    context = {
        **pair,
        "src": f"src/{module}.py",
        "cfg": f"{module}/cfg.yml",
        "test": f"tests/test_{module}.py",
    }
    templates = steps_templates.SUCCESS if success else steps_templates.FAILURE
    return [_step(index, template, context) for index, template in enumerate(templates, 1)]


bind_import_twin(__name__)
