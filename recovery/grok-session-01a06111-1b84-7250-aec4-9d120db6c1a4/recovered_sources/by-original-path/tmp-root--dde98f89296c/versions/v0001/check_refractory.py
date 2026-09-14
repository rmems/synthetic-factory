#!/usr/bin/env python3
"""Report same-channel consecutive spike gaps below the 0.8 ms refractory floor.

Loads any JSONL, walks every nested ``spike_events`` list, and reports
consecutive same-channel dt < 0.8 ms (800 µs). Timestamp is ``t_rel_ms``
when present; other finite numeric time keys are accepted as a fallback.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

REFRACTORY_MS = 0.8
TIME_KEYS = ("t_rel_ms", "t_ms", "timestamp_ms")


def is_finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def event_t_rel_ms(event):
    """Return (time_key, t_rel_ms) for a spike object, or None."""
    if not isinstance(event, dict):
        return None
    for key in TIME_KEYS:
        if key not in event:
            continue
        value = event[key]
        if is_finite_number(value):
            return key, float(value)
    return None


def walk_spike_event_lists(obj, path="$"):
    """Yield (json_path, events) for every list stored under spike_events."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            if key == "spike_events" and isinstance(value, list):
                yield child, value
            yield from walk_spike_event_lists(value, child)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            yield from walk_spike_event_lists(item, f"{path}[{index}]")


def channel_name(event):
    if not isinstance(event, dict):
        return None
    channel = event.get("channel")
    if isinstance(channel, str) and channel.strip():
        return channel
    return None


def consecutive_same_channel_gaps(events):
    """Yield gap dicts for consecutive same-channel spikes in time order.

    Events without a channel or a finite timestamp are skipped. Within a
    channel, order follows the list (globally non-decreasing trains keep
    per-channel order). dt is later minus earlier, in milliseconds.
    """
    by_channel = defaultdict(list)
    for index, event in enumerate(events):
        channel = channel_name(event)
        timed = event_t_rel_ms(event)
        if channel is None or timed is None:
            continue
        key, t_ms = timed
        by_channel[channel].append(
            {
                "index": index,
                "t_rel_ms": t_ms,
                "time_key": key,
                "amplitude": event.get("amplitude"),
            }
        )

    for channel, spikes in by_channel.items():
        for prev, curr in zip(spikes, spikes[1:]):
            dt_ms = curr["t_rel_ms"] - prev["t_rel_ms"]
            yield {
                "channel": channel,
                "i0": prev["index"],
                "i1": curr["index"],
                "t0_ms": prev["t_rel_ms"],
                "t1_ms": curr["t_rel_ms"],
                "dt_ms": dt_ms,
                "time_key": curr["time_key"],
                "a0": prev["amplitude"],
                "a1": curr["amplitude"],
                "violation": dt_ms < REFRACTORY_MS,
            }


def load_jsonl(path):
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            raw = line.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as exc:
                records.append(
                    {
                        "line": line_no,
                        "id": None,
                        "parse_error": str(exc),
                        "record": None,
                    }
                )
                continue
            rec_id = None
            if isinstance(obj, dict):
                rec_id = obj.get("id")
            records.append(
                {
                    "line": line_no,
                    "id": rec_id,
                    "parse_error": None,
                    "record": obj,
                }
            )
    return records


def inspect_record(entry):
    """Return per-stream gap stats for one JSONL line."""
    streams = []
    if entry["parse_error"] is not None:
        return streams
    obj = entry["record"]
    for path, events in walk_spike_event_lists(obj):
        gaps = list(consecutive_same_channel_gaps(events))
        violations = [g for g in gaps if g["violation"]]
        channels = sorted(
            {
                event.get("channel")
                for event in events
                if isinstance(event, dict) and isinstance(event.get("channel"), str)
            }
        )
        streams.append(
            {
                "path": path,
                "n_events": len(events),
                "n_channels": len(channels),
                "channels": channels,
                "n_gaps": len(gaps),
                "gaps": gaps,
                "violations": violations,
                "min_dt_ms": min((g["dt_ms"] for g in gaps), default=None),
            }
        )
    return streams


def fmt_ms(value):
    if value is None:
        return "n/a"
    return f"{value:.6f}"


def print_report(path, entries, streams_by_line):
    violations = []
    n_streams = 0
    n_events = 0
    n_gaps = 0
    for entry in entries:
        for stream in streams_by_line[entry["line"]]:
            n_streams += 1
            n_events += stream["n_events"]
            n_gaps += stream["n_gaps"]
            for gap in stream["violations"]:
                violations.append((entry, stream, gap))

    print(f"file: {path}")
    print(f"records: {len(entries)}")
    print(f"spike_events lists: {n_streams}")
    print(f"events: {n_events}")
    print(f"same-channel consecutive gaps: {n_gaps}")
    print(f"refractory floor: {REFRACTORY_MS} ms")
    print(f"violations (dt < {REFRACTORY_MS} ms): {len(violations)}")
    print()

    parse_errors = [e for e in entries if e["parse_error"]]
    if parse_errors:
        print(f"parse errors: {len(parse_errors)}")
        for entry in parse_errors:
            print(f"  line {entry['line']}: {entry['parse_error']}")
        print()

    print("per-record min same-channel dt")
    for entry in entries:
        rec_id = entry["id"] or "(no id)"
        streams = streams_by_line[entry["line"]]
        if entry["parse_error"]:
            print(f"  L{entry['line']} {rec_id}: PARSE ERROR")
            continue
        if not streams:
            print(f"  L{entry['line']} {rec_id}: no spike_events lists")
            continue
        for stream in streams:
            n_viol = len(stream["violations"])
            print(
                f"  L{entry['line']} {rec_id} {stream['path']}: "
                f"n={stream['n_events']} channels={stream['n_channels']} "
                f"gaps={stream['n_gaps']} min_dt_ms={fmt_ms(stream['min_dt_ms'])} "
                f"violations={n_viol}"
            )

    if violations:
        print()
        print("violations")
        for entry, stream, gap in violations:
            rec_id = entry["id"] or "(no id)"
            print(
                f"  L{entry['line']} {rec_id} {stream['path']} "
                f"channel={gap['channel']!r} "
                f"idx {gap['i0']}->{gap['i1']} "
                f"t {gap['t0_ms']:.6f}->{gap['t1_ms']:.6f} ms "
                f"dt={gap['dt_ms']:.6f} ms "
                f"(floor {REFRACTORY_MS} ms)"
            )
    return violations


def markdown_report(path, entries, streams_by_line, violations):
    lines = [
        "# Refractory check",
        "",
        f"- file: `{path}`",
        f"- records: {len(entries)}",
        f"- spike_events lists: {sum(len(v) for v in streams_by_line.values())}",
        f"- same-channel consecutive gaps: "
        f"{sum(s['n_gaps'] for ss in streams_by_line.values() for s in ss)}",
        f"- refractory floor: {REFRACTORY_MS} ms (800 µs)",
        f"- violations (dt < {REFRACTORY_MS} ms): {len(violations)}",
        "",
        "## Per-record min same-channel dt",
        "",
        "| line | id | path | n | channels | gaps | min_dt_ms | violations |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for entry in entries:
        rec_id = entry["id"] or "(no id)"
        streams = streams_by_line[entry["line"]]
        if entry["parse_error"]:
            lines.append(
                f"| {entry['line']} | `{rec_id}` | PARSE ERROR |  |  |  |  |  |"
            )
            continue
        if not streams:
            lines.append(
                f"| {entry['line']} | `{rec_id}` | *(none)* | 0 | 0 | 0 | n/a | 0 |"
            )
            continue
        for stream in streams:
            lines.append(
                f"| {entry['line']} | `{rec_id}` | `{stream['path']}` | "
                f"{stream['n_events']} | {stream['n_channels']} | "
                f"{stream['n_gaps']} | {fmt_ms(stream['min_dt_ms'])} | "
                f"{len(stream['violations'])} |"
            )

    lines.extend(["", "## Violations", ""])
    if not violations:
        lines.append("None. Every same-channel consecutive gap is ≥ 0.8 ms.")
    else:
        lines.extend(
            [
                "| line | id | path | channel | i0 | i1 | t0_ms | t1_ms | dt_ms |",
                "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for entry, stream, gap in violations:
            rec_id = entry["id"] or "(no id)"
            lines.append(
                f"| {entry['line']} | `{rec_id}` | `{stream['path']}` | "
                f"`{gap['channel']}` | {gap['i0']} | {gap['i1']} | "
                f"{gap['t0_ms']:.6f} | {gap['t1_ms']:.6f} | {gap['dt_ms']:.6f} |"
            )

    lines.extend(["", "## All same-channel consecutive gaps", ""])
    any_gap = False
    for entry in entries:
        rec_id = entry["id"] or "(no id)"
        for stream in streams_by_line[entry["line"]]:
            if not stream["gaps"]:
                continue
            any_gap = True
            lines.append(f"### L{entry['line']} `{rec_id}` `{stream['path']}`")
            lines.append("")
            lines.append("| channel | i0 | i1 | t0_ms | t1_ms | dt_ms | ok |")
            lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- |")
            for gap in stream["gaps"]:
                ok = "yes" if not gap["violation"] else "**NO**"
                lines.append(
                    f"| `{gap['channel']}` | {gap['i0']} | {gap['i1']} | "
                    f"{gap['t0_ms']:.6f} | {gap['t1_ms']:.6f} | "
                    f"{gap['dt_ms']:.6f} | {ok} |"
                )
            lines.append("")
    if not any_gap:
        lines.append("No same-channel consecutive pairs (every channel fired at most once).")
        lines.append("")

    lines.append("Checker: `/tmp/check_refractory.py`. Did not write `outputs/raw/`.")
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: check_refractory.py <file.jsonl> [report.md]", file=sys.stderr)
        return 2
    path = Path(argv[0])
    report_path = Path(argv[1]) if len(argv) > 1 else None
    entries = load_jsonl(path)
    streams_by_line = {entry["line"]: inspect_record(entry) for entry in entries}
    violations = print_report(path, entries, streams_by_line)
    if report_path is not None:
        report_path.write_text(
            markdown_report(path, entries, streams_by_line, violations),
            encoding="utf-8",
        )
        print()
        print(f"wrote {report_path}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
