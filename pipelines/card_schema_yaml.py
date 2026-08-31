#!/usr/bin/env python3
"""YAML front-matter emission for card declarations.

Takes a *validated* declaration (as returned by ``card_schema_validate.validate``)
and renders the ``configs`` / ``dataset_info`` YAML block (``metadata_yaml``)
that the Hugging Face datasets-server reads from the card. The human-readable
Markdown body lives in ``card_schema_render``.
"""

from __future__ import annotations

import json
import re
from typing import cast

from card_schema_core import DEFAULT_CONFIG_NAME, _require

PLAIN_SCALAR_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
YAML_RESERVED = frozenset(
    {
        "true",
        "false",
        "null",
        "yes",
        "no",
        "on",
        "off",
        "y",
        "n",
        "~",
        "none",
    }
)

__all__ = (
    "_yaml_scalar",
    "metadata_yaml",
    "yaml_features",
)


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    _require(isinstance(value, str), f"cannot emit YAML scalar: {value!r}")
    value = cast(str, value)
    # A card's YAML front matter is delimited by ``---``; a scalar containing it
    # would truncate the block and silently drop metadata.
    _require("---" not in value, f"YAML scalar may not contain '---': {value!r}")
    _require("\n" not in value, f"YAML scalar may not contain a newline: {value!r}")
    if PLAIN_SCALAR_RE.fullmatch(value) and value.lower() not in YAML_RESERVED:
        return value
    return json.dumps(value)


def _yaml_block(value: object, indent: int) -> list[str]:
    """Render a mapping or list as block-style YAML lines."""
    if isinstance(value, dict):
        return _yaml_block_mapping(value, indent)
    _require(isinstance(value, list), f"cannot emit YAML for {value!r}")
    value = cast(list, value)
    return _yaml_block_sequence(value, indent)


def _yaml_block_mapping(value: dict, indent: int) -> list[str]:
    pad = " " * indent
    lines: list[str] = []
    for key, item in value.items():
        key_text = _yaml_scalar(key)
        if isinstance(item, (dict, list)):
            _require(bool(item), f"cannot emit an empty YAML container for {key!r}")
            lines.append(f"{pad}{key_text}:")
            # Block sequences sit at the parent key's indentation; nested
            # mappings are indented one level.
            lines.extend(_yaml_block(item, indent if isinstance(item, list) else indent + 2))
        else:
            lines.append(f"{pad}{key_text}: {_yaml_scalar(item)}")
    return lines


def _yaml_block_sequence(value: list, indent: int) -> list[str]:
    pad = " " * indent
    lines: list[str] = []
    for item in value:
        if isinstance(item, dict):
            nested = _yaml_block(item, indent + 2)
            lines.append(f"{pad}- {nested[0][indent + 2:]}")
            lines.extend(nested[1:])
        else:
            _require(
                not isinstance(item, list), "nested bare YAML sequences are not supported"
            )
            lines.append(f"{pad}- {_yaml_scalar(item)}")
    return lines


def yaml_features(features: list[dict]) -> list[dict]:
    """Strip card-only annotations so the YAML matches the HF feature encoding.

    ``datasets`` reads the feature type from the first key left after ``name``
    is popped, so ``optional`` / ``note`` must never reach the YAML.
    """
    return [_yaml_feature_node(feature) for feature in features]


def _yaml_feature_node(feature: dict) -> dict:
    node: dict = {"name": feature["name"]}
    if "dtype" in feature:
        node["dtype"] = feature["dtype"]
    elif "struct" in feature:
        node["struct"] = yaml_features(feature["struct"])
    else:
        child = feature["list"]
        node["list"] = child if isinstance(child, str) else yaml_features(child)
    return node


def metadata_yaml(declaration: dict) -> str:
    """Return the ``configs`` / ``dataset_info`` YAML block, or '' when omitted."""
    if not declaration["features"]:
        return ""
    patterns = declaration["data_files"]
    path: object = patterns[0] if len(patterns) == 1 else list(patterns)
    configs = [
        {
            "config_name": declaration["config_name"],
            "data_files": [{"split": declaration["split"], "path": path}],
        }
    ]
    lines = ["configs:"]
    lines.extend(_yaml_block(configs, 0))
    lines.append("dataset_info:")
    features = yaml_features(declaration["features"])
    if declaration["config_name"] == DEFAULT_CONFIG_NAME:
        # Bare mapping: datasets-server associates this with the default config.
        lines.extend(_yaml_block({"features": features}, 2))
    else:
        # Named configs must be a sequence of {config_name, features} entries.
        lines.extend(
            _yaml_block(
                [{"config_name": declaration["config_name"], "features": features}],
                0,
            )
        )
    return "\n".join(lines) + "\n"
