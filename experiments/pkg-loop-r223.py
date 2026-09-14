#!/usr/bin/env python3
"""Reserve → mill → publish leftover SBOM/license rounds on package-release-factory."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL_223 = ROOT / "experiments" / "pkg-mill-r223.py"
MILL_239 = ROOT / "experiments" / "pkg-mill-r239.py"
SSL_MILL = ROOT / "experiments" / "ssl-mill-r27.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "package-release-factory"
SSL = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "ssl-cert-rotation-factory"

import importlib.util


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_m223 = _load(MILL_223)
_m239 = _load(MILL_239)
_ssl = _load(SSL_MILL)
CATALOG_FIRST = _m223.CATALOG_FIRST
CATALOG_LAST = _m239.CATALOG_FIRST + len(_m239.PAIRS) - 1
SSL_FIRST = _ssl.CATALOG_FIRST
SSL_LAST = SSL_FIRST + len(_ssl.PAIRS) - 1


def mill_for(n: int) -> Path:
    if n >= _m239.CATALOG_FIRST:
        return MILL_239
    return MILL_223


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
    proc = run([sys.executable, TXN, "frontier", factory])
    return json.loads(proc.stdout)


def reserved_path(factory: Path, n: int) -> Path:
    return factory / f"ROUND-r{n:02d}.reserved.json"


def publish_round(factory: Path, mill: Path, n: int, expected: str = "2") -> None:
    proc = run([sys.executable, TXN, "reserve", factory, "--round", str(n), "--expected", expected])
    payload = json.loads(proc.stdout)
    token, staging = payload["token"], payload["staging_dir"]
    print(f"reserved {factory.name} r{n} token={token}", flush=True)
    try:
        mill_out = run([sys.executable, mill, "--round", str(n), "--staging", staging])
        print(mill_out.stdout, flush=True)
        pub = run([sys.executable, TXN, "publish", factory, "--round", str(n), "--token", token])
        print(pub.stdout, flush=True)
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, exc.stderr, flush=True)
        run([sys.executable, TXN, "abort", factory, "--round", str(n), "--token", token], check=False)
        raise


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    done = 0
    published: list[str] = []
    while done < max_rounds:
        status = frontier(FACTORY)
        n = status["next_round"]
        if n > CATALOG_LAST:
            print(f"catalog exhausted at frontier {n} (last {CATALOG_LAST})", flush=True)
            break
        if reserved_path(FACTORY, n).exists():
            print(f"package-release r{n} already reserved; hop ssl if free", flush=True)
            hs = frontier(SSL)
            hn = hs["next_round"]
            if reserved_path(SSL, hn).exists():
                print(f"ssl r{hn} reserved; never steal; stop", flush=True)
                return 3
            if hn > SSL_LAST:
                print(f"ssl catalog exhausted at {hn} (last {SSL_LAST}); never steal; stop", flush=True)
                return 3
            try:
                publish_round(SSL, SSL_MILL, hn)
            except subprocess.CalledProcessError:
                return 6
            done += 1
            published.append(f"ssl-{hn}")
            print(f"published ssl r{hn} ({done}/{max_rounds})", flush=True)
            continue
        try:
            publish_round(FACTORY, mill_for(n), n)
        except subprocess.CalledProcessError as exc:
            if reserved_path(FACTORY, n).exists() and "already reserved" in (exc.stderr or "") + (exc.stdout or ""):
                print("lost race on reserve; never steal", flush=True)
                return 4
            return 6
        done += 1
        published.append(f"pkg-{n}")
        print(f"published package-release r{n} ({done}/{max_rounds})", flush=True)
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
