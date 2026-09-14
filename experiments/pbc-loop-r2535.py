#!/usr/bin/env python3
"""Reserve → mill → publish proto-breaking-change-factory from r2535.

Never steal. Never rewrite raw. Stop on foreign reservation, two consecutive
NOTES under 5% novel coverage, or 26 successful publishes this window.
Does not hop factories.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "pbc-mill-r2535.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "proto-breaking-change-factory"
COVERAGE_RE = re.compile(
    r"^\s*novel[ _-]?coverage\s*(?:\([^)\n]*\))?\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE | re.MULTILINE,
)
COMPLETE_RE = re.compile(r"^ROUND-r(\d+)\.complete\.json$")


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def next_round_fast(factory: Path) -> int:
    highest = 0
    for path in factory.glob("ROUND-r*.complete.json"):
        match = COMPLETE_RE.match(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def reserved(factory: Path, n: int) -> bool:
    round_dir = factory / f"r{n:02d}"
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists() or (
        round_dir / "ROUND.reserved.json"
    ).exists()


def writing(factory: Path) -> bool:
    return (
        any(factory.glob("ROUND-r*.reserved.json"))
        or any(factory.glob("ROUND-r*.publishing.json"))
        or any(factory.glob("r*/ROUND.reserved.json"))
    )


def notes_coverage(factory: Path, n: int) -> float | None:
    path = factory / f"NOTES-r{n:02d}.md"
    if not path.is_file():
        return None
    match = COVERAGE_RE.search(path.read_text())
    if match is None:
        return None
    return float(match.group(1))


def publish_one(factory: Path, n: int) -> None:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(factory),
            "--round",
            str(n),
            "--expected",
            "2",
        ]
    )
    payload = json.loads(proc.stdout)
    print(proc.stdout, flush=True)
    token = payload["token"]
    staging = payload["staging_dir"]
    print(f"reserved r{n} token={token} staging={staging}", flush=True)
    mill_proc = run([sys.executable, str(MILL), "--round", str(n), "--staging", staging])
    sys.stderr.write(mill_proc.stderr or "")
    print(mill_proc.stdout, flush=True)
    last_exc: subprocess.CalledProcessError | None = None
    for attempt in range(1, 4):
        try:
            pub = run(
                [
                    sys.executable,
                    str(TXN),
                    "publish",
                    str(factory),
                    "--round",
                    str(n),
                    "--token",
                    token,
                ]
            )
            print(pub.stdout, flush=True)
            last_exc = None
            break
        except subprocess.CalledProcessError as exc:
            last_exc = exc
            text = f"{exc.stdout or ''}{exc.stderr or ''}"
            print(exc.stdout, exc.stderr, flush=True)
            if "already complete" in text or "already exists" in text:
                print(f"r{n} already published; continue", flush=True)
                last_exc = None
                break
            print(f"publish r{n} attempt {attempt}/3 failed; retry", flush=True)
    if last_exc is not None:
        raise last_exc


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 26
    done = 0
    published: list[int] = []
    low_streak = 0
    while done < max_rounds:
        n = next_round_fast(FACTORY)
        if reserved(FACTORY, n) or writing(FACTORY):
            print(
                json.dumps(
                    {
                        "stop": "foreign_reservation",
                        "round": n,
                        "published": published,
                    }
                ),
                flush=True,
            )
            return 2
        try:
            publish_one(FACTORY, n)
        except subprocess.CalledProcessError as exc:
            text = f"{exc.stdout or ''}{exc.stderr or ''}"
            print(exc.stdout, exc.stderr, flush=True)
            if "already exists" in text or "is not the frontier" in text:
                print("lost race; retry next frontier", flush=True)
                continue
            if reserved(FACTORY, n):
                print("mill/publish failed with our seat held", flush=True)
                return 4
            print("reserve/mill/publish failed; stop", flush=True)
            return 3
        done += 1
        published.append(n)
        cov = notes_coverage(FACTORY, n)
        print(
            f"published r{n} ({done}/{max_rounds}) coverage={cov}",
            flush=True,
        )
        if cov is not None and cov < 5:
            low_streak += 1
        else:
            low_streak = 0
        if low_streak >= 2:
            print(
                json.dumps(
                    {
                        "stop": "coverage_streak",
                        "published": published,
                    }
                ),
                flush=True,
            )
            break
    print(json.dumps({"published": done, "rounds": published}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
