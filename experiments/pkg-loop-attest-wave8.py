#!/usr/bin/env python3
"""Unbounded reserve → mill → publish for package-release-factory attestation wave-8.

Unique mill path (never wave5/6/7 leftover mills).
Never steal a reserved round. If package-release is reserved, hop another
unreserved named factory that has a mill covering its frontier. Never hop
sandbox-refusal-factory. Writes only via round_txn.py reserve/publish.
Do not exit after one batch.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL8 = ROOT / "experiments" / "pkg-mill-attest-wave8.py"
MILL9 = ROOT / "experiments" / "pkg-mill-attest-wave9.py"
MILL10 = ROOT / "experiments" / "pkg-mill-attest-wave10.py"
MILL11 = ROOT / "experiments" / "pkg-mill-attest-wave11.py"
MILL12 = ROOT / "experiments" / "pkg-mill-attest-wave12.py"
MILL13 = ROOT / "experiments" / "pkg-mill-attest-wave13.py"
MILL14 = ROOT / "experiments" / "pkg-mill-attest-wave14.py"
MILL15 = ROOT / "experiments" / "pkg-mill-attest-wave15.py"
MILL16 = ROOT / "experiments" / "pkg-mill-attest-wave16.py"
MILL17 = ROOT / "experiments" / "pkg-mill-attest-wave17.py"
SSL_MILL_206 = ROOT / "experiments" / "ssl-mill-lll-r206.py"
SSL_MILL_286 = ROOT / "experiments" / "ssl-mill-lll-r286.py"
SSL_MILL = SSL_MILL_206
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "package-release-factory"
AGENTIC = FACTORY.parent
SKIP_HOP = {"eval-harness-trajectory-factory", "sandbox-refusal-factory"}

import importlib.util


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_w8 = _load(MILL8)
_w9 = _load(MILL9)
_w10 = _load(MILL10)
_w11 = _load(MILL11)
_w12 = _load(MILL12)
_w13 = _load(MILL13)
_w14 = _load(MILL14)
_w15 = _load(MILL15)
_w16 = _load(MILL16)
_w17 = _load(MILL17)
W8_FIRST = _w8.CATALOG_FIRST
W8_LAST = W8_FIRST + len(_w8.PAIRS) - 1
W9_FIRST = _w9.CATALOG_FIRST
W9_LAST = W9_FIRST + len(_w9.PAIRS) - 1
W10_FIRST = _w10.CATALOG_FIRST
W10_LAST = W10_FIRST + len(_w10.PAIRS) - 1
W11_FIRST = _w11.CATALOG_FIRST
W11_LAST = W11_FIRST + len(_w11.PAIRS) - 1
W12_FIRST = _w12.CATALOG_FIRST
W12_LAST = W12_FIRST + len(_w12.PAIRS) - 1
W13_FIRST = _w13.CATALOG_FIRST
W13_LAST = W13_FIRST + len(_w13.PAIRS) - 1
W14_FIRST = _w14.CATALOG_FIRST
W14_LAST = W14_FIRST + len(_w14.PAIRS) - 1
W15_FIRST = _w15.CATALOG_FIRST
W15_LAST = W15_FIRST + len(_w15.PAIRS) - 1
W16_FIRST = _w16.CATALOG_FIRST
W16_LAST = W16_FIRST + len(_w16.PAIRS) - 1
W17_FIRST = _w17.CATALOG_FIRST
W17_LAST = W17_FIRST + len(_w17.PAIRS) - 1
CATALOG_FIRST = W8_FIRST
CATALOG_LAST = W17_LAST

SSL_RANGES: list[tuple[int, int, Path]] = []
for _ssl_path in (SSL_MILL_206, SSL_MILL_286):
    if not _ssl_path.exists():
        continue
    _ssl = _load(_ssl_path)
    _first = _ssl.CATALOG_FIRST
    _last = _first + len(_ssl.PAIRS) - 1
    SSL_RANGES.append((_first, _last, _ssl_path))
SSL_FIRST = min((a for a, _, _ in SSL_RANGES), default=None)
SSL_LAST = max((b for _, b, _ in SSL_RANGES), default=None)


def mill_for(n: int) -> Path:
    if n >= W17_FIRST:
        return MILL17
    if n >= W16_FIRST:
        return MILL16
    if n >= W15_FIRST:
        return MILL15
    if n >= W14_FIRST:
        return MILL14
    if n >= W13_FIRST:
        return MILL13
    if n >= W12_FIRST:
        return MILL12
    if n >= W11_FIRST:
        return MILL11
    if n >= W10_FIRST:
        return MILL10
    if n >= W9_FIRST:
        return MILL9
    if n >= W8_FIRST:
        return MILL8
    raise SystemExit(f"r{n} outside attest catalog {W8_FIRST}+")


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def frontier(factory: Path) -> dict:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    return json.loads(proc.stdout)


def reserved_path(factory: Path, n: int) -> Path:
    return factory / f"ROUND-r{n:02d}.reserved.json"


def publish_round(
    factory: Path,
    mill: Path,
    n: int,
    expected: str = "2",
    extra: list[str] | None = None,
) -> None:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(factory),
            "--round",
            str(n),
            "--expected",
            expected,
        ]
    )
    payload = json.loads(proc.stdout)
    token, staging = payload["token"], payload["staging_dir"]
    print(f"reserved {factory.name} r{n} token={token}", flush=True)
    mill_cmd = [sys.executable, str(mill), "--round", str(n), "--staging", staging]
    if extra:
        mill_cmd.extend(extra)
    try:
        mill_out = run(mill_cmd)
        print(mill_out.stdout, flush=True)
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
    except subprocess.CalledProcessError as exc:
        print(exc.stdout or "", exc.stderr or "", flush=True)
        run(
            [
                sys.executable,
                str(TXN),
                "abort",
                str(factory),
                "--round",
                str(n),
                "--token",
                token,
            ],
            check=False,
        )
        raise


def hop_mill_for(factory: Path, n: int) -> Path | None:
    if factory.name == "ssl-cert-rotation-factory":
        for first, last, path in SSL_RANGES:
            if first <= n <= last:
                return path
    return None


def try_hop() -> str | None:
    hops = [AGENTIC / "ssl-cert-rotation-factory"]
    for hop in hops:
        if not hop.is_dir():
            continue
        if hop.name in SKIP_HOP:
            continue
        try:
            hs = frontier(hop)
        except Exception as exc:
            print(f"hop {hop.name} frontier failed: {exc}", flush=True)
            continue
        hn = hs["next_round"]
        if reserved_path(hop, hn).exists():
            print(f"hop {hop.name} r{hn} reserved; skip", flush=True)
            continue
        mill = hop_mill_for(hop, hn)
        if mill is None:
            print(
                f"hop {hop.name} r{hn} unreserved — no mill covering frontier; skip",
                flush=True,
            )
            continue
        print(f"hop {hop.name} r{hn} mill={mill.name}", flush=True)
        publish_round(hop, mill, hn)
        return f"{hop.name}-{hn}"
    return None


def main() -> int:
    done = 0
    published: list[str] = []
    used = set()
    fac_dir = FACTORY
    if fac_dir.exists():
        for path in fac_dir.glob("batch-r*.jsonl"):
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                pid = json.loads(line)["id"]
                prefix = "pkg-r"
                if pid.startswith(prefix):
                    rest = pid[len(prefix) :]
                    dash = rest.find("-")
                    if dash >= 0:
                        used.add(rest[dash + 1 :])
    w17_idx = 0
    while w17_idx < len(_w17.PAIRS):
        _, ok, _, fail = _w17.PAIRS[w17_idx]
        if ok["slug"] not in used and fail["slug"] not in used:
            break
        w17_idx += 1
    print(f"wave17 start idx={w17_idx} used_slugs={len(used)} pairs={len(_w17.PAIRS)}", flush=True)
    while True:
        status = frontier(FACTORY)
        n = status["next_round"]
        if w17_idx >= len(_w17.PAIRS):
            print(
                f"wave17 catalog exhausted at frontier {n} (pairs {len(_w17.PAIRS)})",
                flush=True,
            )
            break
        if n < W9_FIRST and n < W8_FIRST:
            print(f"frontier {n} below catalog {CATALOG_FIRST}; stop", flush=True)
            return 2
        if reserved_path(FACTORY, n).exists():
            print(f"package-release r{n} already reserved; hop", flush=True)
            hopped = try_hop()
            if hopped is None:
                print(
                    "all hops reserved or unimplemented; never steal; retry pkg frontier",
                    flush=True,
                )
                continue
            done += 1
            published.append(hopped)
            print(f"published hop {hopped} ({done})", flush=True)
            continue
        extra = ["--idx", str(w17_idx)]
        mill = mill_for(n)
        try:
            publish_round(FACTORY, mill, n, extra=extra)
        except subprocess.CalledProcessError as exc:
            text = (exc.stderr or "") + (exc.stdout or "")
            low = text.lower()
            if (
                "already" in low
                or "not the frontier" in low
                or "reservation path already exists" in low
            ):
                print("lost race or frontier moved; never steal; retry", flush=True)
                hopped = try_hop()
                if hopped is None:
                    time.sleep(0.35)
                    continue
                done += 1
                published.append(hopped)
                continue
            print("reserve/mill/publish failed", flush=True)
            print(text, flush=True)
            return 6
        done += 1
        published.append(f"pkg-{n}")
        w17_idx += 1
        print(f"published package-release r{n} idx={w17_idx} ({done})", flush=True)
    nxt = frontier(FACTORY)["next_round"]
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "pkg_frontier": nxt,
                "catalog_last": CATALOG_LAST,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
