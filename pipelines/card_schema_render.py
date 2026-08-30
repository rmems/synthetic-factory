#!/usr/bin/env python3
"""YAML front matter and Markdown body rendering for card declarations.

Takes a *validated* declaration (as returned by ``card_schema_validate.validate``)
and renders the two pieces a published dataset card needs: the ``configs`` /
``dataset_info`` YAML block (``metadata_yaml``) and the human-readable
"Dataset viewer schema" section (``body_section`` / ``undeclared_body_section``).
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

ISSUE_URL = "https://github.com/rmems/synthetic-factory/issues"

__all__ = (
    "_yaml_scalar",
    "body_section",
    "json_columns",
    "metadata_yaml",
    "undeclared_body_section",
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


def field_notes(features: list[dict], prefix: str = "") -> list[tuple[str, bool, str]]:
    """Return ``(dotted path, optional, note)`` for every annotated field."""
    rows: list[tuple[str, bool, str]] = []
    for feature in features:
        path = f"{prefix}{feature['name']}"
        if feature.get("optional") or feature.get("note"):
            rows.append((path, bool(feature.get("optional")), feature.get("note", "")))
        if "struct" in feature:
            rows.extend(field_notes(feature["struct"], f"{path}."))
        elif isinstance(feature.get("list"), list):
            rows.extend(field_notes(feature["list"], f"{path}[]."))
    return rows


def json_columns(features: list[dict], prefix: str = "") -> list[str]:
    """Return the dotted paths of every column declared as ``json``."""
    columns: list[str] = []
    for feature in features:
        path = f"{prefix}{feature['name']}"
        if feature.get("dtype") == "json" or feature.get("list") == "json":
            columns.append(path)
        if "struct" in feature:
            columns.extend(json_columns(feature["struct"], f"{path}."))
        elif isinstance(feature.get("list"), list):
            columns.extend(json_columns(feature["list"], f"{path}[]."))
    return columns


def _issue_links(issues: list[int]) -> str:
    return ", ".join(f"[#{number}]({ISSUE_URL}/{number})" for number in issues)


def body_section(declaration: dict) -> str:
    """Render the card's viewer-schema section for a declared dataset."""
    lines = ["## Dataset viewer schema", "", _body_note(declaration), ""]
    lines.extend(_body_schema_summary(declaration))
    lines.extend(_body_field_notes(declaration))
    lines.extend(_body_disclosures(declaration))
    return "\n".join(lines)


def _body_note(declaration: dict) -> str:
    note = declaration["note"]
    if declaration["issues"]:
        note = f"{note} Tracked in {_issue_links(declaration['issues'])}."
    return note


def _body_schema_summary(declaration: dict) -> list[str]:
    if not declaration["features"]:
        return [
            "No default `configs` / `dataset_info` block is declared for this "
            "dataset on purpose: the working viewer projection is not replaced by "
            "a raw config.",
            "",
        ]
    patterns = ", ".join(f"`{pattern}`" for pattern in declaration["data_files"])
    lines = [
        f"The `configs` / `dataset_info` metadata above declares config "
        f"`{declaration['config_name']}`, split `{declaration['split']}`, over "
        f"{patterns}. It is written by hand rather than inferred from the first "
        "shard, so the datasets-server can build a parquet index without any "
        "historical raw record being rewritten.",
        "",
    ]
    columns = json_columns(declaration["features"])
    if columns:
        listed = ", ".join(f"`{column}`" for column in columns)
        lines.append(
            f"Key-bag columns are declared as `json` so their keys may differ "
            f"per record without an Arrow cast error: {listed}."
        )
        lines.append("")
    return lines


def _body_field_notes(declaration: dict) -> list[str]:
    rows = field_notes(declaration["features"])
    if not rows:
        return []
    lines = [
        "Field notes. An optional field is absent on some records; every "
        "declared field is nullable, so it reads back as `null` there "
        "instead of breaking the cast.",
        "",
        "| Field | Status | Note |",
        "|---|---|---|",
    ]
    for path, optional, note_text in rows:
        status = "optional" if optional else "present on every record"
        lines.append(f"| `{path}` | {status} | {note_text or '—'} |")
    lines.append("")
    return lines


def _body_disclosures(declaration: dict) -> list[str]:
    if not declaration["disclosures"]:
        return []
    lines = ["### Known payload disclosures", ""]
    for disclosure in declaration["disclosures"]:
        text = disclosure["summary"]
        if disclosure["issues"]:
            text = f"{text} Tracked in {_issue_links(disclosure['issues'])}."
        lines.append(f"- {text}")
        if disclosure["ids"]:
            listed = ", ".join(f"`{record_id}`" for record_id in disclosure["ids"])
            lines.append(f"  Record ids: {listed}.")
    lines.append("")
    return lines


def undeclared_body_section(dataset: str) -> str:
    """Render the visible placeholder for a dataset with no declaration yet."""
    return "\n".join(
        [
            "## Dataset viewer schema",
            "",
            (
                "**Not declared yet.** This card carries no `configs` / `dataset_info` "
                "block, so index availability is unverified here: the datasets-server "
                "may infer a working schema for a homogeneous payload, while a later "
                "heterogeneous shard can still make `viewer`, `search`, `filter`, or "
                "`statistics` fail even where the streaming preview works. The published "
                "raw payload described above is complete and unmodified; only the "
                "card-side schema declaration is missing."
            ),
            "",
            (
                f"Declaring it is tracked per dataset at {ISSUE_URL} (search "
                f"`{dataset}`). The declaration is one JSON file at "
                f"`config/card-schemas/{dataset}.json` in "
                "https://github.com/rmems/synthetic-factory."
            ),
            "",
        ]
    )
