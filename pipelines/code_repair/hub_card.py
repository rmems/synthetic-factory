"""The Hub dataset card of a code-repair bundle: layout names, facts, front matter, body.

Split from :mod:`hub_bundle` by responsibility: :mod:`hub_bundle` verifies an
export and assembles the bundle's bytes; this module holds the bundle layout
the card describes, the :class:`BundleFacts` it is rendered from, the
deterministic YAML front matter, and the Markdown body. Every statement on the
card is derived from the export manifest; nothing here reads files.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import export, lineage
from . import source_policy as sp
from ._contract import bind_import_twin

CARD_FILENAME = "README.md"
PROVENANCE_FILENAME = "provenance.json"
RELEASE_STATUS_FILENAME = "release-status.json"
LICENSE_FILENAME = "LICENSE"
RELEASE_LICENSE = "apache-2.0"
DATA_DIR = "data"
EVIDENCE_DIR = "evidence"
VIEWER_PATH = f"{DATA_DIR}/viewer/records.parquet"
VIEWER_SOURCE_FILE = "candidates.jsonl"
VIEWER_CONFIG = "viewer"
TEXT_CONFIGS = (("sft", export.SFT_DIR), ("chat", export.CHAT_DIR), ("edit", export.EDIT_DIR))
NOTICE_FILES = ("LICENSE.upstream", "NOTICE.txt")
_BARE_YAML = re.compile(r"[A-Za-z][A-Za-z0-9_./-]*")
_YAML_RESERVED = frozenset({"true", "false", "null", "yes", "no", "on", "off", "y", "n"})
_TAGS = (
    "synthetic-data", "code-repair", "software-engineering", "deterministic-execution",
    "procedural", "provenance",
)

__all__ = ["BundleFacts", "BundleRequest", "front_matter", "render_card"]


@dataclass(frozen=True)
class BundleRequest:
    export_dir: Path
    out_dir: Path
    dataset_id: str
    pretty_name: str | None = None


@dataclass(frozen=True)
class BundleFacts:
    """Everything the card and the machine-readable companions are rendered from."""

    request: BundleRequest
    manifest: dict[str, Any]
    manifest_sha256: str
    ready: bool
    freeze: dict[str, Any]
    counts: dict[str, dict[str, int]]
    viewer_rows: int
    viewer_bytes: int
    configs: list[dict[str, Any]]
    info: list[dict[str, Any]]
    digests: dict[str, str]
    record_counts: dict[str, int]

    @property
    def run_meta(self) -> dict[str, Any]:
        return self.manifest["run"]

    @property
    def catalog(self) -> dict[str, Any]:
        catalog = self.run_meta.get("catalog")
        return catalog if isinstance(catalog, dict) else {}


def _is_block(item: Any) -> bool:
    return isinstance(item, (dict, list)) and bool(item)


def _yaml(value: Any, indent: int = 0) -> list[str]:
    """A deterministic YAML rendering of nested dicts, lists and scalars."""

    if isinstance(value, dict):
        return _yaml_mapping(value, indent)
    return _yaml_sequence(value, indent)


def _yaml_mapping(value: dict[str, Any], indent: int) -> list[str]:
    pad = "  " * indent
    lines: list[str] = []
    for key, item in value.items():
        if _is_block(item):
            lines.append(f"{pad}{key}:")
            lines.extend(_yaml(item, indent + 1))
        else:
            lines.append(f"{pad}{key}: {_empty_or_scalar(item)}")
    return lines


def _yaml_sequence(value: list[Any], indent: int) -> list[str]:
    pad = "  " * indent
    lines: list[str] = []
    for item in value:
        if isinstance(item, dict) and item:
            first, *rest = _yaml(item, indent + 1)
            lines.append(f"{pad}- {first.strip()}")
            lines.extend(rest)
        else:
            lines.append(f"{pad}- {_scalar(item)}")
    return lines


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if _BARE_YAML.fullmatch(text) and text.lower() not in _YAML_RESERVED:
        return text
    return json.dumps(text, ensure_ascii=True)


def _empty_or_scalar(item: Any) -> str:
    if isinstance(item, dict):
        return "{}"
    if isinstance(item, list):
        return "[]"
    return _scalar(item)


def front_matter(facts: BundleFacts) -> str:
    header = {
        "pretty_name": _pretty_name(facts.request),
        "license": RELEASE_LICENSE,
        "language": ["en"],
        "task_categories": ["text-generation"],
        "tags": [*_TAGS, "training-candidate" if facts.ready else "research-snapshot"],
        "configs": facts.configs,
        "dataset_info": facts.info,
    }
    return "---\n" + "\n".join(_yaml(header)) + "\n---\n"


def _pretty_name(request: BundleRequest) -> str:
    if request.pretty_name:
        return request.pretty_name.strip()
    return f"Python Function Repair ({request.dataset_id.split('/', 1)[1]})"


def _rights_lines(manifest: dict[str, Any], ready: bool) -> list[str]:
    admission, rights = manifest["admission"], manifest["rights"]
    policy = sp.POLICY
    if ready:
        statement = (
            "**admitted training candidate.** A completed local round was freshly replayed "
            "against the sealed catalog and the export carries `training_export: "
            "training_candidate` with no blockers. Admission is a dataset gate; it is not a "
            "claim that training on these rows improves any model."
        )
    else:
        blockers = ", ".join(f"`{code}`" for code in admission["blockers"]) or "none listed"
        statement = (
            f"**not training-ready.** The export carries `training_export: blocked` with "
            f"blockers {blockers}; this is a research snapshot of a candidate export."
        )
    evidence = policy["source_license_evidence"]
    return [
        f"> **Rights & intended use:** {statement}",
        (f"> Registry route `{policy['path_id']}`: `intended_use: training_candidate`, "
         f"`project_training_policy: {rights.get('project_training_policy')}`."),
        (f"> License: [Apache-2.0](./{LICENSE_FILENAME}) for generated content; upstream programs "
         f"remain {evidence['license']} by their authors ({evidence['repository']} @ "
         f"`{evidence['commit'][:12]}`; `{NOTICE_FILES[0]}` and `{NOTICE_FILES[1]}` ride an "
         "admitted export)."),
        (f"> Machine-readable: [`{PROVENANCE_FILENAME}`](./{PROVENANCE_FILENAME}), "
         f"[`{RELEASE_STATUS_FILENAME}`](./{RELEASE_STATUS_FILENAME}) and the export manifest "
         f"[`{EVIDENCE_DIR}/{export.MANIFEST_FILENAME}`]"
         f"(./{EVIDENCE_DIR}/{export.MANIFEST_FILENAME})."),
    ]


def _verification_lines(manifest: dict[str, Any]) -> list[str]:
    tables = manifest["tables"]
    dispositions = tables.get("dispositions")
    exported = dispositions.get("exported", 0) if isinstance(dispositions, dict) else 0
    return [(
        f"> **Verification:** replay `{manifest['replay']}`; {tables.get('positives')} positive "
        f"records (accepted and validated) out of {tables.get('records')} "
        f"(outcomes {_inline(tables.get('outcomes'))}; oracle statuses "
        f"{_inline(tables.get('oracle_statuses'))}); {exported} rows exported per rendering after "
        f"exact and structural dedup and the lineage cap ({manifest.get('lineage_cap')}). Every "
        "record keeps its five-phase execution evidence in "
        f"`{EVIDENCE_DIR}/{VIEWER_SOURCE_FILE}`."
    )]


def _inline(mapping: Any) -> str:
    if not isinstance(mapping, dict) or not mapping:
        return "none"
    return ", ".join(f"{key} {value}" for key, value in sorted(mapping.items()))


def _config_table(counts: dict[str, dict[str, int]], configs: list[dict[str, Any]],
                  viewer_rows: int) -> list[str]:
    declared = {config["config_name"] for config in configs}
    lines = ["| config | " + " / ".join(lineage.SPLITS) + " | row shape |", "|---|---:|---|"]
    for name, _directory in TEXT_CONFIGS:
        cells = " / ".join(str(counts[name][split]) for split in lineage.SPLITS)
        shape = export.VIEW_FORMATS[name]
        note = "" if name in declared else " (no rows; not declared as a config)"
        keys = "`, `".join(shape["keys"])
        lines.append(f"| `{name}`{note} | {cells} | `{keys}`: {shape['completion']} |")
    viewer = ("lossless `source_file` / `source_line` / `record_json` over "
              f"`{EVIDENCE_DIR}/{VIEWER_SOURCE_FILE}`")
    lines.append(f"| `{VIEWER_CONFIG}` | {viewer_rows} (one `train` split) | {viewer} |")
    return lines


def _file_table(digests: dict[str, str], counts: dict[str, int]) -> list[str]:
    lines = ["| file | records | sha256 |", "|---|---:|---|"]
    for relative in sorted(digests):
        records = counts.get(relative)
        shown = "" if records is None else records
        lines.append(f"| `{relative}` | {shown} | `{digests[relative][:12]}`… |")
    return lines


def train_only_omission(counts: dict[str, dict[str, int]]) -> str | None:
    """Warn when train rows exist and the held-out consumer split is empty.

    Generator 2.1.0 draws train programs only. The bundle still omits empty
    splits; this sentence is what makes that omission visible.
    """

    sft = counts.get("sft") or {}
    if sft.get("train") and not sft.get("held_out"):
        return (
            "Generator 2.1.0 draws train-split programs only, so the `validation` and "
            "`held_out` consumer files are empty and those splits are omitted from the "
            "configs. That omission is limitation `TRAIN_ONLY_DRAW_OMITS_EVAL_SPLITS`."
        )
    return None


def _card_splits(facts: BundleFacts) -> list[str]:
    frozen = facts.freeze.get("canonical_ids", [])
    agoge_keys = "`, `".join(export.VIEW_FORMATS["agoge"]["keys"])
    lines = [
        "## Configs and splits",
        "",
        ("Splits are assigned per program group by the catalog's pinned policy "
         f"(`{_inline_policy(facts.run_meta.get('split_policy'))}`), so no upstream program, "
         "structural twin or reference sibling crosses a split. The `held_out` rows are frozen "
         f"by digest in `{EVIDENCE_DIR}/{Path(export.FREEZE_PATH).name}` (canonical ids frozen: "
         f"{len(frozen) if isinstance(frozen, list) else 0}); never fit on them."),
        "",
        *_config_table(facts.counts, facts.configs, facts.viewer_rows),
        "",
        (f"`{DATA_DIR}/{export.AGOGE_PATH}` carries the consumer rows (`{agoge_keys}`) for the "
         "Agoge trainer and is not declared as a config."),
        "",
    ]
    omission = train_only_omission(facts.counts)
    if omission:
        lines.extend((omission, ""))
    return lines


def _card_limitations(manifest: dict[str, Any]) -> list[str]:
    return [
        "## Evaluation limitations and prerequisites",
        "",
        *[f"- `{code}`" for code in manifest.get("evaluation_limitations", [])],
        *[f"- `{code}` (training-run prerequisite)"
          for code in manifest.get("training_run_prerequisites", [])],
        "",
    ]


def _card_reproduce(facts: BundleFacts) -> list[str]:
    catalog = facts.catalog
    return [
        "## Reproduce",
        "",
        (f"From the factory repository, with the catalog `{catalog.get('catalog_id')}` "
         f"(`programs_sha256` `{str(catalog.get('programs_sha256'))[:12]}`…):"),
        "",
        "```bash",
        *_reproduce_commands(facts.request, facts.run_meta, catalog),
        "```",
        "",
        "Neither this bundle nor the commands above create a Hub repository or launch a trainer.",
        "",
    ]


def render_card(facts: BundleFacts) -> str:
    """The card body below the front matter, assembled from its sections."""

    body = [
        f"# {_pretty_name(facts.request)}",
        "",
        *_rights_lines(facts.manifest, facts.ready),
        "",
        *_verification_lines(facts.manifest),
        "",
        *_card_splits(facts),
        *_card_limitations(facts.manifest),
        "## Files",
        "",
        *_file_table(facts.digests, facts.record_counts),
        "",
        *_card_reproduce(facts),
    ]
    return "\n".join(body)


def _reproduce_commands(request: BundleRequest, run_meta: dict[str, Any],
                        catalog: dict) -> list[str]:
    """The four commands behind the bundle; only the sealed catalog has a repository path."""

    sealed = catalog.get("catalog_id") == sp.POLICY["catalog_id"]
    catalog_dir = f"catalogs/{catalog.get('catalog_id')}" if sealed else "<catalog-dir>"
    tool = "python3 pipelines/code_repair_cli.py"
    return [
        (f"{tool} generate --catalog {catalog_dir} --seed {run_meta.get('seed')} "
         f"--count {run_meta.get('count')} --out <run-dir>"),
        f"{tool} replay --run <run-dir> --catalog {catalog_dir} --out <replay-dir>",
        (f"{tool} export --run <run-dir> --catalog {catalog_dir} --replay <replay-dir> "
         "--out <export-dir>"),
        (f"{tool} hub-bundle --export <export-dir> --out <bundle-dir> "
         f"--dataset-id {request.dataset_id}"),
    ]


def _inline_policy(policy: Any) -> str:
    """The pinned policy in one line; the bundle refuses a malformed one before rendering."""

    if policy is None:
        return "unpinned"
    parsed = lineage.SplitPolicy.from_json(policy)
    return (f"{parsed.algorithm} seed {parsed.seed} salt {parsed.salt} "
            + "/".join(str(parsed.weights[split]) for split in lineage.SPLITS))


bind_import_twin(__name__)
