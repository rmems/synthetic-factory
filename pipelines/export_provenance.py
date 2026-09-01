#!/usr/bin/env python3
"""Build the final provenance document for one curated export."""

from __future__ import annotations

import sys
from typing import Any, Mapping

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("export_provenance", allow_initializing=True):
        import export_provenance as _direct_export_provenance

        _require_local_sibling(_direct_export_provenance, "export_provenance")
        del _direct_export_provenance
    from .export_contract import (
        EVAL_PATH,
        EXPORT_NAME,
        EXPORT_VERSION,
        PROTOCOL_PATH,
        SPLIT_POLICY,
        TRAIN_PATH,
        VIEWER_COLUMNS,
        VIEWER_PATH,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_provenance"
    )
    from export_contract import (
        EVAL_PATH,
        EXPORT_NAME,
        EXPORT_VERSION,
        PROTOCOL_PATH,
        SPLIT_POLICY,
        TRAIN_PATH,
        VIEWER_COLUMNS,
        VIEWER_PATH,
    )


def build_export_provenance(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Return provenance separately from the write transaction control flow."""
    options = inputs["options"]
    written = inputs["written"]
    return {
        "document_type": "curated_export_provenance",
        "export_name": EXPORT_NAME,
        "export_version": EXPORT_VERSION,
        "dataset_name": options["dataset_name"],
        "curated_root": str(inputs["resolved_root"]),
        "compose": inputs["compose_metadata"],
        "records": len(inputs["rows"]),
        "training_ready": inputs["audit"]["training_ready"],
        "audit": inputs["audit"],
        "payload_published": False,
        "trainer_launched": False,
        "files": written["files"],
        "viewer": {
            "path": VIEWER_PATH,
            "rows": len(inputs["rows"]),
            "columns": list(VIEWER_COLUMNS),
            "encoding": "PLAIN/uncompressed",
            "sha256": written["viewer_digest"],
            "lossless": True,
        },
        "splits": {
            "policy": SPLIT_POLICY,
            "scope": "post_curation_snapshot_future_trainer_holdout",
            "eval_fraction": options["eval_fraction"],
            "salt": options["split_salt"],
            "train": {
                "path": TRAIN_PATH,
                "records": len(written["train"]),
                "sha256": written["train_digest"],
            },
            "eval": {
                "path": EVAL_PATH,
                "records": len(written["evaluate"]),
                "sha256": written["eval_digest"],
            },
            "train_records": len(written["train"]),
            "eval_records": len(written["evaluate"]),
            "protocol": PROTOCOL_PATH,
        },
    }


if __package__:
    _expose_package_sibling(__name__)
