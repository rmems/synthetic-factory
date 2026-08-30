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
import re
import sys
from pathlib import Path
from typing import NamedTuple

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))
from check_records import check_spikes, event_time  # noqa: E402
from exact_json import (  # noqa: E402
    dumps_exact_json,
    exact_fraction,
    parse_finite_json_float as _parse_exact_json_float,
)
import quality_gate  # noqa: E402
from quality_gate import validate_embedding_threshold  # noqa: E402
from validate_run import reject_json_constant  # noqa: E402

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


def _matching_existing_claim(default, kind, candidates):
    """Keep an earlier claim when its canonical kind still matches."""
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("kind") != kind:
            continue
        if "claimed" in candidate:
            return candidate["claimed"]
    return default


def _provenance_for_state_claim(claimed, candidates=()):
    """Normalize a state claim while retaining an already-canonical label."""
    if isinstance(claimed, str) and claimed.strip().lower() in ALLOWED_KINDS:
        kind = claimed.strip().lower()
        return {
            "kind": kind,
            "claimed": _matching_existing_claim(claimed, kind, candidates),
        }
    return remap_claimed(claimed)


def _record_state_claim(owner, state):
    """Normalize and mirror ``state.sim_or_real`` provenance."""
    prov = _provenance_for_state_claim(
        state.get("sim_or_real"),
        (state.get("provenance"), owner.get("provenance")),
    )
    state["sim_or_real"] = prov["kind"]
    state["provenance"] = dict(prov)
    owner["provenance"] = dict(prov)


def _preserve_accepted_provenance(owner, state, existing):
    """Mirror or strengthen provenance that already has an accepted kind."""
    if state is not None:
        state["provenance"] = dict(existing)
        owner["provenance"] = dict(existing)
        return
    if existing.get("kind") != "unknown":
        return
    inferred = _factory_origin_provenance(owner)
    if inferred is not None:
        inferred["claimed"] = existing.get("claimed")
        owner["provenance"] = inferred


def _provenance_carrier(owner, state):
    """Resolve meaningful provenance in state-then-owner authority order."""
    nested = state.get("provenance") if state is not None else None
    for candidate in (nested, owner.get("provenance")):
        if isinstance(candidate, dict) and _rejected_claim(candidate) is not None:
            return candidate
    return None


def _provenance_from_rejected_claim(owner, existing):
    """Remap rejected provenance, using the factory envelope as a fallback."""
    prov = remap_claimed(_rejected_claim(existing))
    if prov["kind"] != "unknown":
        return prov
    inferred = _factory_origin_provenance(owner)
    if inferred is None:
        return prov
    inferred["claimed"] = prov["claimed"]
    return inferred


def _attach_owner(owner):
    if not isinstance(owner, dict):
        return
    state = owner.get("state")
    if not isinstance(state, dict):
        state = None
    if state is not None and "sim_or_real" in state:
        _record_state_claim(owner, state)
        return
    existing = _provenance_carrier(owner, state)
    if existing is not None and existing.get("kind") in ALLOWED_KINDS:
        _preserve_accepted_provenance(owner, state, existing)
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
    if state is not None:
        prov = remap_claimed(_rejected_claim(existing))
        state["provenance"] = dict(prov)
        owner["provenance"] = dict(prov)
        return
    owner["provenance"] = _provenance_from_rejected_claim(owner, existing)


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
    return sorted(events, key=lambda event: exact_fraction(event_time(event)[1]))


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


def _literal_lf_lines(path) -> list[str]:
    """Decode JSONL using only literal LF bytes as record boundaries."""

    physical_lines = path.read_bytes().split(b"\n")
    if physical_lines and physical_lines[-1] == b"":
        physical_lines.pop()
    return [raw_line.decode("utf-8") for raw_line in physical_lines]


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
        for line in _literal_lf_lines(src):
            if not line.strip():
                lines_out.append("")
                continue
            try:
                obj = json.loads(
                    line,
                    parse_constant=reject_json_constant,
                    parse_float=_parse_exact_json_float,
                )
            except (ValueError, RecursionError):
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
            lines_out.append(
                dumps_exact_json(obj, ensure_ascii=False, sort_keys=False)
            )
        dest.write_text(
            "\n".join(lines_out) + ("\n" if lines_out else ""),
            encoding="utf-8",
            newline="",
        )
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


class _PromotionPlan(NamedTuple):
    raw_run: Path
    cleaned_out: Path
    manifest_path: Path
    policy: quality_gate.MixPolicy


def _require_raw_directory(value):
    raw_run = Path(value)
    if not raw_run.is_dir():
        raise ValueError(f"not a directory: {raw_run}")
    return raw_run.resolve()


def _quality_manifest_path(args, cleaned_out):
    if args.quality_manifest:
        return Path(args.quality_manifest)
    return cleaned_out / "quality-manifest.json"


def _validate_manifest_outside_raw(raw_run, manifest_path):
    resolved_raw = raw_run.resolve()
    resolved_manifest = manifest_path.resolve()
    if resolved_manifest == resolved_raw or resolved_raw in resolved_manifest.parents:
        raise ValueError("quality manifest must not be written inside raw_run")


class _PromotionCreatedPaths(NamedTuple):
    files: frozenset
    directories: frozenset


def _promotion_created_paths(raw_run, cleaned_out):
    """Return files and directories ``promote_run`` predictably creates."""
    cleaned_root = cleaned_out.resolve()
    files = {
        cleaned_root / "PROVENANCE.md",
        cleaned_root / "reward-scale.json",
    }
    for _source, relative in _iter_jsonl(raw_run):
        files.add((cleaned_root / relative).resolve())
    directories = frozenset(
        parent
        for destination in files
        for parent in destination.parents
        if cleaned_root in parent.parents
    )
    return _PromotionCreatedPaths(frozenset(files), directories)


def _validate_promotion_created_paths(created):
    collisions = created.files & created.directories
    if collisions:
        conflict = min(collisions, key=str)
        raise ValueError(
            "promotion output path would be both a file and directory: "
            f"{conflict}"
        )


def _validate_manifest_not_created_by_promotion(created, manifest_path):
    resolved_manifest = manifest_path.resolve()
    file_conflict = next(
        (
            path
            for path in created.files
            if path == resolved_manifest or path in resolved_manifest.parents
        ),
        None,
    )
    if resolved_manifest in created.directories or file_conflict is not None:
        raise ValueError(
            "quality manifest conflicts with a path created during promotion: "
            f"{manifest_path}"
        )


def _mix_policy_from_args(args):
    return quality_gate.MixPolicy(
        target=args.mix_target,
        tolerance=args.mix_tolerance,
        max_synthetic_ratio=args.max_synthetic_ratio,
        min_synthetic_ratio=args.min_synthetic_ratio,
        max_unlabeled_ratio=args.max_unlabeled_ratio,
    )


def _validate_embedding_pair_cap(value):
    if value < 1:
        raise ValueError(f"max_embedding_pairs must be >= 1, got {value!r}")


def _prepare_promotion(args):
    raw_run = _require_raw_directory(args.raw_run)
    cleaned_out = Path(args.cleaned_out).resolve()
    manifest_path = _quality_manifest_path(args, cleaned_out).resolve()
    created = _promotion_created_paths(raw_run, cleaned_out)
    _validate_promotion_created_paths(created)
    _validate_manifest_outside_raw(raw_run, manifest_path)
    _validate_manifest_not_created_by_promotion(created, manifest_path)
    quality_gate.validate_manifest_target(
        manifest_path, cleaned_out, allow_within_run=True
    )
    policy = _mix_policy_from_args(args).validate()
    validate_embedding_threshold(args.threshold)
    _validate_embedding_pair_cap(args.max_embedding_pairs)
    return _PromotionPlan(raw_run, cleaned_out, manifest_path, policy)


def _promote_with_quality_gate(args, plan):
    summary = promote_run(plan.raw_run, plan.cleaned_out)
    report = quality_gate.audit_run(
        plan.cleaned_out,
        threshold=args.threshold,
        mix_policy=plan.policy,
        embedding_dedup=args.embedding_dedup,
        max_embedding_pairs=args.max_embedding_pairs,
    )
    written = quality_gate.write_manifest(
        plan.manifest_path, plan.cleaned_out, report, allow_within_run=True
    )
    return summary, report, written


def _quality_gate_summary(report, written):
    return {
        "blocked": report["blocked"],
        "blockers": report["blockers"],
        "warnings": report["warnings"],
        "counts": report["counts"],
        "mix": report["mix"],
        "threshold": report["threshold"],
        "manifest": str(written),
    }


def _emit_gate_messages(report):
    for blocker in report["blockers"]:
        print(f"BLOCKED: {blocker}", file=sys.stderr)
    for warning in report["warnings"]:
        print(f"WARN: {warning}", file=sys.stderr)


def main(argv=None):
    args = parse_args(argv)
    try:
        plan = _prepare_promotion(args)
        summary, report, written = _promote_with_quality_gate(args, plan)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    summary["quality_gate"] = _quality_gate_summary(report, written)
    print(json.dumps(summary, indent=2))
    _emit_gate_messages(report)
    raise SystemExit(1 if report["blocked"] else 0)


if __name__ == "__main__":
    main()
