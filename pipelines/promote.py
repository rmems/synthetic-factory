#!/usr/bin/env python3
"""Promote a raw factory run into cleaned JSONL.

Copies every *.jsonl under raw_run to the same relative path under
cleaned_out. Attaches provenance, remaps state.sim_or_real to
designed|simulated|hil|unknown, and sorts unsorted spike trains
(setting meta.spike_events_resorted). Writes reward-scale.json and
PROVENANCE.md. Never mutates raw_run.

Quality Gate — enforced by this CLI after promotion
----------------------------------------------------
Promotion is **not** a training-ready signal. After this script writes
``cleaned_out``, it invokes ``pipelines/quality_gate.py`` in-process, writes
``quality-manifest.json`` inside the cleaned tree by default, and exits 1
when the gate blocks:

    python3 pipelines/promote.py <raw_run> <cleaned_out>

Use ``--quality-manifest PATH`` to place the sidecar elsewhere. The gate's
threshold and mix-policy flags are accepted here too, so an explicit,
auditable policy can be pinned on the established promotion command.

Gate contract (see ``pipelines/quality_gate.py`` and
``docs/quality-gate.md``):

- **Exact-hash dedup**: SHA-256 over the canonical training-identity view —
  any hash collision sets ``blocked = true``.
- **Embedding dedup**: cosine similarity over a separate, identifier-free
  semantic view; pairs above ``--threshold`` (default 0.97)
  are clustered and every member but the first is excluded with a
  reason. See ``docs/quality-gate.md`` for the encoder and sweep
  guidance.
- **Mix enforcement** (blocking): ``synthetic_ratio`` above the policy
  ceiling (default ``--mix-target 0.30`` + ``--mix-tolerance 0.20`` =
  0.50) sets ``blocked = true``; between target and ceiling it warns.
  Target is ~0.30 synthetic (``designed``/``simulated``/``hil``) / 0.70
  real per SOTA guidance. Promoted records already carry normalized
  ``provenance.kind`` so the gate's mix bucketing is consistent.
- **Exit code**: gate exits 1 when ``blocked`` (duplicates, mix outside
  policy, or files/lines it could not read or parse) and 0 otherwise; CI
  should treat ``blocked`` as a hard fail and ``warnings`` as soft fails
  requiring review.

Usage: python3 pipelines/promote.py <raw_run> <cleaned_out> [gate options]

Co-authored-by: Muse Code powered by Muse Spark <muse-spark@meta.com>
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))
from check_records import check_spikes, event_time  # noqa: E402
import quality_gate  # noqa: E402

FFPC = "failure-as-fuel-preference-cascade"
ALLOWED_KINDS = frozenset({"designed", "simulated", "hil", "unknown"})
HIL_WORD = re.compile(r"\bhil\b", re.IGNORECASE)
DEFAULT_SCALE = {
    "aggregation": "unspecified",
    "native_unit": "unspecified",
    "usd_factor_or_null": None,
    "mix_policy": "sign_order_only",
}
PROVENANCE_MD = """# Cleaned provenance

This tree is a promotion of a raw factory run. **Raw JSONL is the source of truth (SoT)** and was not modified.

Cleaned `provenance.kind` is one of `designed` | `simulated` | `hil` | `unknown`. Cleaned records **never emit `real`** in `state.sim_or_real` or `provenance.kind`. The original claim is kept in `provenance.claimed`.

Invented plants and labels that start with `real`/`live` or mention production / actions live are `designed` stories, not live telemetry.

If a `spike_events` train was not globally time-ordered, the cleaned copy is sorted and `meta.spike_events_resorted` is true.
"""


def remap_claimed(claimed):
    """Map a claimed sim_or_real string to {kind, claimed}."""
    if claimed is None:
        return {"kind": "unknown", "claimed": None}
    if not isinstance(claimed, str):
        return {"kind": "unknown", "claimed": claimed}
    low = claimed.strip().lower()
    if not low:
        return {"kind": "unknown", "claimed": claimed}
    if (
        low.startswith("real")
        or low.startswith("live")
        or "actions live" in low
        or "production" in low
    ):
        return {"kind": "designed", "claimed": claimed}
    if "simulation" in low or "simulat" in low or "high-fidelity" in low:
        return {"kind": "simulated", "claimed": claimed}
    if "hardware-in-the-loop" in low or HIL_WORD.search(low) or low.startswith("hil"):
        return {"kind": "hil", "claimed": claimed}
    if low in ALLOWED_KINDS:
        return {"kind": low, "claimed": claimed}
    return {"kind": "unknown", "claimed": claimed}


def _factory_origin_provenance(owner):
    """Infer synthetic provenance from this factory's stateless envelope."""
    if not isinstance(owner, dict):
        return None
    meta = owner.get("meta")
    factory = meta.get("factory") if isinstance(meta, dict) else None
    if isinstance(factory, str) and factory.strip():
        return {
            "kind": "designed",
            "claimed": None,
            "inferred_from": "meta.factory",
        }
    return None


def _rejected_claim(existing):
    """Return the surviving claim from a provenance dict promotion rejects.

    PROVENANCE.md promises that the original claim is kept in
    ``provenance.claimed``. A ``kind`` outside ALLOWED_KINDS (``real`` above
    all) is therefore re-read as a claim rather than dropped, so the stateless
    path preserves the same evidence the stateful path keeps from
    ``state.sim_or_real``.
    """
    if not isinstance(existing, dict):
        return None
    claimed = existing.get("claimed")
    if claimed is not None:
        return claimed
    kind = existing.get("kind")
    if isinstance(kind, str) and kind.strip():
        return kind
    return None


def _attach_owner(owner):
    if not isinstance(owner, dict):
        return
    state = owner.get("state")
    has_state = isinstance(state, dict)
    if has_state and "sim_or_real" in state:
        claimed = state.get("sim_or_real")
        if isinstance(claimed, str) and claimed.strip().lower() in ALLOWED_KINDS:
            prov = {"kind": claimed.strip().lower(), "claimed": claimed}
        else:
            prov = remap_claimed(claimed)
        state["sim_or_real"] = prov["kind"]
        state["provenance"] = dict(prov)
        owner["provenance"] = dict(prov)
        return
    existing = owner.get("provenance")
    if isinstance(existing, dict) and existing.get("kind") in ALLOWED_KINDS:
        if has_state and "provenance" not in state:
            state["provenance"] = dict(existing)
        elif not has_state and existing.get("kind") == "unknown":
            inferred = _factory_origin_provenance(owner)
            if inferred is not None:
                inferred["claimed"] = existing.get("claimed")
                owner["provenance"] = inferred
        return
    # The existing provenance carries a kind this promotion cannot accept.
    # Re-read it as a claim instead of discarding it: dropping it here made the
    # two paths disagree about the same real-world claim, since the stateful
    # branch above keeps `claimed` while this one returned claimed=None. It
    # also made the mix bucket depend on unrelated envelope metadata, because
    # a `real` claim landed on `designed` only when meta.factory happened to
    # be present. Remapping the claim reaches `designed` either way, which is
    # the documented promotion contract: cleaned records never emit `real`,
    # and the original claim survives in provenance.claimed.
    claimed = _rejected_claim(existing)
    if has_state:
        prov = remap_claimed(claimed)
        state["provenance"] = dict(prov)
        owner["provenance"] = dict(prov)
        return
    prov = remap_claimed(claimed)
    if prov["kind"] == "unknown":
        # No usable claim; the factory envelope is the only evidence left.
        inferred = _factory_origin_provenance(owner)
        if inferred is not None:
            inferred["claimed"] = prov["claimed"]
            prov = inferred
    owner["provenance"] = prov


def _walk_state_owners(obj, seen):
    if isinstance(obj, dict):
        oid = id(obj)
        if oid in seen:
            return
        seen.add(oid)
        if "state" in obj and isinstance(obj["state"], dict):
            _attach_owner(obj)
        for value in obj.values():
            _walk_state_owners(value, seen)
    elif isinstance(obj, list):
        for item in obj:
            _walk_state_owners(item, seen)


def _events_are_singly_timed(events):
    """True when every event has exactly one finite timestamp key."""
    return all(event_time(event) is not None for event in events)


def _sort_events(events):
    return sorted(events, key=lambda event: event_time(event)[1])


def _spike_stream_needs_resort(events, enclosing=None):
    """True when an unambiguous stream is out of order and safe to resort.

    Dual-key, untimed, or non-object events make clocks incomparable.
    check_spikes can still report an order error from the remaining timed
    events; the caller must not rewrite those streams with inf placeholders,
    so only a singly-timed stream is eligible here.

    A stream spanning two declared clock domains is equally incomparable even
    when every event is singly timed, so check_spikes is given the enclosing
    record and stays silent for it. promote_run() writes the cleaned copy
    without validating, so sorting there would publish a fabricated ordering
    stamped ``spike_events_resorted``.
    """
    return (
        isinstance(events, list)
        and _events_are_singly_timed(events)
        and check_spikes(events, "", enclosing)
    )


def _maybe_sort_spikes(obj, seen):
    resorted = 0
    if isinstance(obj, dict):
        oid = id(obj)
        if oid in seen:
            return 0
        seen.add(oid)
        events = obj.get("spike_events")
        if _spike_stream_needs_resort(events, obj):
            obj["spike_events"] = _sort_events(events)
            meta = obj.get("meta")
            if not isinstance(meta, dict):
                meta = {}
                obj["meta"] = meta
            meta["spike_events_resorted"] = True
            resorted += 1
        for value in obj.values():
            resorted += _maybe_sort_spikes(value, seen)
    elif isinstance(obj, list):
        for item in obj:
            resorted += _maybe_sort_spikes(item, seen)
    return resorted


def promote_record(obj):
    """Attach provenance, rewrite sim_or_real, sort spikes. Mutates obj."""
    if not isinstance(obj, dict):
        return obj
    _walk_state_owners(obj, set())
    # State owners were normalized by the walk. Normalize a stateless wrapper
    # even when a prior stage left a generic ``unknown`` stamp; its factory
    # metadata is stronger evidence without overwriting the original state
    # claim captured above.
    if not isinstance(obj.get("state"), dict):
        _attach_owner(obj)
    _maybe_sort_spikes(obj, set())
    return obj


def _load_units_migration(raw_run):
    path = Path(raw_run) / FFPC / "units-migration.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _scopes_for_file(migration, filename):
    if not isinstance(migration, dict):
        return []
    matches = []
    for rec in migration.get("records", []):
        if not isinstance(rec, dict):
            continue
        scope = rec.get("scope") or ""
        if filename in scope:
            matches.append(rec)
    return matches


def _entry_from_scopes(scopes):
    if not scopes:
        return dict(DEFAULT_SCALE)
    factors = []
    natives = []
    for rec in scopes:
        factors.append(rec.get("usd_conversion_factor"))
        if rec.get("native_units"):
            natives.append(rec["native_units"])
    unique = set()
    for factor in factors:
        if factor is None:
            unique.add(None)
        elif isinstance(factor, (int, float)) and not isinstance(factor, bool):
            unique.add(float(factor))
        else:
            unique.add(factor)
    native = natives[0] if natives else "unspecified"
    if len(scopes) > 1 and len(unique) > 1:
        return {
            "aggregation": "unspecified",
            "native_unit": "mixed; see units-migration.json",
            "usd_factor_or_null": None,
            "mix_policy": "exclude_from_magnitude",
        }
    factor = factors[0]
    if factor is None:
        return {
            "aggregation": "unspecified",
            "native_unit": native,
            "usd_factor_or_null": None,
            "mix_policy": "sign_order_only",
        }
    try:
        numeric = float(factor)
    except (TypeError, ValueError):
        numeric = None
    return {
        "aggregation": "unspecified",
        "native_unit": native,
        "usd_factor_or_null": numeric,
        "mix_policy": "apply_usd_factor" if numeric is not None else "sign_order_only",
    }


def build_reward_scale(raw_run, jsonl_rels):
    """Per factory/file scale entries."""
    raw_run = Path(raw_run)
    migration = _load_units_migration(raw_run)
    scale = {}
    for rel in jsonl_rels:
        rel = Path(rel)
        factory = rel.parts[0] if len(rel.parts) > 1 else rel.parent.name or "unknown"
        filename = rel.name
        if factory == FFPC:
            entry = _entry_from_scopes(_scopes_for_file(migration, filename))
        else:
            entry = dict(DEFAULT_SCALE)
        scale.setdefault(factory, {})[filename] = entry
    return scale


def write_provenance_md(path):
    Path(path).write_text(PROVENANCE_MD)
    return path


def _iter_jsonl(raw_run):
    raw_run = Path(raw_run).resolve()
    for path in sorted(raw_run.rglob("*.jsonl")):
        yield path, path.relative_to(raw_run)


def promote_run(raw_run, cleaned_out):
    """Copy/remap every jsonl. Return a summary dict. Does not touch raw bytes."""
    raw_run = Path(raw_run).resolve()
    cleaned_out = Path(cleaned_out).resolve()
    if raw_run == cleaned_out or raw_run in cleaned_out.parents:
        raise ValueError(
            "cleaned_out must be distinct from, and not nested inside, raw_run"
        )
    if cleaned_out.exists():
        raise ValueError(
            f"refusing to overwrite an existing cleaned_out: {cleaned_out}"
        )
    cleaned_out.mkdir(parents=True, exist_ok=True)

    files = 0
    records = 0
    resorted = 0
    rels = []

    for src, rel in _iter_jsonl(raw_run):
        dest = cleaned_out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        lines_out = []
        text = src.read_text()
        for line in text.splitlines():
            if not line.strip():
                lines_out.append("")
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                lines_out.append(line)
                continue
            before_flag = False
            if isinstance(obj, dict):
                before_flag = bool(
                    isinstance(obj.get("meta"), dict)
                    and obj["meta"].get("spike_events_resorted")
                )
            promote_record(obj)
            after_flag = False
            if isinstance(obj, dict):
                after_flag = bool(
                    isinstance(obj.get("meta"), dict)
                    and obj["meta"].get("spike_events_resorted")
                )
            if after_flag and not before_flag:
                resorted += 1
            records += 1
            lines_out.append(json.dumps(obj, ensure_ascii=False))
        dest.write_text("\n".join(lines_out) + ("\n" if lines_out else ""))
        files += 1
        rels.append(rel)

    scale = build_reward_scale(raw_run, rels)
    (cleaned_out / "reward-scale.json").write_text(
        json.dumps(scale, indent=2) + "\n"
    )
    write_provenance_md(cleaned_out / "PROVENANCE.md")

    return {
        "raw_run": str(raw_run),
        "cleaned_out": str(cleaned_out),
        "files": files,
        "records": records,
        "resorted": resorted,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Promote raw factory JSONL into cleaned/ with provenance, then run "
            "the blocking quality gate."
        ),
    )
    parser.add_argument("raw_run", help="raw run directory (read-only)")
    parser.add_argument("cleaned_out", help="destination cleaned directory")
    parser.add_argument(
        "--quality-manifest",
        default=None,
        help=(
            "quality-gate manifest path (default: "
            "<cleaned_out>/quality-manifest.json)"
        ),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=quality_gate.DEFAULT_EMBEDDING_THRESHOLD,
        help="embedding near-duplicate cosine threshold (default: %(default)s)",
    )
    parser.add_argument(
        "--no-embedding-dedup",
        dest="embedding_dedup",
        action="store_false",
        help="skip embedding near-duplicate detection (exact dedup remains on)",
    )
    parser.add_argument(
        "--max-embedding-pairs",
        type=int,
        default=quality_gate.DEFAULT_MAX_EMBEDDING_PAIRS,
        help=(
            "blocking cap on LSH candidate pairs; observing an omitted pair "
            "fails closed (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--mix-target",
        type=float,
        default=quality_gate.DEFAULT_TARGET_SYNTHETIC_RATIO,
        help="target synthetic share (default: %(default)s)",
    )
    parser.add_argument(
        "--mix-tolerance",
        type=float,
        default=quality_gate.DEFAULT_MIX_TOLERANCE,
        help="slack above the target before blocking (default: %(default)s)",
    )
    parser.add_argument(
        "--max-synthetic-ratio",
        type=float,
        default=None,
        help="explicit blocking synthetic-share ceiling",
    )
    parser.add_argument(
        "--min-synthetic-ratio",
        type=float,
        default=None,
        help="optional blocking synthetic-share floor",
    )
    parser.add_argument(
        "--max-unlabeled-ratio",
        type=float,
        default=None,
        help="optional blocking ceiling for unlabeled records",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    raw_run = Path(args.raw_run)
    cleaned_out = Path(args.cleaned_out)
    if not raw_run.is_dir():
        print(f"error: not a directory: {raw_run}", file=sys.stderr)
        sys.exit(2)
    manifest_path = (
        Path(args.quality_manifest)
        if args.quality_manifest
        else cleaned_out / "quality-manifest.json"
    )
    resolved_raw = raw_run.resolve()
    resolved_manifest = manifest_path.resolve()
    if resolved_manifest == resolved_raw or resolved_raw in resolved_manifest.parents:
        print("error: quality manifest must not be written inside raw_run", file=sys.stderr)
        sys.exit(2)
    policy = quality_gate.MixPolicy(
        target=args.mix_target,
        tolerance=args.mix_tolerance,
        max_synthetic_ratio=args.max_synthetic_ratio,
        min_synthetic_ratio=args.min_synthetic_ratio,
        max_unlabeled_ratio=args.max_unlabeled_ratio,
    )
    try:
        quality_gate.validate_manifest_target(
            manifest_path, cleaned_out, allow_within_run=True
        )
        policy.validate()
        if not math.isfinite(args.threshold) or not 0.0 <= args.threshold < 1.0:
            raise ValueError(
                f"threshold must be a finite cosine in [0, 1), got {args.threshold!r}"
            )
        if args.max_embedding_pairs < 1:
            raise ValueError(
                "max_embedding_pairs must be >= 1, got "
                f"{args.max_embedding_pairs!r}"
            )
        summary = promote_run(raw_run, cleaned_out)
        report = quality_gate.audit_run(
            cleaned_out,
            threshold=args.threshold,
            mix_policy=policy,
            embedding_dedup=args.embedding_dedup,
            max_embedding_pairs=args.max_embedding_pairs,
        )
        written = quality_gate.write_manifest(
            manifest_path, cleaned_out, report, allow_within_run=True
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    summary["quality_gate"] = {
        "blocked": report["blocked"],
        "blockers": report["blockers"],
        "warnings": report["warnings"],
        "counts": report["counts"],
        "mix": report["mix"],
        "threshold": report["threshold"],
        "manifest": str(written),
    }
    print(json.dumps(summary, indent=2))
    for blocker in report["blockers"]:
        print(f"BLOCKED: {blocker}", file=sys.stderr)
    for warning in report["warnings"]:
        print(f"WARN: {warning}", file=sys.stderr)
    sys.exit(1 if report["blocked"] else 0)


if __name__ == "__main__":
    main()
