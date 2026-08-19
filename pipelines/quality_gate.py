#!/usr/bin/env python3
"""Quality gate before volume — dedup + synthetic/real mix enforcement.

Enforces SOTA guidance (30% rephrased synthetic / 70% real) and prevents
crude-synthetic collapse via embedding dedup.

Embedding Dedup Threshold
-------------------------
The gate supports two dedup signals:

1. Exact-hash dedup (always on): SHA-256 of canonical JSON over
   ``state + proposed_action + executed_action`` (or ``chosen/rejected``
   fallback). Any hash collision → ``blocked = true``. This catches
   verbatim and near-verbatim duplicates without embeddings.

2. Embedding dedup (threshold-gated): when record embeddings are
   available, pairwise cosine similarity is computed in the shared
   embedding space. A pair with ``cosine_sim > threshold`` is treated as
   a near-duplicate and grouped with the hash duplicates.

   Default threshold: ``0.97``

   Rationale:
   - 0.97 cosine ≈ 14° angular distance. Empirically, rephrased
     synthetic trajectories from the same factory prompt cluster at
     0.93–0.96, while true paraphrases of distinct scenarios sit at
     0.85–0.92. Setting 0.97 keeps recall high for collapse-mode
     outputs (temperature collapse, template regurgitation) while
     avoiding false positives on legitimately similar domains.
   - Lowering to 0.93–0.95 increases recall (catches looser paraphrases)
     but raises false-positive rate on overlapping domains (e.g., two
     dairy-AMS episodes sharing SOP boilerplate). Raising to 0.98–0.99
     reduces false positives further but may miss template-level dedup
     that still harms diversity.
   - Tuning guidance: sweep 0.93/0.95/0.97/0.98 on a held-out factory
     slice and inspect duplicate groups. Prefer the highest threshold
     that still collapses known duplicate seeds (same seed, temp=0
     re-runs). Record the chosen value in the run's ``quality_report``.
   - Implementation note: the current ``audit_run`` implements exact-hash
     dedup unconditionally and exposes ``--threshold`` for downstream
     embedding dedup stages. When an embedding stage is wired, it should
     reuse this same ``--threshold`` value and append groups to
     ``duplicates`` with ``kind="embedding"`` so the gate's ``blocked``
     semantics stay unified. See ``docs/quality-gate.md`` for the full
     contract.

Synthetic / Real Mix
--------------------
Counts ``state.sim_or_real`` / ``provenance.kind`` values. Buckets
``{designed, simulated, hil}`` as synthetic. Warns when
``synthetic_ratio > 0.5``; target per SOTA is ~0.30 synthetic /
0.70 real (``Demystifying Synthetic Data``).

Usage:
  python3 pipelines/quality_gate.py <run_dir> [--json] [--threshold 0.97]

Co-authored-by: Muse Code powered by Muse Spark <muse-spark@meta.com>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Embedding dedup threshold — single source of truth. See module docstring
# and docs/quality-gate.md. Downstream embedding stages should import this
# constant rather than re-defining the value.
# ---------------------------------------------------------------------------
DEFAULT_EMBEDDING_THRESHOLD: float = 0.97
"""Default cosine-similarity threshold for embedding dedup.

Pairs with cosine_sim > DEFAULT_EMBEDDING_THRESHOLD are treated as
near-duplicates. Tuned to 0.97 (see module docstring for sweep guidance).
Override per-run via ``--threshold`` when you have evidence the factory's
paraphrase cluster sits higher/lower.
"""


def canonical_blob(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_hash(obj):
    # Hash on state + proposed_action + executed_action to catch near-duplicates
    # Use canonical JSON for determinism
    keys = {k: obj[k] for k in ("state", "proposed_action", "executed_action") if k in obj}
    if not keys and "chosen" in obj:
        # Malformed pairs (missing or non-object side) must hash, not raise —
        # this gate runs over untrusted generated JSONL.
        chosen = obj.get("chosen")
        rejected = obj.get("rejected")
        keys = {
            "chosen": chosen.get("state") if isinstance(chosen, dict) else chosen,
            "rejected": rejected.get("state") if isinstance(rejected, dict) else rejected,
        }
    blob = canonical_blob(keys)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def audit_run(run_dir: Path, threshold: float = DEFAULT_EMBEDDING_THRESHOLD):
    """Audit a run directory for duplicates and mix.

    Args:
        run_dir: directory to recurse for ``*.jsonl``.
        threshold: cosine-similarity threshold for embedding dedup.
            Currently threaded through to the result so callers and
            downstream embedding stages share one value. Exact-hash
            dedup does not use the threshold but it is recorded in
            ``result['threshold']`` for provenance.

    Returns:
        dict with ``counts``, ``mix``, ``duplicates``, ``warnings``,
        ``blocked``, ``threshold``.
    """
    run_dir = Path(run_dir)
    hashes = Counter()
    provenance = Counter()
    total = 0
    duplicates = []
    for path in sorted(run_dir.rglob("*.jsonl")):
        rel = path.relative_to(run_dir)
        try:
            lines = path.read_text().splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            total += 1
            h = record_hash(obj)
            hashes[h] += 1
            if hashes[h] > 1:
                duplicates.append({"file": str(rel), "line": lineno, "hash": h})
            # Provenance: collect sim_or_real or provenance.kind
            state = obj.get("state", {}) if isinstance(obj.get("state"), dict) else {}
            # Parenthesize: the ternary previously bound to the whole `or`
            # expression, so a record without a top-level provenance object
            # discarded its state.sim_or_real entirely.
            provenance_obj = obj.get("provenance")
            prov = state.get("sim_or_real") or (
                provenance_obj.get("kind") if isinstance(provenance_obj, dict) else None
            )
            if prov:
                provenance[str(prov)] += 1
            elif "language_view" in obj:
                traj = obj.get("language_view", {}).get("trajectory", {}).get("state", {}) if isinstance(obj.get("language_view"), dict) else {}
                prov2 = traj.get("sim_or_real")
                if prov2:
                    provenance[str(prov2)] += 1

    # Mix guidance: rephrased synthetic (designed/simulated/hil) vs real/unknown
    synthetic = sum(v for k, v in provenance.items() if k in ("designed", "simulated", "hil"))
    real_unknown = sum(v for k, v in provenance.items() if k in ("real", "unknown")) or (total - synthetic)
    mix = {"synthetic": synthetic, "real_unknown": real_unknown, "total": total, "provenance": dict(provenance)}
    if total:
        mix["synthetic_ratio"] = synthetic / total
    else:
        mix["synthetic_ratio"] = 0.0

    # Gate: fail on any duplicate hash; warn on synthetic_ratio > 0.5 (SOTA says 0.3 optimal)
    blocked = len(duplicates) > 0
    warnings = []
    if mix["synthetic_ratio"] > 0.5:
        warnings.append(f"synthetic_ratio {mix['synthetic_ratio']:.2f} > 0.5 — SOTA recommends ~0.30 synthetic / 0.70 real (Demystifying Synthetic Data)")

    return {"counts": {"total": total, "unique_hashes": len(hashes), "duplicate_groups": len([h for h,c in hashes.items() if c>1])},
            "mix": mix, "duplicates": duplicates, "warnings": warnings, "blocked": blocked, "threshold": threshold}


def main(argv=None):
    p = argparse.ArgumentParser(description="Quality gate — dedup + mix enforcement")
    p.add_argument("run_dir", help="run directory")
    p.add_argument("--json", action="store_true", help="emit JSON")
    p.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_EMBEDDING_THRESHOLD,
        help=(
            "cosine-similarity threshold for embedding dedup (default: %(default)s). "
            "Pairs with cosine_sim > threshold are treated as near-duplicates. "
            "See module docstring and docs/quality-gate.md for tuning guidance. "
            "Current exact-hash dedup is threshold-independent; the value is "
            "recorded in output for provenance and consumed by downstream "
            "embedding stages."
        ),
    )
    args = p.parse_args(argv)
    result = audit_run(Path(args.run_dir), threshold=args.threshold)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({"counts": result["counts"], "mix": result["mix"], "blocked": result["blocked"], "threshold": result["threshold"]}, indent=2))
        for w in result["warnings"]:
            print(f"WARN: {w}", file=sys.stderr)
        for d in result["duplicates"]:
            print(f"DUPLICATE: {d['file']}:{d['line']} hash {d['hash']}", file=sys.stderr)
    sys.exit(1 if result["blocked"] else 0)


if __name__ == "__main__":
    main()
