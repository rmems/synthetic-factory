#!/usr/bin/env python3
"""Scan JSONL batches for hidden-thought / private-reasoning keys.

Walks every JSON object key recursively. A key matches when its
factory-normalized name (case, separators, camelCase) is exactly one of:

    thought, chain_of_thought, scratch, inner_monologue, reasoning,
    internal_reasoning

or is in the ``internal_reasoning*`` prefix family.

Default corpus: all ``/tmp/**/batch-*.jsonl``. Paths whose components
include ``outputs/raw`` are skipped (immutable raw tree; never written).
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
import time
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

TARGET_EXACT = frozenset(
    {
        "thought",
        "chain_of_thought",
        "scratch",
        "inner_monologue",
        "reasoning",
        "internal_reasoning",
    }
)
INTERNAL_REASONING_PREFIX = "internal_reasoning"

DEFAULT_ROOT = Path("/tmp")
DEFAULT_GLOB = "batch-*.jsonl"
DEFAULT_REPORT = Path("/tmp/thought-key-scan.md")

# Staging batches from the current operator window; always tabulated.
OPERATOR_FOCUS = (
    Path("/tmp/actf-r10/batch-r10.jsonl"),
    Path("/tmp/ttf-r13/batch-r13.jsonl"),
    Path("/tmp/maos-r14/batch-r14.jsonl"),
    Path("/tmp/nelb-r13/batch-r13.jsonl"),
    Path("/tmp/ffpc-r11/batch-r11.jsonl"),
    Path("/tmp/batch-r12.jsonl"),
)

HITS_LIST_CAP = 200
FILES_TABLE_CAP = 400
PARSE_ERROR_CAP = 80


def normalized_key_name(value: Any) -> str:
    """Normalize JSON keys across case, separators, and camel-case boundaries."""
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(value)).casefold(),
    ).strip("_")


def is_thought_key(key: Any) -> bool:
    normalized = normalized_key_name(key)
    return normalized in TARGET_EXACT or normalized.startswith(
        INTERNAL_REASONING_PREFIX
    )


def is_outputs_raw(path: Path | str) -> bool:
    parts = Path(path).parts
    for index in range(len(parts) - 1):
        if parts[index] == "outputs" and parts[index + 1] == "raw":
            return True
    return False


def record_id(obj: Any) -> str:
    if not isinstance(obj, dict):
        return ""
    for key in ("id", "record_id", "uid"):
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    meta = obj.get("meta")
    if isinstance(meta, dict):
        for key in ("id", "record_id", "record"):
            value = meta.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def value_kind(value: Any) -> tuple[str, int]:
    if value is None:
        return "null", 0
    if isinstance(value, bool):
        return "bool", 0
    if isinstance(value, int) and not isinstance(value, bool):
        return "int", 0
    if isinstance(value, float):
        return "float", 0
    if isinstance(value, str):
        return "str", len(value)
    if isinstance(value, list):
        return "list", len(value)
    if isinstance(value, dict):
        return "dict", len(value)
    return type(value).__name__, 0


def walk_thought_keys(value: Any, path: str = "") -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            if is_thought_key(key):
                kind, length = value_kind(item)
                yield {
                    "path": child,
                    "key": str(key),
                    "normalized": normalized_key_name(key),
                    "value_kind": kind,
                    "value_len": length,
                }
            yield from walk_thought_keys(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_thought_keys(item, f"{path}[{index}]")


def scan_file(path_str: str) -> dict[str, Any]:
    path = Path(path_str)
    result: dict[str, Any] = {
        "path": path_str,
        "ok": False,
        "bytes": 0,
        "records": 0,
        "blank": 0,
        "hits": [],
        "parse_errors": [],
        "error": "",
    }
    try:
        result["bytes"] = path.stat().st_size
        with path.open("r", encoding="utf-8", errors="strict") as handle:
            for line_no, raw in enumerate(handle, start=1):
                if not raw.strip():
                    result["blank"] += 1
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as exc:
                    result["parse_errors"].append(
                        {"line": line_no, "error": str(exc)}
                    )
                    continue
                result["records"] += 1
                rec_id = record_id(obj)
                for hit in walk_thought_keys(obj):
                    hit["line"] = line_no
                    hit["id"] = rec_id
                    result["hits"].append(hit)
        result["ok"] = True
    except UnicodeDecodeError as exc:
        result["error"] = f"utf-8 decode: {exc}"
    except OSError as exc:
        result["error"] = f"os: {exc}"
    except Exception as exc:  # noqa: BLE001 — isolate worker crashes
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    return result


def scan_chunk(paths: list[str]) -> list[dict[str, Any]]:
    return [scan_file(path) for path in paths]


def _chunks(items: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def discover_batch_files(root: Path, pattern: str) -> tuple[list[str], int]:
    found: list[str] = []
    skipped_raw = 0
    root = root.resolve()

    def _walk_error(err: OSError) -> None:
        print(f"walk skip: {err}", file=sys.stderr)

    for dirpath, dirnames, filenames in os.walk(
        root, followlinks=False, onerror=_walk_error
    ):
        current = Path(dirpath)
        if is_outputs_raw(current):
            dirnames[:] = []
            skipped_raw += sum(
                1
                for name in filenames
                if fnmatch.fnmatch(name, pattern)
            )
            continue
        if current.name == "outputs" and "raw" in dirnames:
            raw_dir = current / "raw"
            for nested_root, _, nested_names in os.walk(raw_dir, followlinks=False):
                skipped_raw += sum(
                    1
                    for name in nested_names
                    if fnmatch.fnmatch(name, pattern)
                )
            dirnames.remove("raw")
        for name in filenames:
            if fnmatch.fnmatch(name, pattern):
                found.append(str(current / name))
    found.sort()
    return found, skipped_raw


def tmp_bucket(path_str: str) -> str:
    path = Path(path_str)
    parts = path.parts
    try:
        tmp_index = parts.index("tmp")
    except ValueError:
        return str(path.parent)
    if tmp_index + 1 < len(parts):
        child = parts[tmp_index + 1]
        if child.startswith("batch-") and child.endswith(".jsonl"):
            return "/tmp (root files)"
        return f"/tmp/{child}"
    return "/tmp"


def md_escape(text: str) -> str:
    return (
        str(text)
        .replace("|", "\\|")
        .replace("\n", " ")
        .replace("`", "\\`")
    )


def render_report(
    *,
    root: Path,
    pattern: str,
    files: list[str],
    skipped_raw: int,
    results: list[dict[str, Any]],
    elapsed_s: float,
    jobs: int,
    scanned_at: str,
) -> str:
    by_path = {item["path"]: item for item in results}
    n_ok = sum(1 for item in results if item["ok"])
    n_fail = sum(1 for item in results if not item["ok"])
    n_records = sum(item["records"] for item in results)
    n_parse = sum(len(item["parse_errors"]) for item in results)
    n_hits = sum(len(item["hits"]) for item in results)
    hitting = [item for item in results if item["hits"]]
    hitting.sort(key=lambda item: (-len(item["hits"]), item["path"]))

    key_counts: Counter[str] = Counter()
    norm_counts: Counter[str] = Counter()
    bucket_files: Counter[str] = Counter()
    bucket_hits: Counter[str] = Counter()
    bucket_hit_files: Counter[str] = Counter()
    for item in results:
        bucket = tmp_bucket(item["path"])
        bucket_files[bucket] += 1
        n = len(item["hits"])
        if n:
            bucket_hits[bucket] += n
            bucket_hit_files[bucket] += 1
        for hit in item["hits"]:
            key_counts[hit["key"]] += 1
            norm_counts[hit["normalized"]] += 1

    lines: list[str] = []
    lines.append("# Thought-key scan")
    lines.append("")
    lines.append(f"**When (UTC):** {scanned_at}")
    lines.append(f"**Scanner:** `/tmp/scan_thought_keys.py`")
    lines.append(f"**Root:** `{root}`")
    lines.append(f"**Glob:** `{pattern}`")
    lines.append("**Excluded:** any path whose components include `outputs/raw/`")
    lines.append(
        "**Match:** recursive JSON **keys** only (not string values). "
        "Factory `normalized_key_name` (casefold, camelCase split, non-alnum → `_`). "
        "Exact: `thought`, `chain_of_thought`, `scratch`, `inner_monologue`, "
        "`reasoning`, `internal_reasoning`. Prefix family: `internal_reasoning*`."
    )
    lines.append(
        "**Not matched:** metadata such as `thought_fields_removed`, nearby names "
        "such as `reasoning_flaw`, or `hidden_reasoning` (not in this token list)."
    )
    lines.append("")
    verdict = "CLEAN" if n_hits == 0 and n_fail == 0 else (
        "HITS" if n_hits else "SCAN-ERRORS"
    )
    lines.append(f"**Verdict:** {verdict}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| metric | count |")
    lines.append("|--------|------:|")
    lines.append(f"| files matching glob | {len(files) + skipped_raw} |")
    lines.append(f"| skipped (`outputs/raw/`) | {skipped_raw} |")
    lines.append(f"| files scanned | {len(results)} |")
    lines.append(f"| files readable | {n_ok} |")
    lines.append(f"| files unreadable | {n_fail} |")
    lines.append(f"| JSONL records parsed | {n_records} |")
    lines.append(f"| JSON parse errors | {n_parse} |")
    lines.append(f"| files with thought-key hits | {len(hitting)} |")
    lines.append(f"| thought-key occurrences | {n_hits} |")
    lines.append(f"| unique original keys | {len(key_counts)} |")
    lines.append(f"| unique normalized keys | {len(norm_counts)} |")
    lines.append(f"| wall seconds | {elapsed_s:.1f} |")
    lines.append(f"| worker processes | {jobs} |")
    lines.append("")

    lines.append("## Operator staging (always listed)")
    lines.append("")
    lines.append(
        "Current-window staging batches. These are outside `outputs/raw/` "
        "and are the fail-closed gate targets."
    )
    lines.append("")
    lines.append("| path | exists | records | hits | keys | ids |")
    lines.append("|------|:------:|--------:|-----:|------|-----|")
    for focus in OPERATOR_FOCUS:
        path_str = str(focus)
        exists = focus.is_file()
        item = by_path.get(path_str)
        if not exists:
            lines.append(f"| `{path_str}` | no | — | — | — | — |")
            continue
        if item is None:
            lines.append(
                f"| `{path_str}` | yes | — | — | *not in scan set* | — |"
            )
            continue
        keys = sorted({hit["key"] for hit in item["hits"]})
        ids = sorted({hit["id"] for hit in item["hits"] if hit["id"]})
        key_s = ", ".join(f"`{k}`" for k in keys) if keys else "—"
        id_s = ", ".join(ids) if ids else "—"
        lines.append(
            f"| `{path_str}` | yes | {item['records']} | {len(item['hits'])} | "
            f"{key_s} | {md_escape(id_s)} |"
        )
        if item["hits"]:
            for hit in item["hits"]:
                lines.append(
                    f"  - line {hit['line']} id=`{hit['id'] or '?'}` "
                    f"`{hit['path']}` key=`{hit['key']}` "
                    f"norm=`{hit['normalized']}` "
                    f"{hit['value_kind']} len={hit['value_len']}"
                )
    lines.append("")

    lines.append("## Hits by original key")
    lines.append("")
    if not key_counts:
        lines.append("None.")
    else:
        lines.append("| original key | occurrences |")
        lines.append("|--------------|------------:|")
        for key, count in key_counts.most_common():
            lines.append(f"| `{md_escape(key)}` | {count} |")
        lines.append("")
        lines.append("### Normalized key")
        lines.append("")
        lines.append("| normalized | occurrences |")
        lines.append("|------------|------------:|")
        for key, count in norm_counts.most_common():
            lines.append(f"| `{md_escape(key)}` | {count} |")
    lines.append("")

    lines.append("## Hits by `/tmp` bucket")
    lines.append("")
    lines.append("| bucket | files scanned | files with hits | occurrences |")
    lines.append("|--------|--------------:|----------------:|------------:|")
    buckets = sorted(
        bucket_files,
        key=lambda name: (-bucket_hits[name], -bucket_hit_files[name], name),
    )
    for bucket in buckets:
        if bucket_hits[bucket] == 0 and bucket_hit_files[bucket] == 0:
            continue
        lines.append(
            f"| `{md_escape(bucket)}` | {bucket_files[bucket]} | "
            f"{bucket_hit_files[bucket]} | {bucket_hits[bucket]} |"
        )
    if n_hits == 0:
        lines.append("| — | 0 | 0 | 0 |")
        lines.append("")
        lines.append("No bucket produced a thought-key hit.")
    lines.append("")
    clean_buckets = sum(1 for b in bucket_files if bucket_hits[b] == 0)
    lines.append(
        f"Clean buckets (files scanned, zero hits): **{clean_buckets}** / "
        f"{len(bucket_files)}."
    )
    lines.append("")

    lines.append("## Hitting files")
    lines.append("")
    if not hitting:
        lines.append("No thought-key hits in any scanned `batch-*.jsonl`.")
    else:
        lines.append(
            f"{len(hitting)} file(s) with hits. "
            f"Table capped at {FILES_TABLE_CAP} rows (sorted by hit count)."
        )
        lines.append("")
        lines.append("| path | records | hits | original keys | sample ids |")
        lines.append("|------|--------:|-----:|---------------|------------|")
        for item in hitting[:FILES_TABLE_CAP]:
            keys = sorted({hit["key"] for hit in item["hits"]})
            ids = []
            seen_ids: set[str] = set()
            for hit in item["hits"]:
                if hit["id"] and hit["id"] not in seen_ids:
                    seen_ids.add(hit["id"])
                    ids.append(hit["id"])
                if len(ids) >= 3:
                    break
            key_s = ", ".join(f"`{md_escape(k)}`" for k in keys[:8])
            if len(keys) > 8:
                key_s += f" (+{len(keys) - 8})"
            id_s = ", ".join(ids) if ids else "—"
            lines.append(
                f"| `{md_escape(item['path'])}` | {item['records']} | "
                f"{len(item['hits'])} | {key_s or '—'} | {md_escape(id_s)} |"
            )
        if len(hitting) > FILES_TABLE_CAP:
            lines.append("")
            lines.append(
                f"… {len(hitting) - FILES_TABLE_CAP} additional hitting files omitted."
            )
        lines.append("")
        lines.append("### Hit paths (cap)")
        lines.append("")
        shown = 0
        for item in hitting:
            if shown >= HITS_LIST_CAP:
                break
            for hit in item["hits"]:
                if shown >= HITS_LIST_CAP:
                    break
                lines.append(
                    f"- `{md_escape(item['path'])}`:{hit['line']} "
                    f"id=`{md_escape(hit['id'] or '?')}` "
                    f"path=`{md_escape(hit['path'])}` "
                    f"key=`{md_escape(hit['key'])}` "
                    f"norm=`{md_escape(hit['normalized'])}` "
                    f"{hit['value_kind']} len={hit['value_len']}"
                )
                shown += 1
        if n_hits > shown:
            lines.append("")
            lines.append(f"… {n_hits - shown} additional occurrences omitted.")
    lines.append("")

    parse_rows = []
    for item in results:
        for err in item["parse_errors"]:
            parse_rows.append((item["path"], err["line"], err["error"]))
    fail_rows = [
        (item["path"], item["error"]) for item in results if not item["ok"]
    ]
    lines.append("## Read / parse errors")
    lines.append("")
    if not parse_rows and not fail_rows:
        lines.append("None.")
    else:
        if fail_rows:
            lines.append(f"Unreadable files: {len(fail_rows)}")
            lines.append("")
            for path_str, error in fail_rows[:PARSE_ERROR_CAP]:
                lines.append(f"- `{md_escape(path_str)}`: {md_escape(error)}")
            if len(fail_rows) > PARSE_ERROR_CAP:
                lines.append(
                    f"- … {len(fail_rows) - PARSE_ERROR_CAP} more unreadable files"
                )
            lines.append("")
        if parse_rows:
            lines.append(f"JSON parse errors: {n_parse}")
            lines.append("")
            for path_str, line_no, error in parse_rows[:PARSE_ERROR_CAP]:
                lines.append(
                    f"- `{md_escape(path_str)}`:{line_no}: {md_escape(error)}"
                )
            if len(parse_rows) > PARSE_ERROR_CAP:
                lines.append(
                    f"- … {len(parse_rows) - PARSE_ERROR_CAP} more parse errors"
                )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "This report does not read or write `outputs/raw/`. "
        "Raw evidence may legally keep thought keys; curated / staging "
        "batches in this scan must not."
    )
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--glob", dest="pattern", default=DEFAULT_GLOB)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--jobs",
        type=int,
        default=max(1, min(16, os.cpu_count() or 1)),
        help="Worker processes (default: min(16, nproc))",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if is_outputs_raw(args.report):
        print("refusing to write report under outputs/raw/", file=sys.stderr)
        return 2
    started = time.perf_counter()
    scanned_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    files, skipped_raw = discover_batch_files(args.root, args.pattern)
    print(
        f"discovered {len(files)} files "
        f"(skipped outputs/raw: {skipped_raw}); jobs={args.jobs}",
        file=sys.stderr,
    )
    results: list[dict[str, Any]] = []
    if not files:
        elapsed = time.perf_counter() - started
        report = render_report(
            root=args.root,
            pattern=args.pattern,
            files=files,
            skipped_raw=skipped_raw,
            results=results,
            elapsed_s=elapsed,
            jobs=args.jobs,
            scanned_at=scanned_at,
        )
        args.report.write_text(report, encoding="utf-8")
        print(report)
        return 0

    jobs = max(1, min(args.jobs, len(files)))
    chunk_size = max(8, min(64, (len(files) + jobs - 1) // max(jobs * 8, 1)))
    chunks = list(_chunks(files, chunk_size))
    done = 0
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(scan_chunk, chunk): chunk for chunk in chunks}
        for future in as_completed(futures):
            chunk = futures[future]
            try:
                results.extend(future.result())
            except Exception as exc:  # noqa: BLE001
                for path in chunk:
                    results.append(
                        {
                            "path": path,
                            "ok": False,
                            "bytes": 0,
                            "records": 0,
                            "blank": 0,
                            "hits": [],
                            "parse_errors": [],
                            "error": f"worker: {type(exc).__name__}: {exc}",
                        }
                    )
            done += len(chunk)
            if done % 4000 < chunk_size or done >= len(files):
                print(
                    f"scanned {min(done, len(files))}/{len(files)}",
                    file=sys.stderr,
                )
    elapsed = time.perf_counter() - started
    report = render_report(
        root=args.root,
        pattern=args.pattern,
        files=files,
        skipped_raw=skipped_raw,
        results=results,
        elapsed_s=elapsed,
        jobs=jobs,
        scanned_at=scanned_at,
    )
    args.report.write_text(report, encoding="utf-8")
    n_hits = sum(len(item["hits"]) for item in results)
    n_fail = sum(1 for item in results if not item["ok"])
    print(
        f"wrote {args.report} hits={n_hits} unreadable={n_fail} "
        f"files={len(results)} in {elapsed:.1f}s",
        file=sys.stderr,
    )
    return 1 if n_hits or n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
