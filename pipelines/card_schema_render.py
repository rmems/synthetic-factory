#!/usr/bin/env python3
"""Markdown body rendering for card declarations.

Takes a *validated* declaration (as returned by ``card_schema_validate.validate``)
and renders the human-readable "Dataset viewer schema" section
(``body_section`` / ``undeclared_body_section``). The ``configs`` /
``dataset_info`` YAML block lives in ``card_schema_yaml``.
"""

from __future__ import annotations

ISSUE_URL = "https://github.com/rmems/synthetic-factory/issues"

__all__ = (
    "body_section",
    "field_notes",
    "json_columns",
    "undeclared_body_section",
)


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
            "Columns declared as `json` may differ in object keys or value "
            "types from record to record; they load without an Arrow cast "
            f"error: {listed}."
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
