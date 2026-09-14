#!/usr/bin/env python3
"""Unbounded reserve → mill → publish for package-release-factory attestation wave-6.

Unique mill path (never pkg-mill-r300.py / pkg-mill-attest-wave5.py).
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
MILL6 = ROOT / "experiments" / "pkg-mill-attest-wave6.py"
MILL7 = ROOT / "experiments" / "pkg-mill-attest-wave7.py"
SSL_MILL = ROOT / "experiments" / "ssl-mill-r35.py"
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


_w6 = _load(MILL6)
_w7 = _load(MILL7)
W6_FIRST = _w6.CATALOG_FIRST
W6_LAST = W6_FIRST + len(_w6.PAIRS) - 1
W7_FIRST = _w7.CATALOG_FIRST
W7_LAST = W7_FIRST + len(_w7.PAIRS) - 1
CATALOG_FIRST = W6_FIRST
CATALOG_LAST = W7_LAST

SSL_FIRST = SSL_LAST = None
if SSL_MILL.exists():
    _ssl = _load(SSL_MILL)
    SSL_FIRST = _ssl.CATALOG_FIRST
    SSL_LAST = SSL_FIRST + len(_ssl.PAIRS) - 1


def mill_for(n: int) -> Path:
    if W6_FIRST <= n <= W6_LAST:
        return MILL6
    if n >= W7_FIRST:
        return MILL7
    raise SystemExit(f"r{n} outside attest catalogs {W6_FIRST}+ / {W7_FIRST}+")


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
    if factory.name == "ssl-cert-rotation-factory" and SSL_FIRST is not None:
        if SSL_FIRST <= n <= SSL_LAST:
            return SSL_MILL
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
                    rest = pid[len(prefix):]
                    dash = rest.find("-")
                    if dash >= 0:
                        used.add(rest[dash + 1 :])
    w7_idx = 0
    while w7_idx < len(_w7.PAIRS):
        _, ok, _, fail = _w7.PAIRS[w7_idx]
        if ok["slug"] not in used and fail["slug"] not in used:
            break
        w7_idx += 1
    print(f"wave7 start idx={w7_idx} used_slugs={len(used)}", flush=True)
    while True:
        status = frontier(FACTORY)
        n = status["next_round"]
        if w7_idx >= len(_w7.PAIRS) and n > W6_LAST:
            print(
                f"wave7 catalog exhausted at frontier {n} (pairs {len(_w7.PAIRS)})",
                flush=True,
            )
            break
        if n < CATALOG_FIRST:
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
                time.sleep(0.35)
                continue
            done += 1
            published.append(hopped)
            print(f"published hop {hopped} ({done})", flush=True)
            continue
        extra = None
        mill = mill_for(n)
        if mill == MILL7:
            extra = ["--idx", str(w7_idx)]
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
        if mill == MILL7:
            w7_idx += 1
        print(f"published package-release r{n} idx={w7_idx} ({done})", flush=True)
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
