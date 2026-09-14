#!/usr/bin/env python3
"""Assert Multi-Agent Ouroboros Swarm transcript heading contract.

Given a swarm-transcript markdown file, check:

- exactly 2 densifying cycles
- each cycle has the 6 verbatim role headings in order
- no merged headings (e.g. ``Generator/Critic``)
- Critic sections contain no jsonl-looking full trajectory objects
  (heuristic: no line whose lstrip starts with ``{"id":``)
- Trajectory Builder is the last heading per cycle

Default target: ``/tmp/maos-r14/swarm-transcript-r14.md`` if it exists,
else the committed r04 transcript as a smoke test.

Does not write under outputs/raw/.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROLE_HEADINGS: tuple[str, ...] = (
    "Generator",
    "Critic",
    "Diversity Enforcer",
    "Edge-Case Hunter",
    "Neuromorphic Translator",
    "Trajectory Builder",
)
ROLE_SET = set(ROLE_HEADINGS)
ROLE_ALT = "|".join(re.escape(name) for name in ROLE_HEADINGS)
MERGED_HEADING_RE = re.compile(
    rf"(?:{ROLE_ALT})\s*(?:/|&|\+|,|;|and)\s*(?:{ROLE_ALT})",
    re.IGNORECASE,
)
CYCLE_MARKER_RE = re.compile(r"^CYCLE\s+(\d+)\b", re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
EMPTY_HEADING_RE = re.compile(r"^(#{1,6})\s*$")
FENCE_RE = re.compile(r"^(```|~~~)")
JSONL_TRAJECTORY_RE = re.compile(r'^\s*\{"id":')

DEFAULT_R14 = Path("/tmp/maos-r14/swarm-transcript-r14.md")
DEFAULT_R04 = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/"
    "2026-08-30/multi-agent-ouroboros-swarm/swarm-transcript-r04.md"
)


@dataclass(frozen=True)
class Heading:
    line_no: int
    level: int
    text: str
    raw: str
    in_fence: bool = False

    @property
    def verbatim_role(self) -> str | None:
        if self.level == 2 and self.text in ROLE_SET:
            return self.text
        return None

    @property
    def cycle_number(self) -> int | None:
        match = CYCLE_MARKER_RE.match(self.text)
        if match:
            return int(match.group(1))
        return None

    @property
    def is_merged(self) -> bool:
        return bool(MERGED_HEADING_RE.search(self.text))


@dataclass
class Cycle:
    number: int
    start_line: int
    end_line: int
    marker: Heading | None
    headings: list[Heading] = field(default_factory=list)
    role_headings: list[Heading] = field(default_factory=list)
    sections: dict[str, tuple[int, int]] = field(default_factory=dict)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


@dataclass
class Report:
    path: Path
    source: str
    checks: list[Check] = field(default_factory=list)
    cycles: list[Cycle] = field(default_factory=list)
    headings: list[Heading] = field(default_factory=list)
    merged: list[Heading] = field(default_factory=list)
    critic_hits: list[tuple[int, int, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.checks) and all(c.ok for c in self.checks) and not self.errors


def resolve_transcript(explicit: str | None) -> tuple[Path, str]:
    if explicit:
        path = Path(explicit)
        return path, "argv"
    if DEFAULT_R14.is_file():
        return DEFAULT_R14, "r14"
    return DEFAULT_R04, "smoke-r04"


def iter_lines(text: str) -> Iterable[tuple[int, str]]:
    for i, line in enumerate(text.splitlines(), start=1):
        yield i, line.rstrip("\n")


def parse_headings(text: str) -> list[Heading]:
    headings: list[Heading] = []
    in_fence = False
    fence_delim: str | None = None
    for line_no, line in iter_lines(text):
        fence = FENCE_RE.match(line.lstrip())
        if fence:
            delim = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_delim = delim
            elif delim == fence_delim:
                in_fence = False
                fence_delim = None
            continue
        if in_fence:
            continue
        empty = EMPTY_HEADING_RE.match(line)
        if empty:
            headings.append(
                Heading(
                    line_no=line_no,
                    level=len(empty.group(1)),
                    text="",
                    raw=line,
                )
            )
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        headings.append(
            Heading(
                line_no=line_no,
                level=len(match.group(1)),
                text=match.group(2).strip(),
                raw=line,
            )
        )
    return headings


def split_cycles(headings: list[Heading], n_lines: int) -> list[Cycle]:
    markers = [h for h in headings if h.cycle_number is not None]
    if markers:
        cycles: list[Cycle] = []
        for i, marker in enumerate(markers):
            start = marker.line_no
            end = markers[i + 1].line_no - 1 if i + 1 < len(markers) else n_lines
            body = [
                h
                for h in headings
                if start < h.line_no <= end and h is not marker
            ]
            roles = [h for h in body if h.verbatim_role]
            cycles.append(
                Cycle(
                    number=marker.cycle_number or (i + 1),
                    start_line=start,
                    end_line=end,
                    marker=marker,
                    headings=body,
                    role_headings=roles,
                )
            )
        return cycles

    roles = [h for h in headings if h.verbatim_role]
    if not roles:
        return []
    cycles = []
    for i in range(0, len(roles), len(ROLE_HEADINGS)):
        chunk = roles[i : i + len(ROLE_HEADINGS)]
        start = chunk[0].line_no
        if i + len(ROLE_HEADINGS) < len(roles):
            end = roles[i + len(ROLE_HEADINGS)].line_no - 1
        else:
            end = n_lines
        body = [h for h in headings if start <= h.line_no <= end]
        cycles.append(
            Cycle(
                number=len(cycles) + 1,
                start_line=start,
                end_line=end,
                marker=None,
                headings=body,
                role_headings=chunk,
            )
        )
    return cycles


def attach_sections(cycle: Cycle) -> None:
    roles = cycle.role_headings
    for i, heading in enumerate(roles):
        name = heading.verbatim_role
        if name is None:
            continue
        start = heading.line_no + 1
        if i + 1 < len(roles):
            end = roles[i + 1].line_no - 1
        else:
            end = cycle.end_line
        cycle.sections[name] = (start, end)


def scan_critic_jsonl(text: str, cycles: list[Cycle]) -> list[tuple[int, int, str]]:
    lines = text.splitlines()
    hits: list[tuple[int, int, str]] = []
    for cycle in cycles:
        span = cycle.sections.get("Critic")
        if span is None:
            continue
        start, end = span
        for line_no in range(start, end + 1):
            if line_no < 1 or line_no > len(lines):
                continue
            raw = lines[line_no - 1]
            if JSONL_TRAJECTORY_RE.match(raw):
                snippet = raw.strip()
                if len(snippet) > 160:
                    snippet = snippet[:157] + "..."
                hits.append((cycle.number, line_no, snippet))
    return hits


def check_transcript(path: Path, source: str) -> Report:
    report = Report(path=path, source=source)
    if not path.is_file():
        report.errors.append(f"transcript not found: {path}")
        report.checks.append(
            Check("file_exists", False, f"missing {path}")
        )
        return report

    text = path.read_text(encoding="utf-8")
    n_lines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
    if text and not text.endswith("\n"):
        n_lines = len(text.splitlines())
    else:
        n_lines = len(text.splitlines())

    headings = parse_headings(text)
    report.headings = headings
    report.merged = [h for h in headings if h.is_merged or ("/" in h.text and any(
        role.lower() in h.text.lower() for role in ROLE_HEADINGS
    ) and MERGED_HEADING_RE.search(h.text))]

    cycles = split_cycles(headings, n_lines)
    for cycle in cycles:
        attach_sections(cycle)
    report.cycles = cycles
    report.critic_hits = scan_critic_jsonl(text, cycles)

    role_names_found = [h.verbatim_role for h in headings if h.verbatim_role]

    # --- exactly 2 cycles ---
    if len(cycles) == 2:
        report.checks.append(
            Check(
                "exactly_2_cycles",
                True,
                "found 2 cycles"
                + (
                    f" (markers at lines {cycles[0].start_line}, {cycles[1].start_line})"
                    if cycles[0].marker or cycles[1].marker
                    else " (inferred from role-heading groups)"
                ),
            )
        )
    else:
        marker_desc = ", ".join(
            f"line {h.line_no}: {h.text}" for h in headings if h.cycle_number is not None
        ) or "no CYCLE markers"
        report.checks.append(
            Check(
                "exactly_2_cycles",
                False,
                f"found {len(cycles)} cycle(s); markers: {marker_desc}; "
                f"verbatim role H2 count={len(role_names_found)}",
            )
        )

    # --- 6 verbatim headings in order per cycle ---
    order_ok = True
    order_parts: list[str] = []
    expected = list(ROLE_HEADINGS)
    if not cycles:
        order_ok = False
        order_parts.append("no cycles to score")
    for cycle in cycles:
        got = [h.verbatim_role for h in cycle.role_headings]
        if got == expected:
            order_parts.append(
                f"cycle {cycle.number}: "
                + " → ".join(f"L{h.line_no} {h.verbatim_role}" for h in cycle.role_headings)
            )
        else:
            order_ok = False
            order_parts.append(
                f"cycle {cycle.number}: expected {expected}, got {got} "
                f"(H2s in span L{cycle.start_line}-L{cycle.end_line}: "
                + ", ".join(f"L{h.line_no} ## {h.text}" for h in cycle.headings if h.level == 2)
                + ")"
            )
    report.checks.append(
        Check("verbatim_headings_in_order", order_ok, "; ".join(order_parts) or "n/a")
    )

    # --- no merged headings ---
    if report.merged:
        detail = "; ".join(
            f"L{h.line_no} {'#' * h.level} {h.text!r}" for h in report.merged
        )
        report.checks.append(Check("no_merged_headings", False, detail))
    else:
        report.checks.append(
            Check(
                "no_merged_headings",
                True,
                "no heading matched Role[/&+,;and]Role",
            )
        )

    # --- critic has no jsonl-looking full trajectory objects ---
    if report.critic_hits:
        detail = "; ".join(
            f"cycle {c} L{n}: {s}" for c, n, s in report.critic_hits
        )
        report.checks.append(
            Check("critic_no_jsonl_trajectory", False, detail)
        )
    else:
        critic_spans = [
            f"cycle {c.number} L{c.sections['Critic'][0]}-{c.sections['Critic'][1]}"
            for c in cycles
            if "Critic" in c.sections
        ]
        report.checks.append(
            Check(
                "critic_no_jsonl_trajectory",
                True,
                "no Critic line starts with {\"id\":"
                + (f" ({'; '.join(critic_spans)})" if critic_spans else " (no Critic spans)"),
            )
        )

    # --- Trajectory Builder is the last heading per cycle ---
    last_ok = True
    last_parts: list[str] = []
    if not cycles:
        last_ok = False
        last_parts.append("no cycles")
    for cycle in cycles:
        if not cycle.headings:
            last_ok = False
            last_parts.append(f"cycle {cycle.number}: no headings in cycle body")
            continue
        last = cycle.headings[-1]
        if last.verbatim_role == "Trajectory Builder":
            last_parts.append(
                f"cycle {cycle.number}: last heading L{last.line_no} ## Trajectory Builder"
            )
        else:
            last_ok = False
            last_parts.append(
                f"cycle {cycle.number}: last heading is L{last.line_no} "
                f"{'#' * last.level} {last.text!r}, not ## Trajectory Builder"
            )
    report.checks.append(
        Check("trajectory_builder_last", last_ok, "; ".join(last_parts) or "n/a")
    )

    return report


def render_markdown(report: Report) -> str:
    now = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    status = "PASS" if report.ok else "FAIL"
    lines = [
        "# MAOS heading check report",
        "",
        f"- Result: **{status}**",
        f"- Transcript: `{report.path}`",
        f"- Selection: `{report.source}`",
        f"- Generated: {now}",
        f"- Checker: `/tmp/maos_heading_check.py`",
        "",
        "## Assertions",
        "",
        "| Check | Result | Detail |",
        "|-------|--------|--------|",
    ]
    for check in report.checks:
        mark = "PASS" if check.ok else "FAIL"
        detail = check.detail.replace("|", "\\|")
        lines.append(f"| `{check.name}` | {mark} | {detail} |")
    if report.errors:
        lines.extend(["", "## Errors", ""])
        for err in report.errors:
            lines.append(f"- {err}")

    lines.extend(["", "## Cycle inventory", ""])
    if not report.cycles:
        lines.append("No cycles parsed.")
    for cycle in report.cycles:
        marker = (
            f"marker L{cycle.marker.line_no} `{cycle.marker.raw}`"
            if cycle.marker
            else "no CYCLE marker (inferred)"
        )
        lines.append(f"### Cycle {cycle.number}")
        lines.append("")
        lines.append(f"- Span: L{cycle.start_line}–L{cycle.end_line} ({marker})")
        if cycle.role_headings:
            lines.append("- Verbatim role headings:")
            for heading in cycle.role_headings:
                lines.append(
                    f"  - L{heading.line_no} `## {heading.verbatim_role}`"
                )
        else:
            lines.append("- Verbatim role headings: none")
        extra = [
            h
            for h in cycle.headings
            if h.verbatim_role is None and h.cycle_number is None
        ]
        if extra:
            lines.append("- Other headings in cycle:")
            for heading in extra:
                lines.append(
                    f"  - L{heading.line_no} `{'#' * heading.level} {heading.text}`"
                )
        last = cycle.headings[-1] if cycle.headings else None
        if last:
            lines.append(
                f"- Last heading: L{last.line_no} `{'#' * last.level} {last.text}`"
            )
        critic = cycle.sections.get("Critic")
        if critic:
            lines.append(f"- Critic span: L{critic[0]}–L{critic[1]}")
        lines.append("")

    lines.extend(["## Merged headings", ""])
    if report.merged:
        for heading in report.merged:
            lines.append(
                f"- L{heading.line_no} `{'#' * heading.level} {heading.text}`"
            )
    else:
        lines.append("None.")
    lines.append("")

    lines.extend(["## Critic JSONL heuristic", ""])
    lines.append('Flag: any Critic line whose lstrip starts with `{"id":`.')
    lines.append("")
    if report.critic_hits:
        for cycle_no, line_no, snippet in report.critic_hits:
            lines.append(f"- cycle {cycle_no} L{line_no}: `{snippet}`")
    else:
        lines.append("No hits.")
    lines.append("")

    lines.extend(["## All ATX headings (outside fences)", ""])
    if not report.headings:
        lines.append("None.")
    else:
        for heading in report.headings:
            role = heading.verbatim_role or ""
            flag = []
            if role:
                flag.append("role")
            if heading.cycle_number is not None:
                flag.append(f"cycle-{heading.cycle_number}")
            if heading.is_merged:
                flag.append("MERGED")
            suffix = f" ({', '.join(flag)})" if flag else ""
            lines.append(
                f"- L{heading.line_no} `{'#' * heading.level} {heading.text}`{suffix}"
            )
    lines.append("")
    lines.append("## Contract")
    lines.append("")
    lines.append(
        "Source: `prompts/02-multi-agent-ouroboros-swarm.md` anti-collapsing rules. "
        "Six headings must appear verbatim per cycle: "
        + ", ".join(f"`## {name}`" for name in ROLE_HEADINGS)
        + ". Trajectory Builder is the last heading per cycle. "
        "Critic never emits trajectory JSONL."
    )
    lines.append("")
    return "\n".join(lines) + "\n"


def render_text(report: Report) -> str:
    status = "PASS" if report.ok else "FAIL"
    parts = [
        f"{status}  {report.path}  [{report.source}]",
    ]
    for check in report.checks:
        mark = "ok" if check.ok else "FAIL"
        parts.append(f"  [{mark}] {check.name}: {check.detail}")
    for err in report.errors:
        parts.append(f"  error: {err}")
    return "\n".join(parts) + "\n"


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "transcript",
        nargs="?",
        help="swarm-transcript markdown path (default: r14 if present else r04 smoke)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="write a markdown report to this path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="also print a JSON summary to stdout",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path, source = resolve_transcript(args.transcript)
    report = check_transcript(path, source)
    sys.stdout.write(render_text(report))
    if args.json:
        payload = {
            "ok": report.ok,
            "path": str(report.path),
            "source": report.source,
            "checks": [
                {"name": c.name, "ok": c.ok, "detail": c.detail} for c in report.checks
            ],
            "errors": report.errors,
            "cycles": [
                {
                    "number": c.number,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "roles": [h.verbatim_role for h in c.role_headings],
                    "last": (
                        None
                        if not c.headings
                        else {
                            "line": c.headings[-1].line_no,
                            "text": c.headings[-1].text,
                            "level": c.headings[-1].level,
                        }
                    ),
                }
                for c in report.cycles
            ],
            "merged": [
                {"line": h.line_no, "text": h.text, "level": h.level}
                for h in report.merged
            ],
            "critic_hits": [
                {"cycle": c, "line": n, "snippet": s} for c, n, s in report.critic_hits
            ],
        }
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    if args.report:
        args.report.write_text(render_markdown(report), encoding="utf-8")
        sys.stdout.write(f"wrote report {args.report}\n")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
