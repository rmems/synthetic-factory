#!/usr/bin/env python3
"""Lint /tmp/**/batch-*.jsonl and write /tmp/jsonl-lint.md. Read-only on JSONL."""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter

ROOT = "/tmp"
OUT = "/tmp/jsonl-lint.md"
FENCE = "```"
MAX_SAMPLES_PER_FILE = 8
MAX_FAILED_FILES_LISTED = 5000
SKIP_DIR_PREFIXES = ("systemd-private-", "snap-private-tmp")


def is_outputs_raw(path: str) -> bool:
    parts = path.split(os.sep)
    for i in range(len(parts) - 1):
        if parts[i] == "outputs" and parts[i + 1] == "raw":
            return True
    return False


def classify_pretty_fragment(stripped: str) -> bool:
    """True for JSONL lines that look like pretty-printed fragments, not other parse errors."""
    if stripped in ("{", "}", "[", "]", "},", "],"):
        return True
    if stripped.endswith(",") and stripped[:-1].strip() in ("}", "]", "{", "["):
        return True
    return False


def lint_line(line: str) -> list[str]:
    reasons: list[str] = []
    if FENCE in line:
        reasons.append("fence")
    if line[:1] in " \t":
        reasons.append("pretty_print")

    stripped = line.strip()
    if not stripped:
        return reasons

    try:
        obj = json.loads(line)
    except json.JSONDecodeError as exc:
        reasons.append(f"json.loads:{exc.msg}")
        if classify_pretty_fragment(stripped) and "pretty_print" not in reasons:
            reasons.append("pretty_print")
        return reasons

    if not isinstance(obj, dict):
        reasons.append(f"not_object:{type(obj).__name__}")
    return reasons


def lint_file(path: str) -> dict:
    result = {
        "path": path,
        "ok": True,
        "nonblank": 0,
        "blank": 0,
        "objects": 0,
        "errors": 0,
        "reasons": Counter(),
        "samples": [],
        "scan_error": None,
        "file_pretty_print": False,
        "empty": False,
    }
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        result["ok"] = False
        result["scan_error"] = f"os:{exc}"
        return result

    if b"\r" in raw:
        result["reasons"]["crlf"] += 1

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        result["ok"] = False
        result["scan_error"] = f"utf-8:{exc}"
        return result

    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    parse_fail_lines = []
    for lineno, line in enumerate(lines, 1):
        if line.endswith("\r"):
            line = line[:-1]
        if not line.strip():
            result["blank"] += 1
            continue
        result["nonblank"] += 1
        reasons = lint_line(line)
        if any(r.startswith("json.loads:") for r in reasons):
            parse_fail_lines.append(lineno)
        if not reasons:
            result["objects"] += 1
            continue
        result["ok"] = False
        result["errors"] += 1
        for r in reasons:
            key = r.split(":", 1)[0]
            result["reasons"][key] += 1
        if len(result["samples"]) < MAX_SAMPLES_PER_FILE:
            result["samples"].append({"line": lineno, "reasons": reasons, "preview": line[:120]})

    if result["nonblank"] == 0 and result["scan_error"] is None:
        result["empty"] = True

    if parse_fail_lines and text.strip():
        try:
            whole = json.loads(text)
        except json.JSONDecodeError:
            whole = None
        if whole is not None:
            result["file_pretty_print"] = True
            result["ok"] = False
            result["reasons"]["pretty_print"] += 1
            if len(result["samples"]) < MAX_SAMPLES_PER_FILE:
                result["samples"].append(
                    {
                        "line": parse_fail_lines[0],
                        "reasons": ["pretty_print:file_is_one_json_value"],
                        "preview": text.strip()[:120],
                    }
                )

    return result


def md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", "\\n")


def main() -> int:
    t0 = time.time()
    paths = []
    under_outputs_raw = 0
    for dirpath, dirnames, filenames in os.walk(ROOT, onerror=lambda _exc: None):
        dirnames[:] = [d for d in dirnames if d != "snap-private-tmp" and not d.startswith("systemd-private-")]
        for name in filenames:
            if name.startswith("batch-") and name.endswith(".jsonl"):
                path = os.path.join(dirpath, name)
                paths.append(path)
                if is_outputs_raw(path):
                    under_outputs_raw += 1
    paths.sort()

    totals = Counter()
    reason_totals = Counter()
    failed = []
    empty = 0
    scan_errors = []
    vanished = 0

    for path in paths:
        if not os.path.isfile(path):
            vanished += 1
            continue
        rec = lint_file(path)
        totals["files"] += 1
        totals["nonblank"] += rec["nonblank"]
        totals["blank"] += rec["blank"]
        totals["objects"] += rec["objects"]
        totals["line_errors"] += rec["errors"]
        reason_totals.update(rec["reasons"])
        if rec["empty"]:
            empty += 1
        if rec["scan_error"]:
            scan_errors.append(rec)
            totals["failed"] += 1
            continue
        if rec["ok"]:
            totals["passed"] += 1
        else:
            totals["failed"] += 1
            failed.append(rec)

    elapsed = time.time() - t0
    failed.sort(key=lambda r: r["path"])

    lines = []
    a = lines.append
    a("# JSONL lint")
    a("")
    a("Lint of every `/tmp/**/batch-*.jsonl` (nonblank lines).")
    a("Read-only on JSONL. Did not write under `outputs/raw/`.")
    a("")
    a("## Checks")
    a("")
    a("- one complete JSON object (`dict`) per nonblank line")
    a("- `json.loads` success on the whole line")
    a("- no pretty-print (leading indent, `{`/`[`/`]`/`}` fragment lines, or whole-file pretty JSON)")
    a("- no ` ``` ` fences inside lines")
    a("")
    a("## Summary")
    a("")
    a(f"- files discovered: {len(paths)}")
    a(f"- files linted: {totals['files']}")
    a(f"- under `*/outputs/raw/*` (read-only, not written): {under_outputs_raw}")
    a(f"- vanished before read: {vanished}")
    a(f"- passed: {totals['passed']}")
    a(f"- failed: {totals['failed']}")
    a(f"- empty (no nonblank lines): {empty}")
    a(f"- scan errors (open/decode): {len(scan_errors)}")
    a(f"- nonblank lines: {totals['nonblank']}")
    a(f"- blank lines: {totals['blank']}")
    a(f"- clean objects: {totals['objects']}")
    a(f"- line-level errors: {totals['line_errors']}")
    a(f"- elapsed_s: {elapsed:.2f}")
    a("")
    a("## Error reason counts")
    a("")
    if reason_totals:
        for key, n in sorted(reason_totals.items(), key=lambda kv: (-kv[1], kv[0])):
            a(f"- `{key}`: {n}")
    else:
        a("- none")
    a("")
    a("## Scan errors")
    a("")
    if not scan_errors:
        a("None.")
    else:
        for rec in scan_errors[:200]:
            a(f"- `{rec['path']}`: {rec['scan_error']}")
        if len(scan_errors) > 200:
            a(f"- … {len(scan_errors) - 200} more")
    a("")
    a("## Failed files")
    a("")
    if not failed:
        a("None. All linted files passed.")
    else:
        a(f"{len(failed)} failed files" + (
            f" (listing first {MAX_FAILED_FILES_LISTED})." if len(failed) > MAX_FAILED_FILES_LISTED else "."
        ))
        a("")
        listed = failed[:MAX_FAILED_FILES_LISTED]
        a("| path | nonblank | errors | reasons | sample |")
        a("|---|---:|---:|---|---|")
        for rec in listed:
            reasons = ", ".join(f"{k}={v}" for k, v in sorted(rec["reasons"].items()))
            sample = ""
            if rec["samples"]:
                s0 = rec["samples"][0]
                sample = f"L{s0['line']}: {', '.join(s0['reasons'])} :: {md_escape(s0['preview'])}"
            a(
                f"| `{rec['path']}` | {rec['nonblank']} | {rec['errors']} | {md_escape(reasons)} | {sample} |"
            )
        a("")
        a("### Sample details")
        a("")
        for rec in listed[:500]:
            a(f"#### `{rec['path']}`")
            a("")
            if rec["file_pretty_print"]:
                a("- whole file parses as one JSON value (pretty-printed / not JSONL)")
            for s in rec["samples"]:
                a(f"- line {s['line']}: {', '.join(s['reasons'])}")
                a(f"  - `{md_escape(s['preview'])}`")
            a("")
    a("")
    a("## Result")
    a("")
    if totals["failed"] == 0 and not scan_errors:
        a("PASS")
    else:
        a("FAIL")
    a("")

    text = "\n".join(lines)
    # Write report only to /tmp/jsonl-lint.md, never under outputs/raw/.
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
        if not text.endswith("\n"):
            fh.write("\n")
    print(f"wrote {OUT} files={totals['files']} passed={totals['passed']} failed={totals['failed']} empty={empty}", file=sys.stderr)
    return 0 if totals["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
