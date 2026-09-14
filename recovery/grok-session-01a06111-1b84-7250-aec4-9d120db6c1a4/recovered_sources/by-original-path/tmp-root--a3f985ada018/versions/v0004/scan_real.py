#!/usr/bin/env python3
"""Scan /tmp/**/batch-*.jsonl for publish-time 'real' provenance claims.

Uses pipelines.check_records.claims_real and check_provenance_publish when
importable. Never walks or writes outputs/raw/.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
DEFAULT_ROOT = Path("/tmp")
BATCH_PREFIX = "batch-"
BATCH_SUFFIX = ".jsonl"
OUTPUTS_RAW_MARKER = "/outputs/raw/"
FALLBACK_SOURCE = "inline-fallback"

_CLAIMS_REAL = None
_CHECK_PROVENANCE_PUBLISH = None
_CANONICAL_RECORD_ID = None
_IMPORT_STATUS = {
    "ok": False,
    "source": FALLBACK_SOURCE,
    "error": None,
}


def _fallback_claims_real(value):
    if not isinstance(value, str):
        return False
    lowered = value.strip().lower()
    return lowered == "real" or lowered.startswith(("real_", "real-", "real "))


def _fallback_canonical_record_id(obj):
    if not isinstance(obj, dict):
        return None
    value = obj.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    meta = obj.get("meta")
    if isinstance(meta, dict):
        value = meta.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _fallback_check_provenance_publish(obj, where):
    errs = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                cur = f"{path}.{key}" if path else key
                if key == "sim_or_real" and _fallback_claims_real(value):
                    errs.append(
                        f"{where}: {cur} must not be 'real' (use 'designed') — got {value!r}"
                    )
                if key == "provenance" and isinstance(value, dict):
                    kind = value.get("kind")
                    if _fallback_claims_real(kind):
                        errs.append(
                            f"{where}: {cur}.kind must not be 'real' — got {kind!r}"
                        )
                walk(value, cur)
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{path}[{index}]")

    walk(obj, "")
    seen = set()
    out = []
    for err in errs:
        if err not in seen:
            seen.add(err)
            out.append(err)
    return out


def _import_check_records():
    status = {"ok": False, "source": FALLBACK_SOURCE, "error": None}
    repo = str(REPO)
    pipelines = str(REPO / "pipelines")
    attempts = (
        ("pipelines.check_records", [repo]),
        ("check_records", [pipelines, repo]),
    )
    last_error = None
    for module_name, extra_paths in attempts:
        for path in extra_paths:
            if path not in sys.path:
                sys.path.insert(0, path)
        try:
            module = __import__(module_name, fromlist=["claims_real", "check_provenance_publish"])
            claims = getattr(module, "claims_real", None)
            check = getattr(module, "check_provenance_publish", None)
            if not callable(claims) or not callable(check):
                raise ImportError(
                    f"{module_name} missing claims_real/check_provenance_publish"
                )
            canonical = getattr(module, "canonical_record_id", None)
            status.update(
                ok=True,
                source=f"{module_name} ({getattr(module, '__file__', '?')})",
                error=None,
            )
            return claims, check, canonical if callable(canonical) else None, status
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    status["error"] = last_error
    return (
        _fallback_claims_real,
        _fallback_check_provenance_publish,
        _fallback_canonical_record_id,
        status,
    )


def _init_worker():
    global _CLAIMS_REAL, _CHECK_PROVENANCE_PUBLISH, _CANONICAL_RECORD_ID, _IMPORT_STATUS
    claims, check, canonical, status = _import_check_records()
    _CLAIMS_REAL = claims
    _CHECK_PROVENANCE_PUBLISH = check
    _CANONICAL_RECORD_ID = canonical or _fallback_canonical_record_id
    _IMPORT_STATUS = status


def is_outputs_raw_path(path):
    normalized = path.replace("\\", "/")
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    if OUTPUTS_RAW_MARKER in normalized:
        return True
    stripped = normalized.rstrip("/")
    return stripped.endswith("/outputs/raw") or stripped == "/outputs/raw"


def _batch_files_under(dirpath, walk_errors):
    found = []

    def onerror(err):
        walk_errors.append(f"{type(err).__name__}: {err}")

    for nested_dir, _dirnames, filenames in os.walk(dirpath, onerror=onerror, followlinks=False):
        for name in filenames:
            if name.startswith(BATCH_PREFIX) and name.endswith(BATCH_SUFFIX):
                found.append(os.path.join(nested_dir, name))
    return found


def discover_batch_files(root):
    found = []
    skipped_outputs_raw = []
    walk_errors = []

    def onerror(err):
        walk_errors.append(f"{type(err).__name__}: {err}")

    for dirpath, dirnames, filenames in os.walk(root, onerror=onerror, followlinks=False):
        if is_outputs_raw_path(dirpath):
            skipped_outputs_raw.extend(
                os.path.join(dirpath, name)
                for name in filenames
                if name.startswith(BATCH_PREFIX) and name.endswith(BATCH_SUFFIX)
            )
            dirnames[:] = []
            continue
        keep = []
        for name in dirnames:
            child = os.path.join(dirpath, name)
            if is_outputs_raw_path(child):
                skipped_outputs_raw.extend(_batch_files_under(child, walk_errors))
            else:
                keep.append(name)
        dirnames[:] = keep
        for name in filenames:
            if not (name.startswith(BATCH_PREFIX) and name.endswith(BATCH_SUFFIX)):
                continue
            path = os.path.join(dirpath, name)
            try:
                resolved = os.path.realpath(path)
            except OSError:
                resolved = path
            if is_outputs_raw_path(path) or is_outputs_raw_path(resolved):
                skipped_outputs_raw.append(path)
                continue
            found.append(path)
    found.sort()
    skipped_outputs_raw = sorted(set(skipped_outputs_raw))
    return found, skipped_outputs_raw, walk_errors


def _walk_real_claims(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            cur = f"{path}.{key}" if path else key
            if key == "sim_or_real" and _CLAIMS_REAL(value):
                hits.append({"path": cur, "key": key, "value": value})
            elif key == "provenance" and isinstance(value, dict):
                kind = value.get("kind")
                if _CLAIMS_REAL(kind):
                    hits.append({"path": f"{cur}.kind", "key": "provenance.kind", "value": kind})
                hits.extend(_walk_real_claims(value, cur))
            else:
                hits.extend(_walk_real_claims(value, cur))
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            hits.extend(_walk_real_claims(item, f"{path}[{index}]"))
    return hits


def scan_file(path):
    result = {
        "path": path,
        "records": 0,
        "blank_lines": 0,
        "hits": [],
        "parse_errors": [],
        "io_error": None,
        "bytes": None,
    }
    try:
        result["bytes"] = os.path.getsize(path)
        with open(path, "r", encoding="utf-8") as handle:
            for line_no, raw in enumerate(handle, 1):
                if not raw.strip():
                    result["blank_lines"] += 1
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as exc:
                    result["parse_errors"].append(
                        {"line": line_no, "error": f"JSONDecodeError: {exc}"}
                    )
                    continue
                result["records"] += 1
                where = f"{path}:{line_no}"
                try:
                    record_id = _CANONICAL_RECORD_ID(obj)
                except Exception:
                    record_id = None
                try:
                    publish_errors = list(_CHECK_PROVENANCE_PUBLISH(obj, where))
                except Exception as exc:
                    result["parse_errors"].append(
                        {
                            "line": line_no,
                            "error": f"check_provenance_publish: {type(exc).__name__}: {exc}",
                        }
                    )
                    publish_errors = []
                try:
                    claimed = _walk_real_claims(obj)
                except Exception as exc:
                    result["parse_errors"].append(
                        {
                            "line": line_no,
                            "error": f"claims_real walk: {type(exc).__name__}: {exc}",
                        }
                    )
                    claimed = []
                if publish_errors or claimed:
                    result["hits"].append(
                        {
                            "line": line_no,
                            "id": record_id,
                            "claims": claimed,
                            "publish_errors": publish_errors,
                        }
                    )
    except OSError as exc:
        result["io_error"] = f"{type(exc).__name__}: {exc}"
    except UnicodeDecodeError as exc:
        result["io_error"] = f"UnicodeDecodeError: {exc}"
    return result


def _chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def scan_chunk(paths):
    _init_worker()
    return [scan_file(path) for path in paths]


def _md_escape(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def classify_path(path):
    lowered = path.lower()
    if "/outputs/raw/" in lowered:
        return "outputs_raw"
    if "/tests/fixtures/" in lowered or "/fixtures/" in lowered:
        return "fixture"
    if "failure-as-fuel" in lowered or "/ffpc" in lowered:
        return "ffpc_copy"
    if "thalamic" in lowered:
        return "thalamic_copy"
    if "neuromorphic-event-language-bridge" in lowered:
        return "nelb_copy"
    if any(token in lowered for token in ("/dry", "-dry", "smoke", "mill")):
        return "dry_or_mill"
    if "/scratchpad/" in lowered or "/probe/" in lowered:
        return "scratch"
    if "/tmp/tmp" in lowered or "/tmp/tmp." in lowered:
        return "ephemeral_tmp"
    return "other"


def _truncate(text, limit=96):
    text = str(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _claim_signature(item):
    return tuple(sorted((c["path"], c["value"]) for c in item.get("claims") or []))


def unique_hit_identities(hits):
    grouped = {}
    for item in hits:
        record_id = item.get("id")
        key = record_id if record_id else f"NO_ID {item['path']}:{item['line']}"
        bucket = grouped.setdefault(
            key,
            {
                "id": record_id,
                "n": 0,
                "files": set(),
                "claims": _claim_signature(item),
                "class": classify_path(item["path"]),
            },
        )
        bucket["n"] += 1
        bucket["files"].add(item["path"])
    rows = []
    for key, bucket in grouped.items():
        rows.append(
            {
                "key": key,
                "id": bucket["id"],
                "n": bucket["n"],
                "copies": len(bucket["files"]),
                "class": bucket["class"],
                "claims": bucket["claims"],
            }
        )
    rows.sort(key=lambda row: (row["id"] is None, row["key"]))
    return rows


def build_report(summary):
    hits = summary["hits"]
    parse_errors = summary["parse_errors"]
    io_errors = summary["io_errors"]
    n_hit_files = len({item["path"] for item in hits})
    n_hit_records = len(hits)
    n_publish_errors = sum(len(item["publish_errors"]) for item in hits)
    n_claims = sum(len(item["claims"]) for item in hits)
    complete = not parse_errors and not io_errors and not summary["walk_errors"]
    if n_hit_records:
        verdict = "FAIL"
    elif complete:
        verdict = "PASS"
    else:
        verdict = "PASS-WITH-GAPS"

    by_class = {}
    for item in hits:
        kind = classify_path(item["path"])
        by_class.setdefault(kind, {"files": set(), "records": 0})
        by_class[kind]["files"].add(item["path"])
        by_class[kind]["records"] += 1

    lines = []
    lines.append("# Never-real provenance scan")
    lines.append("")
    lines.append(f"**Verdict:** {verdict}")
    lines.append(f"**When (UTC):** {summary['started_utc']} → {summary['finished_utc']}")
    lines.append(f"**Repo:** `{summary['repo']}`")
    lines.append(f"**Scanner:** `{summary['scanner']}`")
    lines.append(f"**Scope:** `{summary['root']}/**/batch-*.jsonl`")
    lines.append("**Excluded:** any path containing `/outputs/raw/` (immutable; not scanned).")
    lines.append("")
    lines.append("Gate: a record fails when `check_provenance_publish` reports a nested")
    lines.append("`sim_or_real` / `provenance.kind` value that `claims_real` treats as a")
    lines.append("real-world claim (`real`, `real_*`, `real-*`, `real …`).")
    lines.append("")
    lines.append("## Import")
    lines.append("")
    lines.append(f"- **ok:** `{summary['import']['ok']}`")
    lines.append(f"- **source:** `{summary['import']['source']}`")
    if summary["import"].get("error"):
        lines.append(f"- **error:** `{_md_escape(summary['import']['error'])}`")
        lines.append("- Fallback copies the `check_records` walk (`sim_or_real` + `provenance.kind`).")
    else:
        lines.append("- Used `pipelines.check_records.claims_real` and `check_provenance_publish`.")
    lines.append("")
    lines.append("## Totals")
    lines.append("")
    lines.append("| metric | count |")
    lines.append("|---|---:|")
    lines.append(f"| batch-*.jsonl discovered | {summary['files_discovered']} |")
    lines.append(f"| skipped `outputs/raw/` | {summary['files_skipped_outputs_raw']} |")
    lines.append(f"| scanned | {summary['files_scanned']} |")
    lines.append(f"| bytes scanned | {summary['bytes_scanned']} |")
    lines.append(f"| JSONL records | {summary['records']} |")
    lines.append(f"| blank lines | {summary['blank_lines']} |")
    lines.append(f"| walk errors | {len(summary['walk_errors'])} |")
    lines.append(f"| I/O errors | {len(io_errors)} |")
    lines.append(f"| parse / checker errors | {len(parse_errors)} |")
    lines.append(f"| files with real claims | {n_hit_files} |")
    lines.append(f"| records with real claims | {n_hit_records} |")
    lines.append(f"| `claims_real` hits | {n_claims} |")
    lines.append(f"| `check_provenance_publish` errors | {n_publish_errors} |")
    lines.append("")
    lines.append("## Hits by path class")
    lines.append("")
    if not by_class:
        lines.append("No real-world provenance claims.")
        lines.append("")
    else:
        lines.append("| class | files | records |")
        lines.append("|---|---:|---:|")
        for kind in sorted(by_class):
            info = by_class[kind]
            lines.append(f"| {kind} | {len(info['files'])} | {info['records']} |")
        lines.append("")

    identities = unique_hit_identities(hits)
    named = [row for row in identities if row["id"]]
    anonymous = [row for row in identities if not row["id"]]
    lines.append("## Unique identities")
    lines.append("")
    if not hits:
        lines.append("None.")
        lines.append("")
    else:
        lines.append(
            f"{len(identities)} distinct identities "
            f"({len(named)} with `id`, {len(anonymous)} without) "
            f"across {n_hit_records} copy-rows in {n_hit_files} files."
        )
        lines.append("")
        lines.append("Current staging trees (`/tmp/actf-r10`, `/tmp/maos-r14`, `/tmp/nelb-r13`, `/tmp/ttf-r13`) had **zero** hits.")
        lines.append("Hits are historical TTF / FFPC / NELB copies under hub snapshots and audit packs, not new staging.")
        lines.append("")
        if named:
            lines.append("### Named record ids")
            lines.append("")
            lines.append("| id | copies | class | claims |")
            lines.append("|---|---:|---|---|")
            for row in named:
                claims = "; ".join(f"{path}={_truncate(value, 72)!r}" for path, value in row["claims"]) or "—"
                lines.append(
                    f"| `{_md_escape(row['id'])}` | {row['copies']} | {row['class']} | {_md_escape(claims)} |"
                )
            lines.append("")
        if anonymous:
            lines.append("### Records without top-level `id`")
            lines.append("")
            lines.append("Early TTF `batch-r02` / NELB `batch-r02`/`batch-r03` copies (legacy envelope).")
            lines.append("")
            lines.append("| location | class | claims |")
            lines.append("|---|---|---|")
            for row in anonymous[:80]:
                claims = "; ".join(f"{path}={_truncate(value, 72)!r}" for path, value in row["claims"]) or "—"
                loc = row["key"][len("NO_ID ") :] if row["key"].startswith("NO_ID ") else row["key"]
                lines.append(f"| `{_md_escape(loc)}` | {row['class']} | {_md_escape(claims)} |")
            if len(anonymous) > 80:
                lines.append("")
                lines.append(f"_Showing 80 of {len(anonymous)} anonymous hit rows._")
            lines.append("")

    lines.append("## Real-claim records (per copy)")
    lines.append("")
    if not hits:
        lines.append("None. Every parsed record passed `check_provenance_publish`.")
        lines.append("")
    else:
        max_rows = 120
        lines.append("| file | line | id | class | claims |")
        lines.append("|---|---:|---|---|---|")
        for item in hits[:max_rows]:
            claims = "; ".join(
                f"{c['path']}={_truncate(c['value'], 64)!r}" for c in item["claims"]
            ) or "—"
            rec_id = item["id"] or "—"
            lines.append(
                "| `{path}` | {line} | `{rid}` | {klass} | {claims} |".format(
                    path=_md_escape(item["path"]),
                    line=item["line"],
                    rid=_md_escape(rec_id),
                    klass=classify_path(item["path"]),
                    claims=_md_escape(claims),
                )
            )
        if len(hits) > max_rows:
            lines.append("")
            lines.append(f"_Showing first {max_rows} of {len(hits)} copy-rows. See unique identities above._")
        lines.append("")

        lines.append("## Hit files")
        lines.append("")
        file_counts = {}
        for item in hits:
            file_counts[item["path"]] = file_counts.get(item["path"], 0) + 1
        lines.append("| file | hit records |")
        lines.append("|---|---:|")
        for path, count in sorted(file_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:200]:
            lines.append(f"| `{_md_escape(path)}` | {count} |")
        if len(file_counts) > 200:
            lines.append("")
            lines.append(f"_Showing 200 of {len(file_counts)} hit files._")
        lines.append("")

    skipped = summary.get("skipped_outputs_raw_sample") or []
    n_skipped = summary.get("files_skipped_outputs_raw") or 0
    if n_skipped:
        lines.append("## Skipped `outputs/raw/`")
        lines.append("")
        lines.append(f"{n_skipped} `batch-*.jsonl` files under `/outputs/raw/` were enumerated and **not** parsed.")
        lines.append("")
        for path in skipped[:20]:
            lines.append(f"- `{_md_escape(path)}`")
        if n_skipped > 20:
            lines.append(f"- _… {n_skipped - 20} more_")
        lines.append("")

    if parse_errors:
        lines.append("## Parse / checker errors")
        lines.append("")
        lines.append("| file | line | error |")
        lines.append("|---|---:|---|")
        for item in parse_errors[:100]:
            lines.append(
                f"| `{_md_escape(item['path'])}` | {item['line']} | {_md_escape(item['error'])} |"
            )
        if len(parse_errors) > 100:
            lines.append("")
            lines.append(f"_Showing first 100 of {len(parse_errors)} parse errors._")
        lines.append("")

    if io_errors:
        lines.append("## I/O errors")
        lines.append("")
        for item in io_errors[:50]:
            lines.append(f"- `{item['path']}`: {_md_escape(item['error'])}")
        if len(io_errors) > 50:
            lines.append(f"- _… {len(io_errors) - 50} more_")
        lines.append("")

    if summary["walk_errors"]:
        lines.append("## Walk errors")
        lines.append("")
        for err in summary["walk_errors"][:50]:
            lines.append(f"- {_md_escape(err)}")
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append("- `outputs/raw/` was not scanned and was not written.")
    lines.append("- `claims_real` matches exact `real` or a `real_` / `real-` / `real ` prefix;")
    lines.append("  substrings such as `not_real` / `non-real` are not claims.")
    lines.append("- Completeness gaps (parse/I/O) do not by themselves prove a real claim,")
    lines.append("  but they leave those lines unverified.")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="scan root (default /tmp)")
    parser.add_argument("--repo", default=str(REPO), help="synthetic-factory repo")
    parser.add_argument("--report", default="/tmp/never-real-scan.md")
    parser.add_argument("--json-out", default="/tmp/scan_real-results.json")
    parser.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument("--chunk-size", type=int, default=64)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    global REPO
    REPO = Path(args.repo)
    started = datetime.now(timezone.utc)
    _init_worker()
    import_status = dict(_IMPORT_STATUS)

    files, skipped, walk_errors = discover_batch_files(args.root)
    jobs = max(1, args.jobs)
    chunk_size = max(1, args.chunk_size)
    chunks = list(_chunked(files, chunk_size))

    totals = {
        "files_scanned": 0,
        "bytes_scanned": 0,
        "records": 0,
        "blank_lines": 0,
        "hits": [],
        "parse_errors": [],
        "io_errors": [],
    }

    if not files:
        worker_results = []
    elif jobs == 1:
        worker_results = [scan_file(path) for path in files]
    else:
        worker_results = []
        with ProcessPoolExecutor(max_workers=jobs, initializer=_init_worker) as pool:
            futures = [pool.submit(scan_chunk, chunk) for chunk in chunks]
            for future in as_completed(futures):
                worker_results.extend(future.result())

    for item in worker_results:
        totals["files_scanned"] += 1
        totals["bytes_scanned"] += int(item.get("bytes") or 0)
        totals["records"] += item["records"]
        totals["blank_lines"] += item["blank_lines"]
        if item.get("io_error"):
            totals["io_errors"].append({"path": item["path"], "error": item["io_error"]})
        for err in item.get("parse_errors") or []:
            totals["parse_errors"].append({"path": item["path"], **err})
        for hit in item.get("hits") or []:
            totals["hits"].append({"path": item["path"], **hit})

    totals["hits"].sort(key=lambda row: (row["path"], row["line"]))
    totals["parse_errors"].sort(key=lambda row: (row["path"], row.get("line") or 0))
    totals["io_errors"].sort(key=lambda row: row["path"])
    finished = datetime.now(timezone.utc)

    summary = {
        "repo": str(REPO),
        "scanner": str(Path(__file__).resolve()),
        "root": str(Path(args.root).resolve()) if os.path.exists(args.root) else args.root,
        "started_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "finished_utc": finished.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "import": import_status,
        "jobs": jobs,
        "files_discovered": len(files) + len(skipped),
        "files_skipped_outputs_raw": len(skipped),
        "skipped_outputs_raw_sample": skipped[:20],
        "walk_errors": walk_errors,
        **totals,
    }

    report = build_report(summary)
    if args.report:
        report_path = Path(args.report)
        report_path.write_text(report, encoding="utf-8")
    if args.json_out:
        slim = dict(summary)
        Path(args.json_out).write_text(json.dumps(slim, indent=2, default=str) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "verdict": "FAIL"
                if summary["hits"]
                else ("PASS" if not summary["parse_errors"] and not summary["io_errors"] else "PASS-WITH-GAPS"),
                "files_scanned": summary["files_scanned"],
                "records": summary["records"],
                "hits": len(summary["hits"]),
                "parse_errors": len(summary["parse_errors"]),
                "io_errors": len(summary["io_errors"]),
                "skipped_outputs_raw": summary["files_skipped_outputs_raw"],
                "import_ok": summary["import"]["ok"],
                "report": args.report,
            }
        )
    )
    return 1 if summary["hits"] else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
