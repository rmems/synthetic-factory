#!/usr/bin/env python3
"""Quality gate before volume: exact/semantic dedup and mix enforcement.

The implementation is split by responsibility while this module remains the
stable import facade and CLI. Exact identity lives in
``quality_gate_identity``, lexical embedding and LSH nomination live in
``quality_gate_embedding``, and run scanning/reporting live in
``quality_gate_audit``.

The deterministic encoder blocks pairs whose exact TF-IDF cosine is strictly
above the configured threshold. Candidate generation is approximate, but its
accepted threshold range is bounded by the LSH recall design and every
nominated pair is scored exactly. The synthetic/real policy is independently
blocking, with a default target of 30 percent synthetic and 20 points of
slack.

Usage:
  python3 pipelines/quality_gate.py RUN_DIR [--json] [--threshold 0.97]
      [--mix-target 0.30] [--mix-tolerance 0.20] [--manifest PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from quality_gate_identity import (  # noqa: E402
    _CANONICAL_ID_KEYS,
    _IDENTITY_FIELDS,
    _PREFERENCE_WRAPPER_FIELDS,
    _SEMANTIC_BOOKKEEPING_PARENTS,
    _SEMANTIC_PROMOTION_BOOKKEEPING_KEYS,
    _SEMANTIC_ROOT_BOOKKEEPING_KEYS,
    _preference_identity_side,
    _without_canonical_ids,
    canonical_blob,
    dedup_view,
    exact_identity_view,
    record_hash,
    semantic_similarity_view,
)
from quality_gate_embedding import (  # noqa: E402
    DEFAULT_EMBEDDING_THRESHOLD,
    DEFAULT_MAX_EMBEDDING_PAIRS,
    EMBEDDING_CANDIDATE_SKETCH,
    EMBEDDING_ENCODER,
    EMBEDDING_LSH_BANDS,
    EMBEDDING_MINHASH_SLOTS,
    EMBEDDING_MIN_THRESHOLD,
    EMBEDDING_SKETCH_LEVELS,
    _BIGRAM_SEP,
    _GAP_SEP,
    _ORDER_MARK,
    _PATH_SEP,
    _SKETCH_SEP,
    _Union,
    _candidate_pairs,
    _cosine,
    _element_digest,
    _embedding_duplicates,
    _graphemes,
    _leaf_words,
    _minhash_signature,
    _path_child,
    _string_units,
    _tfidf_vector,
    _uses_unsegmented_script,
    _where,
    candidate_sketch_features,
    embedding_tokens,
    validate_embedding_threshold,
)
from quality_gate_audit import (  # noqa: E402
    DEFAULT_MIX_TOLERANCE,
    DEFAULT_TARGET_SYNTHETIC_RATIO,
    MAX_ERROR_EXAMPLES,
    REAL_KINDS,
    SYNTHETIC_KINDS,
    AuditOptions,
    MixPolicy,
    _owner_provenance_kind,
    _record_provenance_kind,
    _state_provenance_kind,
    audit_run,
    validate_manifest_target,
    write_manifest,
)


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Quality gate — dedup + mix enforcement"
    )
    parser.add_argument("run_dir", help="run directory")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_EMBEDDING_THRESHOLD,
        help=(
            "cosine threshold for near-duplicate exclusion in "
            f"[{EMBEDDING_MIN_THRESHOLD:.4f}, 1) (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--no-embedding-dedup",
        dest="embedding_dedup",
        action="store_false",
        help="skip embedding dedup (exact-hash dedup still runs)",
    )
    parser.add_argument(
        "--max-embedding-pairs",
        type=int,
        default=DEFAULT_MAX_EMBEDDING_PAIRS,
        help=(
            "blocking cap on LSH candidate pairs; observing an omitted pair "
            "fails closed (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--mix-target",
        type=float,
        default=DEFAULT_TARGET_SYNTHETIC_RATIO,
        help="target synthetic share (default: %(default)s, i.e. roughly 30/70)",
    )
    parser.add_argument(
        "--mix-tolerance",
        type=float,
        default=DEFAULT_MIX_TOLERANCE,
        help="slack above the target before the gate blocks (default: %(default)s)",
    )
    parser.add_argument(
        "--max-synthetic-ratio",
        type=float,
        default=None,
        help="explicit blocking ceiling; overrides target plus tolerance",
    )
    parser.add_argument(
        "--min-synthetic-ratio",
        type=float,
        default=None,
        help="optional blocking floor on the synthetic share",
    )
    parser.add_argument(
        "--max-unlabeled-ratio",
        type=float,
        default=None,
        help="optional blocking ceiling for unrecognized provenance",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="write the curated sidecar manifest to this path",
    )
    return parser


def _policy_from_args(args):
    return MixPolicy(
        target=args.mix_target,
        tolerance=args.mix_tolerance,
        max_synthetic_ratio=args.max_synthetic_ratio,
        min_synthetic_ratio=args.min_synthetic_ratio,
        max_unlabeled_ratio=args.max_unlabeled_ratio,
    )


def _run_from_args(args):
    run_dir = Path(args.run_dir)
    if args.manifest:
        validate_manifest_target(args.manifest, run_dir)
    result = audit_run(
        run_dir,
        threshold=args.threshold,
        mix_policy=_policy_from_args(args),
        embedding_dedup=args.embedding_dedup,
        max_embedding_pairs=args.max_embedding_pairs,
    )
    written = None
    if args.manifest:
        written = write_manifest(args.manifest, run_dir, result)
    return result, written


def _summary(result):
    return {
        "counts": result["counts"],
        "mix": result["mix"],
        "mix_policy": result["mix_policy"],
        "embedding": result["embedding"],
        "reward_shapes": {
            key: value
            for key, value in result["reward_shapes"].items()
            if not key.startswith("top_")
        },
        "blocked": result["blocked"],
        "threshold": result["threshold"],
    }


def _emit_diagnostics(result):
    for blocker in result["blockers"]:
        print(f"BLOCKED: {blocker}", file=sys.stderr)
    for warning in result["warnings"]:
        print(f"WARN: {warning}", file=sys.stderr)
    for duplicate in result["duplicates"]:
        print(
            f"DUPLICATE: {duplicate['file']}:{duplicate['line']} "
            f"({duplicate['reason']})",
            file=sys.stderr,
        )
    for error in result["errors"]["unreadable_examples"]:
        print(f"UNREADABLE: {error['file']} ({error['error']})", file=sys.stderr)
    for error in result["errors"]["malformed_examples"]:
        print(
            f"MALFORMED: {error['file']}:{error['line']} ({error['error']})",
            file=sys.stderr,
        )


def _emit_output(args, result, written):
    if written is not None:
        print(f"MANIFEST: {written}", file=sys.stderr)
    payload = result if args.json else _summary(result)
    print(json.dumps(payload, indent=2))
    if not args.json:
        _emit_diagnostics(result)


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result, written = _run_from_args(args)
    except ValueError as exc:
        parser.error(str(exc))
    _emit_output(args, result, written)
    sys.exit(1 if result["blocked"] else 0)


if __name__ == "__main__":
    main()
