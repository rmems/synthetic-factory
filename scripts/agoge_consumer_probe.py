#!/usr/bin/env python3
"""Consumer proof for the code-repair export, run with Agoge-Forger's own interpreter.

Read-only against Agoge (``/home/raulmc/rmems/agoge-forger/.venv/bin/python
scripts/agoge_consumer_probe.py <agoge.jsonl> ...``): every row is normalised
by ``datasets.normalize_row``, loaded under the frozen-split identity policy
with a declared lineage, and its recorded split compared with Agoge's own
``assign_records``. With ``--config`` (an Agoge experiment YAML) the rows are
tokenized with the configured model's tokenizer and pushed through TRL's SFT
collator twice: as Agoge's trainer does today (one ``text`` column, so every
token receives loss) and as a prompt/completion pair with completion-only
loss, so the report states how many corrected-code tokens receive loss in
each mode and which completions are cut by truncation. It launches no
training; ``--freeze-into`` materializes Agoge's frozen split into a scratch
directory as the one write. What it establishes: the export loads under
Agoge's current contract and the label behaviour of that contract today. What
it does not establish: that Agoge's training path is fixed (that is the
linked Agoge issue and its trainer-batch test).
"""

from __future__ import annotations

import argparse
import contextlib
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


def _spec(policy: dict, source_path: str):
    """The materialization spec Agoge would pin for this export (revision is a placeholder)."""

    from agoge_forger.split_schema import SplitMaterializationSpec, SplitPolicy

    return SplitMaterializationSpec(
        source_repository="rmems/synthetic-factory", source_revision="0" * 40,
        dataset_version="probe", source_path=source_path,
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
            "max_seq_length": config.training.max_seq_length}


def _label_report(rows: list[dict], config: dict) -> dict:
    """Real tokenization and TRL collator labels in both modes, per row."""

    model_id, max_length = config["model_id"], config["max_seq_length"]
    revision = config["revision"]
    if not isinstance(revision, str) or not PINNED_REVISION.match(revision):
        raise ValueError("CONFIG_REVISION_PIN_REQUIRED_40_HEX: pass --tokenizer-revision")

    from transformers import AutoTokenizer
    from trl.trainer.sft_trainer import DataCollatorForLanguageModeling

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
    pad = tokenizer.pad_token_id
    pad = tokenizer.eos_token_id if pad is None else pad
    collators = {
        "full_sequence": DataCollatorForLanguageModeling(
            pad_token_id=pad, max_length=max_length, completion_only_loss=False
        ),
        "completion_only": DataCollatorForLanguageModeling(
            pad_token_id=pad, max_length=max_length, completion_only_loss=True
        ),
    }
    per_row = [_row_labels(tokenizer, collators, max_length, row) for row in rows]
    return {
        "tokenizer": model_id, "max_seq_length": max_length, "rows": per_row,
        "completion_truncated_rows": sum(1 for r in per_row if r["completion_truncated"]),
        "loss_mode_in_agoge": "full_sequence",
    }


def _row_labels(tokenizer, collators: dict, max_length: int, row: dict) -> dict:
    """One row through both collators: how many prompt and completion tokens receive loss."""

    prompt, sep, completion = row["text"].partition(SEPARATOR)
    prompt_ids = tokenizer(prompt + sep, add_special_tokens=False)["input_ids"]
    completion_ids = tokenizer(completion, add_special_tokens=False)["input_ids"]
    ids = prompt_ids + completion_ids
    mask = [0] * len(prompt_ids) + [1] * len(completion_ids)
    labels = {
        mode: collator([{"input_ids": ids, "completion_mask": mask}])["labels"][0]
        for mode, collator in collators.items()
    }
    prompt_kept = min(len(prompt_ids), max_length)
    surviving = max(0, min(len(ids), max_length) - len(prompt_ids))
    return {
        "canonical_id": row["canonical_id"], "prompt_tokens": len(prompt_ids),
        "completion_tokens": len(completion_ids), "total_tokens": len(ids),
        "completion_tokens_surviving_truncation": surviving,
        "completion_truncated": surviving < len(completion_ids),
        "loss_tokens_full_sequence": int((labels["full_sequence"] != -100).sum()),
        "loss_tokens_completion_only": int((labels["completion_only"] != -100).sum()),
        "prompt_tokens_receiving_loss_full_sequence": int(
            (labels["full_sequence"][:prompt_kept] != -100).sum()
        ),
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
    except Exception as exc:  # noqa: BLE001 - the refusal text is the evidence
        return {"error": f"{type(exc).__name__}: {exc}", "agree": False}, []
    return report, report.pop("records", [])


def _report(args: argparse.Namespace) -> dict:
    rows = _rows(args.agoge_jsonl)
    policy = json.loads(args.manifest.read_text(encoding="utf-8"))["run"]["split_policy"]
    report: dict = {"rows": len(rows), "gaps": dict(GAPS)}
    spec = _spec(policy, args.source_path)
    report["load"], records = _guarded(_load_proof, args.agoge_jsonl, args.source_path)
    report["split_agreement"] = (
        _guarded(_split_agreement, records, rows, spec)[0] if records else {"agree": False}
    )
    config = _config(args.config, args.tokenizer_revision)
    if config:
        try:
            report["labels"] = _label_report(rows, config)
        except Exception as exc:  # noqa: BLE001 - reported as the gap it is
            report["labels"] = {"error": f"TOKENIZER_UNAVAILABLE: {type(exc).__name__}: {exc}"}
        report["config"] = config
    if args.freeze_into is not None:
        report["freeze"] = _guarded(_freeze, args.agoge_jsonl, args.freeze_into, spec)[0]
    report["pass"] = bool(report["load"].get("frozen_split_records")) and bool(
        report["split_agreement"].get("agree")
    )
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
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    with contextlib.redirect_stdout(sys.stderr):  # Agoge and the Hub client log to stdout
        report = _report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"pass={report['pass']} rows={report['rows']}")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
