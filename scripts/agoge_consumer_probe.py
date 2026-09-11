#!/usr/bin/env python3
"""Consumer proof using Agoge normalization, frozen splits, and current completion masking.

With --config, a locally cached pinned tokenizer and the real TRL collator measure
both loss modes from explicit Unicode completion boundaries without truncation.
No training is launched. --freeze-into writes a new snapshot and requires real
producer commit and dataset-version provenance.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import sys
from pathlib import Path

GAPS = {
    "PROMPT_COMPLETION_UNSUPPORTED_RENDERED_TO_TEXT": (
        "Agoge's normalize_row rejects {prompt, completion}; the factory renders one text"
    ),
    "NO_LOSS_MASKING_PROMPT_TOKENS_TRAINED": (
        "Agoge feeds a single text column to TRL, so completion_only_loss resolves False"
    ),
    "CONFIG_REVISION_PIN_REQUIRED_40_HEX": (
        "producer_provenance_from_config needs config.revision pinned"
    ),
    "CONFIG_HAS_NO_SPLIT_FIELD_DATASET_PATH_MUST_BE_SPLITS_TRAIN": (
        "ExperimentConfig has no split field; dataset_path must be <snapshot>/splits/train.jsonl"
    ),
    "EVAL_IDENTIFIES_HELD_OUT_BY_CANONICAL_ID_ONLY": (
        "the eval contract carries no reference field"
    ),
}
SEPARATOR = "\n\n### Corrected module: program.py\n"
SOURCE_PATH = "datasets/curated/code_repair_v1.jsonl"
PINNED_REVISION = re.compile(r"^[0-9a-f]{40}$")


def _rows(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _load_proof(path: Path, source_path: str) -> dict:
    from agoge_forger.datasets import iter_normalized_rows
    from agoge_forger.split_materialize import iter_source_records
    from agoge_forger.split_schema import CanonicalIdentityPolicy
    from agoge_forger.train.preflight import validate_dataset_text_field_in_source

    normalized = list(iter_normalized_rows(str(path)))
    validate_dataset_text_field_in_source(str(path), "text")
    identity = CanonicalIdentityPolicy(content_hash_policy="normalized-training-payload-v1")
    records = list(iter_source_records(
        path, identity, source_coordinate_path=source_path, require_declared_lineage=True,
    ))
    return {
        "normalized_rows": len(normalized), "frozen_split_records": len(records),
        "records": records,
    }


def _spec(policy: dict, source_path: str, source_revision='0' * 40, dataset_version='probe'):
    """The materialization spec Agoge would pin for this export (revision is a placeholder)."""

    from agoge_forger.split_schema import SplitMaterializationSpec, SplitPolicy

    return SplitMaterializationSpec(
        source_repository="rmems/synthetic-factory", source_revision=source_revision,
        dataset_version=dataset_version, source_path=source_path,
        split_policy=SplitPolicy(
            seed=policy["seed"], salt=policy["salt"], weights=policy["weights"]
        ),
    )


def _split_agreement(records: list, rows: list[dict], spec) -> dict:
    from agoge_forger.split_materialize import assign_records

    assigned = assign_records(records, spec)
    agoge = {
        records[i].member.canonical_id: split
        for split, indexes in assigned.items() for i in indexes
    }
    factory = {row["canonical_id"]: row["split"] for row in rows}
    disagree = sorted(k for k in factory if agoge.get(k) != factory[k])
    return {
        "agree": not disagree, "disagree": disagree,
        "agoge_counts": {s: len(v) for s, v in assigned.items()},
    }


def _config(path: Path | None, tokenizer_revision: str | None) -> dict:
    """The model, its pinned revision (config or command line) and the sequence budget."""

    if path is None:
        return {}
    from agoge_forger.config import load_config

    config = load_config(str(path))
    revision = tokenizer_revision or config.revision
    return {"model_id": config.model_id, "revision": revision,
            "max_seq_length": config.training.max_seq_length,
            "completion_only_loss": config.training.completion_only_loss}


def _label_report(rows: list[dict], config: dict) -> dict:
    """Real tokenization and TRL collator labels in both modes, per row."""

    model_id, max_length = config["model_id"], config["max_seq_length"]
    revision = config["revision"]
    if not isinstance(revision, str) or not PINNED_REVISION.match(revision):
        raise ValueError("CONFIG_REVISION_PIN_REQUIRED_40_HEX: pass --tokenizer-revision")

    from transformers import AutoTokenizer
    from trl.trainer.sft_trainer import DataCollatorForLanguageModeling

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, local_files_only=True)
    pad = tokenizer.pad_token_id
    pad = tokenizer.eos_token_id if pad is None else pad
    collators = {
        "full_sequence": DataCollatorForLanguageModeling(
            pad_token_id=pad, completion_only_loss=False
        ),
        "completion_only": DataCollatorForLanguageModeling(
            pad_token_id=pad, completion_only_loss=True
        ),
    }
    per_row = [_row_labels(tokenizer, collators, max_length, row) for row in rows]
    return {
        "tokenizer": model_id, "max_seq_length": max_length, "rows": per_row,
        "completion_truncated_rows": sum(1 for r in per_row if r["completion_truncated"]),
        "loss_mode_in_agoge": "completion_only" if config["completion_only_loss"] else "full_sequence",
    }


def _valid_boundary_offset(text, start) -> bool:
    if not isinstance(text, str):
        return False
    # Exact int rejects bool and subclasses as completion offsets.
    if type(start) is not int:  # pylint: disable=unidiomatic-typecheck
        return False
    return start in range(1, len(text))


def _delimits_completion(text: str, start: int) -> bool:
    if not text[start:].strip():
        return False
    return text[:start].endswith(SEPARATOR)


def completion_boundary(row: dict) -> int:
    """Validate the producer's explicit Unicode offset, without searching prompt contents."""
    text, start = row.get("text"), row.get("completion_start_char")
    if not _valid_boundary_offset(text, start):
        raise ValueError("invalid completion_start_char")
    if not _delimits_completion(text, start):
        raise ValueError("boundary does not delimit a nonempty corrected module")
    return start


def _row_labels(tokenizer, collators: dict, max_length: int, row: dict) -> dict:
    """Use the current trainer's preprocessing and real collator on exact frozen text."""
    from agoge_forger.train.completion import completion_tokens
    completion_boundary(row)
    prepared = completion_tokens(row, tokenizer, max_length)
    mask = prepared["completion_mask"]
    labels = {}
    for mode, collator in collators.items():
        sample = dict(prepared)
        if mode == "full_sequence":
            sample["labels"] = list(prepared["input_ids"])
        labels[mode] = collator([sample])["labels"][0]
    prompt = sum(active == 0 for active in mask)
    completion = sum(mask)
    return {
        "canonical_id": row["canonical_id"], "prompt_tokens": prompt,
        "completion_tokens": completion, "total_tokens": len(mask),
        "completion_tokens_surviving_truncation": completion, "completion_truncated": False,
        "loss_tokens_full_sequence": int((labels["full_sequence"] != -100).sum()),
        "loss_tokens_completion_only": int((labels["completion_only"] != -100).sum()),
        "prompt_tokens_receiving_loss_full_sequence": sum(
            int(labels["full_sequence"][i] != -100) for i, active in enumerate(mask) if not active),
        "prompt_tokens_receiving_loss_completion_only": sum(
            int(labels["completion_only"][i] != -100) for i, active in enumerate(mask) if not active),
    }


def _freeze(path: Path, into: Path, spec) -> dict:
    """The one write: Agoge's own materialize_split into a brand-new scratch directory."""

    from agoge_forger.split_materialize import materialize_split

    manifest = materialize_split(path, into, spec)
    return {"output_dir": str(into), "manifest_type": type(manifest).__name__}


def _guarded(step, *args) -> tuple[dict, list]:
    """Run one consumer step; Agoge's refusal is reported, never raised."""

    try:
        report = step(*args)
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}", "agree": False}, []
    visible = {key: value for key, value in report.items() if key != "records"}
    return visible, report.get("records", [])


def _manifest_proof(path: Path, manifest: dict, count: int) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != manifest["files"]["agoge/code_repair_v1.jsonl"]:
        raise ValueError("input sha256 differs from manifest")
    if count != manifest["tables"]["dispositions"].get("exported", 0):
        raise ValueError("input row count differs from manifest")
    for row in _rows(path):
        completion_boundary(row)
    return {"sha256": digest, "rows": count}


def _labels(rows: list[dict], args: argparse.Namespace) -> dict:
    config = _config(args.config, args.tokenizer_revision)
    return {**_label_report(rows, config), "config": config}


def _freeze_ready(args: argparse.Namespace) -> bool:
    revision = args.source_revision
    if not revision:
        return False
    if not PINNED_REVISION.fullmatch(revision):
        return False
    if revision == '0' * 40:
        return False
    if not args.dataset_version:
        return False
    return args.dataset_version != 'probe'


def _freeze_step(report: dict, args: argparse.Namespace, spec) -> None:
    if args.freeze_into is None:
        return
    if not _freeze_ready(args):
        report['freeze'] = {
            'error': 'freeze requires real --source-revision and --dataset-version',
        }
        return
    report["freeze"] = _guarded(_freeze, args.agoge_jsonl, args.freeze_into, spec)[0]


def _split_steps(report: dict, records: list, rows: list, args: argparse.Namespace) -> None:
    policy = report.pop("policy")
    if policy is None:
        report["split_agreement"] = {"status": "not evaluated: no split policy"}
        if args.freeze_into is not None:
            report["freeze"] = {"error": "no split policy"}
        return
    spec_report, _unused = _guarded(_make_spec, policy, args.source_path,
                                  args.source_revision or '0' * 40, args.dataset_version or 'probe')
    if "error" in spec_report:
        report["split_agreement"] = spec_report
        return
    spec = spec_report["spec"]
    report["split_agreement"] = _guarded(_split_agreement, records, rows, spec)[0]
    _freeze_step(report, args, spec)


def _make_spec(policy: dict, source_path: str, source_revision, dataset_version) -> dict:
    return {"spec": _spec(policy, source_path, source_revision, dataset_version)}


def _failed_steps(report: dict, args: argparse.Namespace) -> list[str]:
    required = ["manifest", "load", "split_agreement"]
    if args.config is not None:
        required.append("labels")
    if args.freeze_into is not None:
        required.append("freeze")
    failed = [name for name in required if "error" in report.get(name, {"error": "not run"})]
    if report.get("split_agreement", {}).get("agree") is False:
        failed.append("split_agreement")
    return sorted(set(failed))


def _report(args: argparse.Namespace) -> dict:
    rows = _rows(args.agoge_jsonl)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report: dict = {"rows": len(rows), "gaps": {k: v for k, v in GAPS.items() if k != "NO_LOSS_MASKING_PROMPT_TOKENS_TRAINED"}}
    report["manifest"] = _guarded(_manifest_proof, args.agoge_jsonl, manifest, len(rows))[0]
    if "error" in report["manifest"]:
        return {**report, "passed": False, "failed_steps": ["manifest"]}
    report["load"], records = _guarded(_load_proof, args.agoge_jsonl, args.source_path)
    report["policy"] = manifest["run"].get("split_policy")
    _split_steps(report, records, rows, args)
    if args.config is not None:
        report["labels"] = _guarded(_labels, rows, args)[0]
        report["config"] = report["labels"].pop("config", {})
    report["failed_steps"] = _failed_steps(report, args)
    report["passed"] = not report["failed_steps"]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agoge_jsonl", type=Path)
    parser.add_argument(
        "--manifest", type=Path, required=True, help="the export's MANIFEST.json"
    )
    parser.add_argument("--source-path", default=SOURCE_PATH)
    parser.add_argument("--config", type=Path, default=None, help="an Agoge experiment YAML")
    parser.add_argument(
        "--tokenizer-revision", default=None,
        help="the model revision to tokenize with (40 hex) when the config pins none",
    )
    parser.add_argument("--freeze-into", type=Path, default=None)
    parser.add_argument('--source-revision', default=None)
    parser.add_argument('--dataset-version', default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    with contextlib.redirect_stdout(sys.stderr):  # Agoge and the Hub client log to stdout
        report = _report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"passed={report['passed']} rows={report['rows']} "
              f"failed_steps={','.join(report['failed_steps']) or 'none'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
