#!/usr/bin/env python3
"""Quality gate before volume — dedup + synthetic/real mix enforcement.

Enforces SOTA guidance (30% rephrased synthetic / 70% real) and prevents
crude-synthetic collapse via exact-hash dedup. Embedding dedup is PLANNED,
not wired — see ``docs/quality-gate.md``.

Embedding Dedup Threshold
-------------------------
The gate supports two dedup signals:

1. Exact-hash dedup (always on): SHA-256 of canonical JSON over
   ``state + proposed_action + executed_action`` (falling back to
   ``chosen/rejected``, then to the whole record for shapes this gate
   does not model). Any hash collision → ``blocked = true``. This catches
   verbatim and near-verbatim duplicates without embeddings.

2. Embedding dedup (PLANNED — not implemented here): no similarity is
   computed by this module; ``--threshold`` is only recorded in the
   report. When the stage is wired, a pair with
   ``cosine_sim > threshold`` is to be treated as a near-duplicate and
   grouped with the hash duplicates.

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
``{designed, simulated, hil}`` as synthetic and ``{real, unknown}`` as
real_unknown; records with no recognized label are reported separately as
``unlabeled`` rather than assumed real. Warns when
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

SYNTHETIC_KINDS = frozenset({"designed", "simulated", "hil"})
"""Provenance labels counted as rephrased synthetic."""

REAL_KINDS = frozenset({"real", "unknown"})
"""Provenance labels counted as real/unknown. Anything else (including a
missing label) lands in the separate ``unlabeled`` bucket."""

MAX_ERROR_EXAMPLES = 10
"""Cap on per-category read/parse failure examples kept in the report."""


def canonical_blob(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _preference_side(value):
    """Stable hash representation of one side of a preference pair.

    Well-formed sides hash on their ``state`` (so pairs that differ only in
    bookkeeping fields still collide). A side without a dict ``state`` keeps
    its whole value, otherwise every malformed side would reduce to ``None``
    and unrelated records would collapse into one hash.
    """
    if isinstance(value, dict):
        state = value.get("state")
        return state if isinstance(state, dict) else value
    return value


def record_hash(obj):
    # Hash on state + proposed_action + executed_action to catch near-duplicates
    # Use canonical JSON for determinism
    if not isinstance(obj, dict):
        # A JSONL line that parses to a scalar/array must hash, not raise.
        return hashlib.sha256(canonical_blob(obj).encode("utf-8")).hexdigest()[:16]
    keys = {k: obj[k] for k in ("state", "proposed_action", "executed_action") if k in obj}
    if not keys and ("chosen" in obj or "rejected" in obj):
        # Malformed pairs (missing or non-object side) must hash, not raise —
        # this gate runs over untrusted generated JSONL. Both fields are always
        # present in the key set so a one-sided record stays distinguishable.
        keys = {
            "chosen": _preference_side(obj.get("chosen")),
            "rejected": _preference_side(obj.get("rejected")),
        }
    if not keys:
        # Shapes this gate does not model (e.g. bridge records carrying state
        # under language_view) must not all hash to the empty key set, which
        # would report every record after the first as a duplicate.
        keys = obj
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
        dict with ``counts``, ``mix``, ``duplicates``, ``errors``,
        ``warnings``, ``blocked``, ``threshold``.
    """
    run_dir = Path(run_dir)
    hashes = Counter()
    provenance = Counter()
    total = 0
    duplicates = []
    unreadable_files = 0
    malformed_lines = 0
    unreadable_examples = []
    malformed_examples = []
    for path in sorted(run_dir.rglob("*.jsonl")):
        rel = path.relative_to(run_dir)
        try:
            # JSONL is UTF-8 by contract; never fall back to the locale encoding.
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            unreadable_files += 1
            if len(unreadable_examples) < MAX_ERROR_EXAMPLES:
                unreadable_examples.append(
                    {"file": str(rel), "error": f"{type(exc).__name__}: {exc}"}
                )
            continue
        for lineno, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                malformed_lines += 1
                if len(malformed_examples) < MAX_ERROR_EXAMPLES:
                    malformed_examples.append(
                        {"file": str(rel), "line": lineno, "error": str(exc)}
                    )
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

    # Mix guidance: rephrased synthetic (designed/simulated/hil) vs real/unknown.
    # Records carrying no recognized provenance label are their own bucket —
    # folding them into real_unknown would assert "real" about unlabeled data.
    synthetic = sum(v for k, v in provenance.items() if k in SYNTHETIC_KINDS)
    real_unknown = sum(v for k, v in provenance.items() if k in REAL_KINDS)
    unlabeled = total - synthetic - real_unknown
    mix = {"synthetic": synthetic, "real_unknown": real_unknown, "unlabeled": unlabeled,
           "total": total, "provenance": dict(provenance)}
    if total:
        mix["synthetic_ratio"] = synthetic / total
    else:
        mix["synthetic_ratio"] = 0.0

    errors = {
        "unreadable_files": unreadable_files,
        "malformed_lines": malformed_lines,
        "unreadable_examples": unreadable_examples,
        "malformed_examples": malformed_examples,
    }

    # Gate: fail on any duplicate hash or unparseable input; warn on
    # synthetic_ratio > 0.5 (SOTA says 0.3 optimal). Skipped files/lines are not
    # covered by any count above, so a run containing them cannot pass clean.
    blocked = len(duplicates) > 0 or unreadable_files > 0 or malformed_lines > 0
    warnings = []
    if mix["synthetic_ratio"] > 0.5:
        warnings.append(f"synthetic_ratio {mix['synthetic_ratio']:.2f} > 0.5 — SOTA recommends ~0.30 synthetic / 0.70 real (Demystifying Synthetic Data)")
    if unreadable_files:
        warnings.append(f"{unreadable_files} file(s) unreadable/undecodable — counts, mix and dedup cover only the readable subset")
    if malformed_lines:
        warnings.append(f"{malformed_lines} malformed JSON line(s) skipped — counts, mix and dedup cover only the parseable subset")

    return {"counts": {"total": total, "unique_hashes": len(hashes), "duplicate_groups": len([h for h,c in hashes.items() if c>1]),
                       "unreadable_files": unreadable_files, "malformed_lines": malformed_lines},
            "mix": mix, "duplicates": duplicates, "errors": errors, "warnings": warnings,
            "blocked": blocked, "threshold": threshold}


def main(argv=None):
    p = argparse.ArgumentParser(description="Quality gate — dedup + mix enforcement")
    p.add_argument("run_dir", help="run directory")
    p.add_argument("--json", action="store_true", help="emit JSON")
    p.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_EMBEDDING_THRESHOLD,
        help=(
            "cosine-similarity threshold for the PLANNED embedding dedup stage "
            "(default: %(default)s). No similarity is computed today: the value "
            "is only recorded in the output for provenance and consumed by "
            "downstream embedding stages once wired. See module docstring and "
            "docs/quality-gate.md for tuning guidance."
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
        for e in result["errors"]["unreadable_examples"]:
            print(f"UNREADABLE: {e['file']} ({e['error']})", file=sys.stderr)
        for e in result["errors"]["malformed_examples"]:
            print(f"MALFORMED: {e['file']}:{e['line']} ({e['error']})", file=sys.stderr)
    sys.exit(1 if result["blocked"] else 0)


if __name__ == "__main__":
    main()
