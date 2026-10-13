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

Every export file is re-digested against the manifest before it is copied, the
held-out freeze's ``sft`` / ``chat`` / ``edit`` digests are recomputed over the
held-out JSONL bytes, and the viewer projection is read back and compared to
the evidence lines; a mismatch or a missing freeze digest refuses the whole
bundle even when the manifest's own file digests are consistent. The bundle is
written to a brand-new destination outside ``outputs/raw/``. Nothing here
creates or uploads a Hub repository or launches a trainer.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from . import export, lineage
from . import source_policy as sp
from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, is_under_raw, load_strict_json
from .hub_card import (
    CARD_FILENAME,
    DATA_DIR,
    EVIDENCE_DIR,
    LICENSE_FILENAME,
    NOTICE_FILES,
    PROVENANCE_FILENAME,
    RELEASE_LICENSE,
    RELEASE_STATUS_FILENAME,
    TEXT_CONFIGS,
    VIEWER_CONFIG,
    VIEWER_PATH,
    VIEWER_SOURCE_FILE,
    BundleFacts,
    BundleRequest,
    front_matter,
    render_card,
)

# The lossless viewer writer the published datasets use, under this module's import form.
if __name__.startswith("pipelines."):
    from ..export_viewer import ViewerRow, read_viewer_parquet, write_viewer_parquet
else:
    from export_viewer import ViewerRow, read_viewer_parquet, write_viewer_parquet

BUNDLE_FORMAT = "code-repair-hub-bundle/1"
BUNDLE_FILENAME = "BUNDLE.json"
SOURCE_REPOSITORY = "https://github.com/rmems/synthetic-factory"
STAGE_ADMITTED = "admitted_training_candidate"
STAGE_BLOCKED = "blocked_candidate_export"
_DATASET_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*")
_HEX64 = re.compile(r"[0-9a-f]{64}")

__all__ = [
    "BUNDLE_FILENAME", "BUNDLE_FORMAT", "STAGE_ADMITTED", "STAGE_BLOCKED", "read_viewer_parquet",
    "run", "training_ready",
]


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
    typed = isinstance(path, str) and isinstance(digest, str)
    return typed and _HEX64.fullmatch(digest) is not None


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


def _policy_ok(policy: Any) -> bool:
    """``None`` (unpinned) or a split policy the lineage parser accepts."""

    if policy is None:
        return True
    try:
        lineage.SplitPolicy.from_json(policy)
    except cv.RepairRefusal:
        return False
    return True


def _contents_ok(manifest: dict[str, Any]) -> bool:
    return (_files_ok(manifest.get("files")) and _admission_ok(manifest.get("admission"))
            and _policy_ok(manifest["run"].get("split_policy")))


def _manifest_shape_ok(manifest: Any) -> bool:
    return isinstance(manifest, dict) and _sections_ok(manifest) and _contents_ok(manifest)


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


def _sha256_pin(pinned: Any) -> str | None:
    if isinstance(pinned, str) and _HEX64.fullmatch(pinned) is not None:
        return pinned
    return None


def _held_out_digest_ok(freeze: dict, files: dict[str, bytes], directory: str) -> bool:
    """Whether this rendering's freeze digest is the sha256 of the held-out bytes."""

    pinned = _sha256_pin(freeze.get(f"{directory}_sha256"))
    payload = files.get(f"{directory}/held_out.jsonl")
    return isinstance(payload, bytes) and pinned is not None and _sha(payload) == pinned


def _check_held_out_freeze(freeze: dict, files: dict[str, bytes]) -> None:
    """Refuse a missing or mismatched rendering digest, whatever the manifest says."""

    for _name, directory in TEXT_CONFIGS:
        cv.refuse_when(
            not _held_out_digest_ok(freeze, files, directory), cv.FINDING_EXPORT_INTEGRITY,
            f"held-out freeze digest for {directory} is missing or differs from the export bytes",
        )


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


def _row_count(payload: bytes) -> int:
    return payload.count(b"\n")


def _viewer_rows(evidence: bytes) -> list[ViewerRow]:
    try:
        text = evidence.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise cv.RepairRefusal(cv.FINDING_EXPORT_INTEGRITY, "evidence is not UTF-8") from exc
    lines = text.split("\n")
    cv.refuse_when(lines[-1] != "", cv.FINDING_EXPORT_INTEGRITY,
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
                  sizes: dict[str, int], viewer: tuple[int, int]) -> list[dict]:
    viewer_rows, viewer_bytes = viewer
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


def _provenance(facts: BundleFacts) -> dict[str, Any]:
    manifest, run_meta, catalog, ready = (
        facts.manifest, facts.run_meta, facts.catalog, facts.ready
    )
    generator = run_meta.get("generator")
    generator = generator if isinstance(generator, dict) else {}
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
                       f"{catalog.get('catalog_id')}, seed {run_meta.get('seed')}, "
                       f"count {run_meta.get('count')}; export "
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

    bundled = {
        _data_path(directory, split): files[f"{directory}/{split}.jsonl"]
        for _name, directory in TEXT_CONFIGS for split in lineage.SPLITS
    }
    bundled.update({
        f"{DATA_DIR}/{export.AGOGE_PATH}": files[export.AGOGE_PATH],
        f"{EVIDENCE_DIR}/{VIEWER_SOURCE_FILE}": files[export.EVIDENCE_PATH],
        f"{EVIDENCE_DIR}/{Path(export.FREEZE_PATH).name}": files[export.FREEZE_PATH],
        f"{EVIDENCE_DIR}/{export.MANIFEST_FILENAME}": manifest_bytes,
    })
    bundled.update({name: files[name] for name in NOTICE_FILES if name in files})
    return bundled


def _load_export(export_dir: Path) -> tuple[bytes, dict[str, Any], dict[str, bytes], dict]:
    """Manifest bytes, verified file bytes, and a freeze whose digests match those bytes."""

    manifest_bytes = (export_dir / export.MANIFEST_FILENAME).read_bytes()
    manifest = _load_manifest(manifest_bytes)
    files = _verified_files(export_dir, manifest)
    freeze = load_strict_json(files[export.FREEZE_PATH])
    cv.refuse_when(not isinstance(freeze, dict), cv.FINDING_BUNDLE_MANIFEST_INVALID,
                   "the held-out freeze is not an object")
    _check_held_out_freeze(freeze, files)
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
        info=_dataset_info(configs, counts, sizes, (viewer_rows, len(viewer_bytes))),
        digests={path: _sha(payload) for path, payload in bundled.items()},
        record_counts=_record_counts(files, counts, viewer_rows),
    )
    return bundled, facts


def _companions(facts: BundleFacts) -> dict[str, bytes]:
    card = front_matter(facts) + "\n" + render_card(facts)
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
