#!/usr/bin/env python3
"""Per-dataset Hugging Face card schema declarations.

Published raw JSONL has heterogeneous ``meta`` / ``reward`` / ``tool_call.args``
shapes plus optional per-dataset extras. The datasets-server infers a schema from
the first shard, then fails to cast a later shard, so it cannot build a parquet
index: ``/is-valid`` reports ``preview`` true but ``viewer`` / ``search`` /
``filter`` / ``statistics`` false. The fix is always card-side -- declare the
union schema on the card. Historical raw JSONL is never rewritten.

One dataset owns exactly one declaration file::

    config/card-schemas/<hub-dataset-name>.json

Keying on the published Hub dataset name (not the factory slug) means a dataset
is added as an independent file with zero merge conflicts against its siblings.

Declaration format (``version: 1``)::

    {
      "version": 1,
      "dataset": "long-horizon-coding-trajectories",   # must equal the filename stem
      "issues": [36],                                  # tracking issues, optional
      "note": "One sentence saying why the schema is declared by hand.",
      "config_name": "default",                        # optional, default "default"
      "split": "train",                                # optional, default "train"
      "data_files": ["data/raw/batch-*.jsonl"],        # optional, default that glob
      "features": [ <feature>, ... ],                  # omit for a disclosure-only card
      "disclosures": [ <disclosure>, ... ]             # optional
    }

A ``<feature>`` mirrors the Hugging Face YAML feature encoding one-to-one, plus
two card-only annotations that are stripped before the YAML is emitted::

    {"name": "goal", "dtype": "string"}
    {"name": "plan", "dtype": "json", "optional": true, "note": "4262 of 9970"}
    {"name": "tags", "list": "string"}
    {"name": "tool_call", "struct": [ <feature>, ... ]}
    {"name": "steps", "list": [ <feature>, ... ]}

``dtype: json`` maps to the ``datasets`` ``Json()`` feature, which is what a
key-bag column (``meta``, ``reward``, ``tool_call.args``) needs: keys may differ
per record without an Arrow cast error. Every declared field is nullable --
``datasets`` sets all struct fields nullable -- so declaring an optional field
makes it read back as ``null`` where the raw record omits it. ``optional`` is
therefore documentation: it drives the card's field table, not the Arrow schema.

A ``<disclosure>`` is either a plain sentence, or::

    {"summary": "...", "ids": ["..."], "issues": [43, 44]}

Disclosures carry the known leftover-mill / dest-stamped rows that a dataset must
own on its card.

Omitting ``features`` produces a disclosure-only declaration: no ``configs`` and
no ``dataset_info`` are emitted. That is the right shape for a dataset whose
working viewer projection must not be replaced by a default raw config.
"""

from __future__ import annotations

import json
import re
from fnmatch import fnmatchcase
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = REPO_ROOT / "config" / "card-schemas"

DEFAULT_CONFIG_NAME = "default"
DEFAULT_SPLIT = "train"
DEFAULT_DATA_FILES = ("data/raw/batch-*.jsonl",)

# Value dtypes this repository declares. ``json`` is the ``datasets`` Json()
# feature and is the only correct choice for a key-bag column.
SCALAR_DTYPES = frozenset(
    {"string", "bool", "int32", "int64", "float32", "float64", "json"}
)

DATASET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FIELD_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
DATA_FILE_RE = re.compile(r"^data/[A-Za-z0-9_*?./-]+$")
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

TOP_LEVEL_KEYS = frozenset(
    {
        "version",
        "dataset",
        "issues",
        "note",
        "config_name",
        "split",
        "data_files",
        "features",
        "disclosures",
    }
)
FEATURE_KEYS = frozenset({"name", "dtype", "struct", "list", "optional", "note"})
DISCLOSURE_KEYS = frozenset({"summary", "ids", "issues"})

ISSUE_URL = "https://github.com/rmems/synthetic-factory/issues"


class CardSchemaError(Exception):
    """A declaration file is missing, unreadable, or does not validate."""


def schema_root() -> Path:
    """Directory holding one declaration file per dataset, resolved at call time."""
    return SCHEMA_ROOT


def _require(condition: object, message: str) -> None:
    if not condition:
        raise CardSchemaError(message)


def declaration_path(dataset: str, root: Path | None = None) -> Path:
    """Return the declaration path for one Hub dataset name."""
    _require(
        isinstance(dataset, str) and DATASET_NAME_RE.fullmatch(dataset) is not None,
        f"invalid Hub dataset name: {dataset!r}",
    )
    return (root if root is not None else schema_root()) / f"{dataset}.json"


def _declaration_root(root: Path | None = None) -> Path:
    """Return a safe declaration root, whether or not it exists yet."""
    directory = root if root is not None else schema_root()
    _require(
        not directory.is_symlink(),
        f"unsafe card schema root: {directory}",
    )
    if directory.exists():
        _require(
            directory.is_dir(),
            f"unsafe card schema root: {directory}",
        )
    return directory


def declared_datasets(root: Path | None = None) -> list[str]:
    """Return every dataset name that owns a declaration file."""
    directory = _declaration_root(root)
    if not directory.exists():
        return []
    names = []
    for path in sorted(directory.iterdir()):
        if path.name.startswith("."):
            continue
        _require(
            path.is_file() and not path.is_symlink(),
            f"unsafe card schema entry: {path}",
        )
        _require(
            path.suffix == ".json",
            f"unexpected card schema entry (expected <dataset>.json): {path}",
        )
        _require(
            DATASET_NAME_RE.fullmatch(path.stem) is not None,
            f"invalid card schema filename: {path}",
        )
        names.append(path.stem)
    return names


def load(dataset: str, root: Path | None = None) -> dict | None:
    """Return a validated declaration for ``dataset``, or ``None`` if undeclared.

    A file that exists but does not validate raises ``CardSchemaError``. A
    declaration is never silently ignored.
    """
    directory = _declaration_root(root)
    if not directory.exists():
        return None
    path = declaration_path(dataset, directory)
    if not path.exists() and not path.is_symlink():
        return None
    _require(
        path.is_file() and not path.is_symlink(),
        f"unsafe card schema entry: {path}",
    )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CardSchemaError(f"cannot read card schema {path}: {exc}") from exc
    try:
        return validate(payload, dataset)
    except CardSchemaError as exc:
        raise CardSchemaError(f"invalid card schema {path}: {exc}") from exc


def validate(payload: object, dataset: str) -> dict:
    """Validate one declaration payload and return it normalized."""
    _require(isinstance(payload, dict), "declaration must be a JSON object")
    assert isinstance(payload, dict)  # narrowed by _require
    unknown = sorted(set(payload) - TOP_LEVEL_KEYS)
    _require(not unknown, f"unknown declaration key(s): {', '.join(unknown)}")
    _require(payload.get("version") == 1, "declaration version must be 1")
    _require(
        payload.get("dataset") == dataset,
        f"declaration dataset {payload.get('dataset')!r} does not match {dataset!r}",
    )
    note = payload.get("note")
    _require(
        isinstance(note, str) and note.strip() != "",
        "declaration needs a non-empty 'note' explaining the hand-declared schema",
    )
    assert isinstance(note, str)

    config_name = payload.get("config_name", DEFAULT_CONFIG_NAME)
    _require(
        isinstance(config_name, str) and DATASET_NAME_RE.fullmatch(config_name),
        f"invalid config_name: {config_name!r}",
    )
    split = payload.get("split", DEFAULT_SPLIT)
    _require(
        isinstance(split, str) and DATASET_NAME_RE.fullmatch(split),
        f"invalid split: {split!r}",
    )

    raw_data_files = payload.get("data_files", list(DEFAULT_DATA_FILES))
    if isinstance(raw_data_files, str):
        raw_data_files = [raw_data_files]
    _require(
        isinstance(raw_data_files, list) and raw_data_files,
        "data_files must be a non-empty string or list of strings",
    )
    data_files: list[str] = []
    for pattern in raw_data_files:
        _require(
            isinstance(pattern, str) and DATA_FILE_RE.fullmatch(pattern) is not None,
            f"data_files pattern must be a repo-relative data/ path: {pattern!r}",
        )
        assert isinstance(pattern, str)
        _require(".." not in pattern, f"data_files pattern escapes the repo: {pattern!r}")
        _require(
            all("**" not in segment or segment == "**" for segment in pattern.split("/")),
            f"recursive wildcard '**' must occupy an entire path segment: {pattern!r}",
        )
        _require(pattern not in data_files, f"duplicate data_files pattern: {pattern!r}")
        data_files.append(pattern)

    raw_features = payload.get("features", [])
    _require(isinstance(raw_features, list), "features must be a list")
    assert isinstance(raw_features, list)
    features = [_validate_feature(node, ()) for node in raw_features]
    _reject_duplicate_names(features, ())

    raw_disclosures = payload.get("disclosures", [])
    _require(isinstance(raw_disclosures, list), "disclosures must be a list")
    assert isinstance(raw_disclosures, list)
    disclosures = [_validate_disclosure(item) for item in raw_disclosures]

    issues = _validate_issues(payload.get("issues", []), "issues")

    return {
        "version": 1,
        "dataset": dataset,
        "issues": issues,
        "note": note.strip(),
        "config_name": config_name,
        "split": split,
        "data_files": data_files,
        "features": features,
        "disclosures": disclosures,
    }


def _validate_issues(value: object, label: str) -> list[int]:
    _require(isinstance(value, list), f"{label} must be a list of issue numbers")
    assert isinstance(value, list)
    issues = []
    for number in value:
        _require(
            isinstance(number, int) and not isinstance(number, bool) and number > 0,
            f"{label} entries must be positive integers: {number!r}",
        )
        assert isinstance(number, int)
        issues.append(number)
    return issues


def _validate_feature(node: object, path: tuple[str, ...]) -> dict:
    where = ".".join(path) or "<top level>"
    _require(isinstance(node, dict), f"feature under {where} must be an object")
    assert isinstance(node, dict)
    unknown = sorted(set(node) - FEATURE_KEYS)
    _require(not unknown, f"unknown feature key(s) under {where}: {', '.join(unknown)}")
    name = node.get("name")
    _require(
        isinstance(name, str) and FIELD_NAME_RE.fullmatch(name) is not None,
        f"invalid feature name under {where}: {name!r}",
    )
    assert isinstance(name, str)
    here = (*path, name)

    kinds = [key for key in ("dtype", "struct", "list") if key in node]
    _require(
        len(kinds) == 1,
        f"feature {'.'.join(here)} needs exactly one of dtype/struct/list, got "
        f"{kinds or ['none']}",
    )
    kind = kinds[0]
    out: dict = {"name": name}
    if kind == "dtype":
        dtype = node["dtype"]
        _require(
            isinstance(dtype, str) and dtype in SCALAR_DTYPES,
            f"unsupported dtype on {'.'.join(here)}: {dtype!r} "
            f"(allowed: {', '.join(sorted(SCALAR_DTYPES))})",
        )
        out["dtype"] = dtype
    elif kind == "struct":
        children = node["struct"]
        _require(
            isinstance(children, list) and children,
            f"struct on {'.'.join(here)} must be a non-empty list of features",
        )
        assert isinstance(children, list)
        out["struct"] = [_validate_feature(child, here) for child in children]
        _reject_duplicate_names(out["struct"], here)
    else:
        children = node["list"]
        if isinstance(children, str):
            _require(
                children in SCALAR_DTYPES,
                f"unsupported list dtype on {'.'.join(here)}: {children!r}",
            )
            out["list"] = children
        else:
            _require(
                isinstance(children, list) and children,
                f"list on {'.'.join(here)} must be a dtype string or a non-empty "
                "list of features",
            )
            assert isinstance(children, list)
            out["list"] = [_validate_feature(child, (*here, "[]")) for child in children]
            _reject_duplicate_names(out["list"], (*here, "[]"))

    if "optional" in node:
        _require(
            isinstance(node["optional"], bool),
            f"optional on {'.'.join(here)} must be a boolean",
        )
        out["optional"] = node["optional"]
    if "note" in node:
        _require(
            isinstance(node["note"], str) and node["note"].strip() != "",
            f"note on {'.'.join(here)} must be a non-empty string",
        )
        out["note"] = node["note"].strip()
    return out


def _reject_duplicate_names(features: list[dict], path: tuple[str, ...]) -> None:
    seen: set[str] = set()
    for feature in features:
        name = feature["name"]
        _require(
            name not in seen,
            f"duplicate feature name {name!r} under {'.'.join(path) or '<top level>'}",
        )
        seen.add(name)


def _validate_disclosure(item: object) -> dict:
    if isinstance(item, str):
        _require(item.strip() != "", "disclosure sentence must not be empty")
        return {"summary": item.strip(), "ids": [], "issues": []}
    _require(isinstance(item, dict), "disclosure must be a string or an object")
    assert isinstance(item, dict)
    unknown = sorted(set(item) - DISCLOSURE_KEYS)
    _require(not unknown, f"unknown disclosure key(s): {', '.join(unknown)}")
    summary = item.get("summary")
    _require(
        isinstance(summary, str) and summary.strip() != "",
        "disclosure needs a non-empty 'summary'",
    )
    assert isinstance(summary, str)
    raw_ids = item.get("ids", [])
    _require(isinstance(raw_ids, list), "disclosure ids must be a list")
    assert isinstance(raw_ids, list)
    ids = []
    for record_id in raw_ids:
        _require(
            isinstance(record_id, str) and record_id.strip() != "",
            f"disclosure id must be a non-empty string: {record_id!r}",
        )
        assert isinstance(record_id, str)
        ids.append(record_id.strip())
    return {
        "summary": summary.strip(),
        "ids": ids,
        "issues": _validate_issues(item.get("issues", []), "disclosure issues"),
    }


# --- YAML emission -------------------------------------------------------


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    _require(isinstance(value, str), f"cannot emit YAML scalar: {value!r}")
    assert isinstance(value, str)
    # A card's YAML front matter is delimited by ``---``; a scalar containing it
    # would truncate the block and silently drop metadata.
    _require("---" not in value, f"YAML scalar may not contain '---': {value!r}")
    _require("\n" not in value, f"YAML scalar may not contain a newline: {value!r}")
    if PLAIN_SCALAR_RE.fullmatch(value) and value.lower() not in YAML_RESERVED:
        return value
    return json.dumps(value)


def _yaml_block(value: object, indent: int) -> list[str]:
    """Render a mapping or list as block-style YAML lines."""
    pad = " " * indent
    lines: list[str] = []
    if isinstance(value, dict):
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
    _require(isinstance(value, list), f"cannot emit YAML for {value!r}")
    assert isinstance(value, list)
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
    out = []
    for feature in features:
        node: dict = {"name": feature["name"]}
        if "dtype" in feature:
            node["dtype"] = feature["dtype"]
        elif "struct" in feature:
            node["struct"] = yaml_features(feature["struct"])
        else:
            child = feature["list"]
            node["list"] = child if isinstance(child, str) else yaml_features(child)
        out.append(node)
    return out


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
    dataset_info: dict = {"features": yaml_features(declaration["features"])}
    if declaration["config_name"] != DEFAULT_CONFIG_NAME:
        dataset_info = {
            "config_name": declaration["config_name"],
            **dataset_info,
        }
    lines.extend(_yaml_block(dataset_info, 2))
    return "\n".join(lines) + "\n"


# --- Card body ------------------------------------------------------------


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
    lines = ["## Dataset viewer schema", ""]
    note = declaration["note"]
    if declaration["issues"]:
        note = f"{note} Tracked in {_issue_links(declaration['issues'])}."
    lines.append(note)
    lines.append("")
    if declaration["features"]:
        patterns = ", ".join(f"`{pattern}`" for pattern in declaration["data_files"])
        lines.append(
            f"The `configs` / `dataset_info` metadata above declares config "
            f"`{declaration['config_name']}`, split `{declaration['split']}`, over "
            f"{patterns}. It is written by hand rather than inferred from the first "
            "shard, so the datasets-server can build a parquet index without any "
            "historical raw record being rewritten."
        )
        lines.append("")
        columns = json_columns(declaration["features"])
        if columns:
            listed = ", ".join(f"`{column}`" for column in columns)
            lines.append(
                f"Key-bag columns are declared as `json` so their keys may differ "
                f"per record without an Arrow cast error: {listed}."
            )
            lines.append("")
    else:
        lines.append(
            "No default `configs` / `dataset_info` block is declared for this "
            "dataset on purpose: the working viewer projection is not replaced by "
            "a raw config."
        )
        lines.append("")

    rows = field_notes(declaration["features"])
    if rows:
        lines.append(
            "Field notes. An optional field is absent on some records; every "
            "declared field is nullable, so it reads back as `null` there "
            "instead of breaking the cast."
        )
        lines.append("")
        lines.append("| Field | Status | Note |")
        lines.append("|---|---|---|")
        for path, optional, note_text in rows:
            status = "optional" if optional else "present on every record"
            lines.append(f"| `{path}` | {status} | {note_text or '—'} |")
        lines.append("")

    if declaration["disclosures"]:
        lines.append("### Known payload disclosures")
        lines.append("")
        for disclosure in declaration["disclosures"]:
            text = disclosure["summary"]
            if disclosure["issues"]:
                text = f"{text} Tracked in {_issue_links(disclosure['issues'])}."
            lines.append(f"- {text}")
            if disclosure["ids"]:
                listed = ", ".join(f"`{record_id}`" for record_id in disclosure["ids"])
                lines.append(f"  Record ids: {listed}.")
        lines.append("")

    return "\n".join(lines)


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


def _glob_matches(path: str, pattern: str) -> bool:
    """Match one repo-relative path with case-sensitive Hub-style glob semantics.

    ``*`` and ``?`` match within one path segment only. A segment consisting
    of ``**`` may consume zero or more complete segments. This prevents a
    declaration such as ``data/raw/*.jsonl`` from covering a nested payload
    that the Hub globber would not select.
    """
    path_parts = path.split("/")
    pattern_parts = pattern.split("/")
    previous = [False] * (len(pattern_parts) + 1)
    previous[0] = True
    for pattern_index, glob in enumerate(pattern_parts, 1):
        if glob == "**":
            previous[pattern_index] = previous[pattern_index - 1]

    for part in path_parts:
        current = [False] * (len(pattern_parts) + 1)
        for pattern_index, glob in enumerate(pattern_parts, 1):
            if glob == "**":
                current[pattern_index] = (
                    current[pattern_index - 1] or previous[pattern_index]
                )
            else:
                current[pattern_index] = previous[
                    pattern_index - 1
                ] and fnmatchcase(part, glob)
        previous = current
    return previous[-1]


def payload_coverage_errors(declaration: dict, payload_names: list[str]) -> list[str]:
    """Return every mismatch between declared globs and published payload files.

    A payload file no glob matches would silently vanish from the viewer while
    the card still counts it; a glob matching nothing would advertise a config
    over an empty file set. Both are reported rather than tolerated.
    """
    if not declaration["features"]:
        return []
    patterns = declaration["data_files"]
    paths = [f"data/raw/{name}" for name in payload_names]
    errors = []
    uncovered = [
        path
        for path in paths
        if not any(_glob_matches(path, pattern) for pattern in patterns)
    ]
    if uncovered:
        errors.append(
            "published payload not matched by any declared data_files pattern: "
            + ", ".join(sorted(uncovered))
        )
    unused = [
        pattern
        for pattern in patterns
        if not any(_glob_matches(path, pattern) for path in paths)
    ]
    if unused:
        errors.append(
            "declared data_files pattern matches no published payload: "
            + ", ".join(unused)
        )
    return errors
