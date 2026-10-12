#!/usr/bin/env python3
"""A Hub-ready dataset directory from one complete export: typed configs, real splits.

The procedural datasets on the Hub expose one ``viewer`` config whose
``record_json`` column is a JSON string, so a trainer parses records by hand
and every row lands in one ``train`` split although each record carries its
lineage split. This module turns a complete export (:func:`export.run`) into a
directory the Hub can serve as-is: the three text renderings per split as
``sft``, ``chat`` and ``edit`` configs with ``train`` / ``validation`` /
``held_out`` splits, the lossless ``viewer`` projection over the evidence file
(the same writer the published datasets use), the export manifest, the held-out
freeze, the attribution notices, and a card, ``provenance.json`` and
``release-status.json`` whose training-readiness statement is derived from the
manifest's admission block rather than typed by hand.

Every export file is re-digested against the manifest before it is copied and
the viewer projection is read back and compared to the evidence lines; a
mismatch refuses the whole bundle. The bundle is written to a brand-new
destination outside ``outputs/raw/``. Nothing here creates or uploads a Hub
repository or launches a trainer.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import export, lineage
from . import source_policy as sp
from . import vocabulary as cv
from ._contract import (
    ViewerRow,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    load_strict_json,
    read_viewer_parquet,
    write_viewer_parquet,
)

BUNDLE_FORMAT = "code-repair-hub-bundle/1"
BUNDLE_FILENAME = "BUNDLE.json"
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
SOURCE_REPOSITORY = "https://github.com/rmems/synthetic-factory"
NOTICE_FILES = ("LICENSE.upstream", "NOTICE.txt")
STAGE_ADMITTED = "admitted_training_candidate"
STAGE_BLOCKED = "blocked_candidate_export"
_DATASET_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_BARE_YAML = re.compile(r"[A-Za-z][A-Za-z0-9_./-]*")
_YAML_RESERVED = frozenset({"true", "false", "null", "yes", "no", "on", "off", "y", "n"})
_TAGS = (
    "synthetic-data", "code-repair", "software-engineering", "deterministic-execution",
    "procedural", "provenance",
)

__all__ = [
    "BUNDLE_FILENAME",
    "BUNDLE_FORMAT",
    "CARD_FILENAME",
    "TEXT_CONFIGS",
    "VIEWER_PATH",
    "BundleFacts",
    "BundleRequest",
    "render_card",
    "run",
    "training_ready",
]


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
    def run(self) -> dict[str, Any]:
        return self.manifest["run"]

    @property
    def catalog(self) -> dict[str, Any]:
        catalog = self.run.get("catalog")
        return catalog if isinstance(catalog, dict) else {}


# --- request and manifest ------------------------------------------------------------------


def _check_request(request: BundleRequest) -> None:
    export_dir, out_dir = Path(request.export_dir), Path(request.out_dir)
    manifest = export_dir / export.MANIFEST_FILENAME
    cv.refuse_first((
        (not isinstance(request.dataset_id, str)
         or _DATASET_ID.fullmatch(request.dataset_id) is None,
         cv.FINDING_BUNDLE_REQUEST_INVALID, "dataset id must be owner/name"),
        (request.pretty_name is not None
         and (not isinstance(request.pretty_name, str) or not request.pretty_name.strip()
              or "\n" in request.pretty_name),
         cv.FINDING_BUNDLE_REQUEST_INVALID, "pretty name must be one nonempty line"),
        (not manifest.is_file(), cv.FINDING_RUN_FILE_MISSING, f"{cv.shown(manifest)} is missing"),
        (is_under_raw(out_dir), cv.FINDING_DESTINATION_UNDER_RAW,
         f"{cv.shown(out_dir)} names or aliases the raw tree"),
        (out_dir.exists(), cv.FINDING_DESTINATION_EXISTS, f"{cv.shown(out_dir)} already exists"),
    ))


def _required_paths() -> list[str]:
    text = [f"{directory}/{split}.jsonl" for _name, directory in TEXT_CONFIGS
            for split in lineage.SPLITS]
    return [*text, export.AGOGE_PATH, export.EVIDENCE_PATH, export.FREEZE_PATH]


def _digest_entry_ok(path: Any, digest: Any) -> bool:
    return isinstance(path, str) and isinstance(digest, str) and _HEX64.fullmatch(digest) is not None


def _files_ok(files: Any) -> bool:
    """Every pinned path has a SHA-256 digest and every required export file is pinned."""

    if not isinstance(files, dict):
        return False
    pinned = all(_digest_entry_ok(path, digest) for path, digest in files.items())
    return pinned and all(path in files for path in _required_paths())


def _admission_ok(admission: Any) -> bool:
    return (isinstance(admission, dict) and isinstance(admission.get("blockers"), list)
            and admission.get("training_export") in ("training_candidate", "blocked"))


def _sections_ok(manifest: dict[str, Any]) -> bool:
    return (manifest.get("format") == export.EXPORT_FORMAT
            and manifest.get("pipeline_status") == "complete"
            and isinstance(manifest.get("replay"), str)
            and all(isinstance(manifest.get(key), dict) for key in ("tables", "run", "rights")))


def _manifest_shape_ok(manifest: Any) -> bool:
    return (isinstance(manifest, dict) and _sections_ok(manifest)
            and _files_ok(manifest.get("files")) and _admission_ok(manifest.get("admission")))


def _load_manifest(payload: bytes) -> dict[str, Any]:
    try:
        manifest = load_strict_json(payload)
    except ValueError as exc:
        raise cv.RepairRefusal(cv.FINDING_BUNDLE_MANIFEST_INVALID,
                               f"export manifest is not JSON: {cv.shown(exc)}") from exc
    cv.refuse_when(not _manifest_shape_ok(manifest), cv.FINDING_BUNDLE_MANIFEST_INVALID,
                   "export manifest is not a complete code-repair export manifest")
    return manifest


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _verified_files(export_dir: Path, manifest: dict[str, Any]) -> dict[str, bytes]:
    """Every manifest-pinned file's exact bytes; a missing or drifted file refuses."""

    verified: dict[str, bytes] = {}
    for relative, digest in manifest["files"].items():
        path = export_dir / relative
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise cv.RepairRefusal(cv.FINDING_EXPORT_INTEGRITY,
                                   f"export file {cv.shown(relative)} is unreadable") from exc
        cv.refuse_when(_sha(payload) != digest, cv.FINDING_EXPORT_INTEGRITY,
                       f"export file {cv.shown(relative)} differs from its manifest digest")
        verified[relative] = payload
    return verified


def training_ready(manifest: dict[str, Any]) -> bool:
    """Admitted, unblocked and replayed; derived from the manifest, never asserted."""

    admission = manifest["admission"]
    return (admission["training_export"] == "training_candidate"
            and not admission["blockers"] and manifest["replay"] == "passed")


# --- projections -----------------------------------------------------------------------------


def _row_count(payload: bytes) -> int:
    return payload.count(b"\n")


def _viewer_rows(evidence: bytes) -> list[ViewerRow]:
    try:
        text = evidence.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise cv.RepairRefusal(cv.FINDING_EXPORT_INTEGRITY, "evidence is not UTF-8") from exc
    lines = text.split("\n")
    cv.refuse_when(lines and lines[-1] != "", cv.FINDING_EXPORT_INTEGRITY,
                   "evidence is not LF-terminated")
    return [ViewerRow(VIEWER_SOURCE_FILE, number, line)
            for number, line in enumerate(lines[:-1], start=1)]


def _viewer_parquet(evidence: bytes) -> tuple[bytes, int]:
    rows = _viewer_rows(evidence)
    cv.refuse_when(not rows, cv.FINDING_EXPORT_INTEGRITY, "evidence holds no records")
    payload = write_viewer_parquet(rows)
    cv.refuse_when(read_viewer_parquet(payload) != rows, cv.FINDING_EXPORT_INTEGRITY,
                   "viewer projection did not round-trip")
    return payload, len(rows)


def _text_counts(files: dict[str, bytes]) -> dict[str, dict[str, int]]:
    return {name: {split: _row_count(files[f"{directory}/{split}.jsonl"])
                   for split in lineage.SPLITS}
            for name, directory in TEXT_CONFIGS}


def _data_path(directory: str, split: str) -> str:
    return f"{DATA_DIR}/{directory}/{split}.jsonl"


def _configs(counts: dict[str, dict[str, int]], viewer_rows: int) -> list[dict[str, Any]]:
    configs = []
    for name, directory in TEXT_CONFIGS:
        data_files = [{"split": split, "path": _data_path(directory, split)}
                      for split in lineage.SPLITS if counts[name][split]]
        if data_files:
            configs.append({"config_name": name, "data_files": data_files})
    if viewer_rows:
        configs.append({"config_name": VIEWER_CONFIG,
                        "data_files": [{"split": "train", "path": VIEWER_PATH}]})
    return configs


_FEATURES = {
    "sft": [{"name": "prompt", "dtype": "string"}, {"name": "completion", "dtype": "string"}],
    "edit": [{"name": "prompt", "dtype": "string"}, {"name": "completion", "dtype": "string"}],
    "chat": [{"name": "messages", "list": [{"name": "role", "dtype": "string"},
                                           {"name": "content", "dtype": "string"}]}],
    VIEWER_CONFIG: [{"name": "source_file", "dtype": "string"},
                    {"name": "source_line", "dtype": "int64"},
                    {"name": "record_json", "dtype": "string"}],
}


def _dataset_info(configs: list[dict[str, Any]], counts: dict[str, dict[str, int]],
                  sizes: dict[str, int], viewer_rows: int, viewer_bytes: int) -> list[dict]:
    info = []
    for config in configs:
        name = config["config_name"]
        if name == VIEWER_CONFIG:
            splits = [{"name": "train", "num_examples": viewer_rows, "num_bytes": viewer_bytes}]
        else:
            splits = [{"name": entry["split"], "num_examples": counts[name][entry["split"]],
                       "num_bytes": sizes[entry["path"]]} for entry in config["data_files"]]
        info.append({"config_name": name, "features": _FEATURES[name], "splits": splits})
    return info


# --- card ------------------------------------------------------------------------------------


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


def _yaml(value: Any, indent: int = 0) -> list[str]:
    """A deterministic YAML rendering of nested dicts, lists and scalars."""

    pad = "  " * indent
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{pad}{key}:")
                lines.extend(_yaml(item, indent + 1))
            else:
                lines.append(f"{pad}{key}: {_empty_or_scalar(item)}")
        return lines
    for item in value:
        if isinstance(item, dict) and item:
            first, *rest = _yaml(item, indent + 1)
            lines.append(f"{pad}- {first.strip()}")
            lines.extend(rest)
        else:
            lines.append(f"{pad}- {_scalar(item)}")
    return lines


def _front_matter(facts: BundleFacts) -> str:
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
    exported = tables.get("dispositions", {}).get("exported", 0)
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


def _card_splits(facts: BundleFacts) -> list[str]:
    frozen = facts.freeze.get("canonical_ids", [])
    agoge_keys = "`, `".join(export.VIEW_FORMATS["agoge"]["keys"])
    return [
        "## Configs and splits",
        "",
        ("Splits are assigned per program group by the catalog's pinned policy "
         f"(`{_inline_policy(facts.run.get('split_policy'))}`), so no upstream program, "
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
        *_reproduce_commands(facts.request, facts.run, catalog),
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


def _reproduce_commands(request: BundleRequest, run: dict[str, Any], catalog: dict) -> list[str]:
    """The four commands behind the bundle; only the sealed catalog has a repository path."""

    sealed = catalog.get("catalog_id") == sp.POLICY["catalog_id"]
    catalog_dir = f"catalogs/{catalog.get('catalog_id')}" if sealed else "<catalog-dir>"
    tool = "python3 pipelines/code_repair_cli.py"
    return [
        (f"{tool} generate --catalog {catalog_dir} --seed {run.get('seed')} "
         f"--count {run.get('count')} --out <run-dir>"),
        f"{tool} replay --run <run-dir> --catalog {catalog_dir} --out <replay-dir>",
        (f"{tool} export --run <run-dir> --catalog {catalog_dir} --replay <replay-dir> "
         "--out <export-dir>"),
        (f"{tool} hub-bundle --export <export-dir> --out <bundle-dir> "
         f"--dataset-id {request.dataset_id}"),
    ]


def _inline_policy(policy: Any) -> str:
    if not isinstance(policy, dict):
        return "unpinned"
    weights = policy.get("weights") if isinstance(policy.get("weights"), dict) else {}
    return (f"{policy.get('algorithm')} seed {policy.get('seed')} salt {policy.get('salt')} "
            + "/".join(str(weights.get(split)) for split in lineage.SPLITS))


# --- machine-readable companions -----------------------------------------------------------


def _provenance(facts: BundleFacts) -> dict[str, Any]:
    manifest, run, catalog, ready = facts.manifest, facts.run, facts.catalog, facts.ready
    generator = run.get("generator") if isinstance(run.get("generator"), dict) else {}
    digests = facts.digests
    return {
        "schema_version": "1.0.0",
        "dataset_id": facts.request.dataset_id,
        "purpose": ("Deterministic Python function-repair records: a project-owned mutator breaks "
                    "real MIT-licensed programs, the harness executes original, mutant, repaired "
                    "and reference phases, and every positive is re-verified by fresh replay"),
        "primary_target": ("Supervised fine-tuning and evaluation of code repair under the "
                           "registry's training-candidate route" if ready else
                           "Research retention and evaluation; admission pending"),
        "generation": {
            "primary_model": None,
            "generator": f"{generator.get('name')} {generator.get('version')} (project-owned)",
            "contribution": "Generated every record in this release",
            "method": ("pipelines/code_repair_cli.py generate, catalog "
                       f"{catalog.get('catalog_id')}, seed {run.get('seed')}, "
                       f"count {run.get('count')}; export "
                       f"{export.EXPORT_FORMAT}; replay {manifest['replay']}"),
        },
        "source_factory": sp.POLICY["path_id"],
        "source_repository": SOURCE_REPOSITORY,
        "payload_published": False,
        "training_ready": ready,
        "admission": manifest["admission"],
        "catalog_pins": {"catalog_id": catalog.get("catalog_id"),
                         "programs_sha256": catalog.get("programs_sha256"),
                         "program_count": catalog.get("program_count")},
        "source_license_evidence": dict(sp.POLICY["source_license_evidence"]),
        "export_manifest_sha256": facts.manifest_sha256,
        "files": [{"path": path, "sha256": digests[path],
                   "records": facts.record_counts.get(path)} for path in sorted(digests)],
        "viewer": {"path": VIEWER_PATH, "rows": facts.viewer_rows, "bytes": facts.viewer_bytes,
                   "sha256": digests[VIEWER_PATH],
                   "writer": "synthetic-factory export_viewer (stdlib PLAIN parquet)"},
        "rights": manifest["rights"],
        "evaluation_limitations": manifest.get("evaluation_limitations", []),
        "training_run_prerequisites": manifest.get("training_run_prerequisites", []),
    }


def _release_status(facts: BundleFacts) -> dict[str, Any]:
    manifest, ready = facts.manifest, facts.ready
    return {
        "schema_version": "1.0.0",
        "dataset_id": facts.request.dataset_id,
        "release_stage": STAGE_ADMITTED if ready else STAGE_BLOCKED,
        "visibility": "not_uploaded",
        "payload_published": False,
        "training_ready": ready,
        "strict_audit": "fresh_code_repair_gate" if ready else "pending_admission",
        "license": RELEASE_LICENSE,
        "intended_use": "training_candidate",
        "project_training_policy": manifest["rights"].get("project_training_policy"),
        "admission": manifest["admission"],
        "replay": manifest["replay"],
        "produced_at": manifest["run"].get("produced_at"),
        "rights_record": None,
    }


def _release_license() -> bytes:
    payload = (sp.ROOT / LICENSE_FILENAME).read_bytes()
    cv.refuse_when(b"Apache License" not in payload or b"Version 2.0" not in payload,
                   cv.FINDING_BUNDLE_REQUEST_INVALID,
                   "the repository LICENSE is not the Apache-2.0 text the card declares")
    return payload


# --- writing -----------------------------------------------------------------------------------


def _write(root: Path, relative: str, payload: bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "xb") as handle:
        handle.write(payload)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    text = dumps_exact_json(payload, ensure_ascii=True, indent=2, sort_keys=True)
    return (text + "\n").encode("utf-8")


def _bundle_files(files: dict[str, bytes], manifest_bytes: bytes) -> dict[str, bytes]:
    """The export files at their bundle paths plus the evidence companions."""

    bundled: dict[str, bytes] = {}
    for _name, directory in TEXT_CONFIGS:
        for split in lineage.SPLITS:
            bundled[_data_path(directory, split)] = files[f"{directory}/{split}.jsonl"]
    bundled[f"{DATA_DIR}/{export.AGOGE_PATH}"] = files[export.AGOGE_PATH]
    bundled[f"{EVIDENCE_DIR}/{VIEWER_SOURCE_FILE}"] = files[export.EVIDENCE_PATH]
    bundled[f"{EVIDENCE_DIR}/{Path(export.FREEZE_PATH).name}"] = files[export.FREEZE_PATH]
    bundled[f"{EVIDENCE_DIR}/{export.MANIFEST_FILENAME}"] = manifest_bytes
    for name in NOTICE_FILES:
        if name in files:
            bundled[name] = files[name]
    return bundled


def _load_export(export_dir: Path) -> tuple[bytes, dict[str, Any], dict[str, bytes], dict]:
    """The manifest bytes and object, every pinned file's verified bytes, and the freeze."""

    manifest_bytes = (export_dir / export.MANIFEST_FILENAME).read_bytes()
    manifest = _load_manifest(manifest_bytes)
    files = _verified_files(export_dir, manifest)
    freeze = load_strict_json(files[export.FREEZE_PATH])
    cv.refuse_when(not isinstance(freeze, dict), cv.FINDING_BUNDLE_MANIFEST_INVALID,
                   "the held-out freeze is not an object")
    return manifest_bytes, manifest, files, freeze


def _record_counts(files: dict[str, bytes], counts: dict[str, dict[str, int]],
                   viewer_rows: int) -> dict[str, int]:
    record_counts = {
        _data_path(directory, split): counts[name][split]
        for name, directory in TEXT_CONFIGS for split in lineage.SPLITS
    }
    record_counts[f"{EVIDENCE_DIR}/{VIEWER_SOURCE_FILE}"] = viewer_rows
    record_counts[VIEWER_PATH] = viewer_rows
    record_counts[f"{DATA_DIR}/{export.AGOGE_PATH}"] = _row_count(files[export.AGOGE_PATH])
    return record_counts


def _assemble(request: BundleRequest) -> tuple[dict[str, bytes], BundleFacts]:
    """The bundle's data files at their paths, and the facts its companions describe."""

    manifest_bytes, manifest, files, freeze = _load_export(Path(request.export_dir))
    viewer_bytes, viewer_rows = _viewer_parquet(files[export.EVIDENCE_PATH])
    bundled = _bundle_files(files, manifest_bytes)
    bundled[VIEWER_PATH] = viewer_bytes
    bundled[LICENSE_FILENAME] = _release_license()
    counts = _text_counts(files)
    configs = _configs(counts, viewer_rows)
    sizes = {path: len(payload) for path, payload in bundled.items()}
    facts = BundleFacts(
        request=request, manifest=manifest, manifest_sha256=_sha(manifest_bytes),
        ready=training_ready(manifest), freeze=freeze, counts=counts, viewer_rows=viewer_rows,
        viewer_bytes=len(viewer_bytes), configs=configs,
        info=_dataset_info(configs, counts, sizes, viewer_rows, len(viewer_bytes)),
        digests={path: _sha(payload) for path, payload in bundled.items()},
        record_counts=_record_counts(files, counts, viewer_rows),
    )
    return bundled, facts


def _companions(facts: BundleFacts) -> dict[str, bytes]:
    card = _front_matter(facts) + "\n" + render_card(facts)
    return {
        PROVENANCE_FILENAME: _json_bytes(_provenance(facts)),
        RELEASE_STATUS_FILENAME: _json_bytes(_release_status(facts)),
        CARD_FILENAME: card.encode("utf-8"),
    }


def _summary(facts: BundleFacts, bundled: dict[str, bytes]) -> dict[str, Any]:
    return {
        "format": BUNDLE_FORMAT, "dataset_id": facts.request.dataset_id,
        "training_ready": facts.ready, "export_manifest_sha256": facts.manifest_sha256,
        "configs": [config["config_name"] for config in facts.configs],
        "rows": {**facts.counts, VIEWER_CONFIG: {"train": facts.viewer_rows}},
        "files": {path: _sha(payload) for path, payload in sorted(bundled.items())},
    }


def run(request: BundleRequest) -> dict[str, Any]:
    """Build the bundle into a brand-new directory; returns the summary written as BUNDLE.json."""

    _check_request(request)
    bundled, facts = _assemble(request)
    bundled.update(_companions(facts))
    summary = _summary(facts, bundled)
    root = Path(request.out_dir)
    root.mkdir(parents=True, exist_ok=False)
    for relative, payload in bundled.items():
        _write(root, relative, payload)
    _write(root, BUNDLE_FILENAME, _json_bytes(summary))
    return summary


bind_import_twin(__name__)
