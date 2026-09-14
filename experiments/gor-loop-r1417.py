#!/usr/bin/env python3
"""Reserve → mill → publish git-ops-recovery-factory until catalog or quota.

Never steal. Never rewrite raw. If git-ops is reserved by another writer, hop
another unreserved named factory. Never hop sandbox-refusal if it is reserved
or writing. Never hop eval-harness.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "gor-mill-r1417.py"
QBP_MILL = ROOT / "experiments" / "qbp-mill-leftover-lll-r77.py"
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
FACTORY = AGENTIC / "git-ops-recovery-factory"
SBOX = AGENTIC / "sandbox-refusal-factory"
EVALH = AGENTIC / "eval-harness-trajectory-factory"
FACTORY_EXPECTED = {
    "git-ops-recovery-factory": 2,
    "queue-backpressure-factory": 2,
    "email-webhook-retry-factory": 2,
    "rate-limit-backoff-factory": 2,
    "csv-excel-ingest-factory": 2,
    "mcp-tool-schema-drift-factory": 2,
}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def frontier(factory: Path) -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)["next_round"]


def reserved_payload(factory: Path, n: int) -> dict | None:
    for path in (
        factory / f"ROUND-r{n:02d}.reserved.json",
        factory / f"ROUND-r{n}.reserved.json",
    ):
        if path.exists():
            return json.loads(path.read_text())
    return None


def reserved(factory: Path, n: int) -> bool:
    return reserved_payload(factory, n) is not None


def mill_for(factory: Path) -> Path | None:
    if factory.name == FACTORY.name:
        return MILL
    if factory.name == "queue-backpressure-factory" and QBP_MILL.is_file():
        return QBP_MILL
    return None


def staging_kind(payload: dict) -> str:
    stag = Path(payload["staging_dir"])
    batch = stag / payload.get("batch_file", f"batch-r{payload['round']}.jsonl")
    if not batch.is_file() or batch.stat().st_size == 0:
        return "empty"
    text = batch.read_text()[:4000]
    if "gor-r" in text and "git-ops-recovery-factory" in text:
        return "gor"
    if '"id":"gor-r' in text or '"id": "gor-r' in text:
        return "gor"
    return "invalid"


def sandbox_busy() -> bool:
    if not SBOX.is_dir():
        return False
    n = frontier(SBOX)
    return reserved(SBOX, n) or any(SBOX.glob("ROUND-r*.reserved.json"))


def unused_count() -> int:
    gor = load(MILL, "gor_mill_r1417")
    return gor.unused_count()


def mill_publish(factory: Path, n: int, mill: Path, token: str, staging: str) -> None:
    print(f"mill {factory.name} r{n} token={token}", flush=True)
    try:
        mill_proc = run(
            [
                sys.executable,
                str(mill),
                "--round",
                str(n),
                "--staging",
                staging,
            ]
        )
        sys.stderr.write(mill_proc.stderr or "")
        print(mill_proc.stdout, flush=True)
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
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, exc.stderr, flush=True)
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
    print(pub.stdout, flush=True)


def publish_existing(factory: Path, n: int, token: str) -> None:
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


def publish_one(factory: Path, n: int, mill: Path, expected: int = 2) -> None:
    existing = reserved_payload(factory, n)
    if existing is not None:
        kind = staging_kind(existing)
        token = existing["token"]
        staging = existing["staging_dir"]
        if factory.resolve() == FACTORY.resolve() and kind == "gor":
            print(f"r{n} staging valid GOR; publish", flush=True)
            publish_existing(factory, n, token)
            return
        if factory.resolve() == FACTORY.resolve() and kind in ("empty", "invalid"):
            print(f"r{n} staging {kind}; remill GOR token={token}", flush=True)
            mill_publish(factory, n, mill, token, staging)
            return
        if kind != "empty":
            raise subprocess.CalledProcessError(1, ["occupied"], "", "occupied staging")
        mill_publish(factory, n, mill, token, staging)
        return
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(factory),
            "--round",
            str(n),
            "--expected",
            str(expected),
        ]
    )
    print(proc.stdout, flush=True)
    payload = json.loads(proc.stdout)
    token = payload["token"]
    staging = payload["staging_dir"]
    print(f"reserved {factory.name} r{n} token={token}", flush=True)
    mill_publish(factory, n, mill, token, staging)


def hop_target() -> tuple[Path, Path] | None:
    skip = {FACTORY.resolve(), EVALH.resolve()}
    if sandbox_busy():
        skip.add(SBOX.resolve())
    preferred = [
        AGENTIC / "queue-backpressure-factory",
        AGENTIC / "email-webhook-retry-factory",
        AGENTIC / "rate-limit-backoff-factory",
        AGENTIC / "csv-excel-ingest-factory",
        AGENTIC / "mcp-tool-schema-drift-factory",
    ]
    ordered = [p for p in preferred if p.is_dir()] + [
        p for p in sorted(AGENTIC.iterdir()) if p.is_dir() and p not in preferred
    ]
    for factory in ordered:
        if factory.resolve() in skip:
            continue
        mill = mill_for(factory)
        if mill is None:
            continue
        n = frontier(factory)
        if reserved(factory, n):
            continue
        return factory, mill
    return None


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    done = 0
    hops = 0
    published: list[str] = []

    while done < max_rounds:
        n = frontier(FACTORY)
        payload = reserved_payload(FACTORY, n)
        if payload is not None:
            kind = staging_kind(payload)
            token = payload["token"]
            if kind == "gor":
                try:
                    publish_existing(FACTORY, n, token)
                except subprocess.CalledProcessError as exc:
                    print(exc.stdout, exc.stderr, flush=True)
                    print("lost race on valid staging; hop", flush=True)
                    hop = hop_target()
                    if hop is None:
                        continue
                    hf, hm = hop
                    hn = frontier(hf)
                    try:
                        publish_one(hf, hn, hm, expected=FACTORY_EXPECTED.get(hf.name, 2))
                    except subprocess.CalledProcessError:
                        continue
                    hops += 1
                    published.append(f"{hf.name}-{hn}")
                    done += 1
                    continue
                done += 1
                published.append(f"gor-{n}")
                print(f"published git-ops r{n} ({done}/{max_rounds})", flush=True)
                continue
            if kind in ("empty", "invalid"):
                print(f"r{n} reserved empty/invalid; mill GOR token={token}", flush=True)
                try:
                    mill_publish(FACTORY, n, MILL, token, payload["staging_dir"])
                except subprocess.CalledProcessError as exc:
                    print(exc.stdout, exc.stderr, flush=True)
                    hop = hop_target()
                    if hop is None:
                        continue
                    continue
                done += 1
                published.append(f"gor-{n}")
                print(f"published git-ops r{n} ({done}/{max_rounds})", flush=True)
                continue
            print(f"git-ops r{n} occupied token={token[:8]} kind={kind}; hop", flush=True)
            hop = hop_target()
            if hop is None:
                print("hop unavailable; never steal; retry git-ops", flush=True)
                continue
            hf, hm = hop
            hn = frontier(hf)
            try:
                publish_one(hf, hn, hm, expected=FACTORY_EXPECTED.get(hf.name, 2))
            except subprocess.CalledProcessError:
                print(
                    f"hop mill/publish failed for {hf.name} r{hn}; never steal; retry git-ops",
                    flush=True,
                )
                continue
            hops += 1
            published.append(f"{hf.name}-{hn}")
            done += 1
            print(f"published {hf.name} r{hn} ({done}/{max_rounds})", flush=True)
            continue
        try:
            publish_one(FACTORY, n, MILL, expected=2)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            err = (exc.stderr or "") + (exc.stdout or "")
            if "occupied staging" in err or reserved(FACTORY, n):
                print("lost race on reserve; never steal; hop next", flush=True)
                continue
            if "no unused unique pair" in err:
                print("catalog empty; hop", flush=True)
                hop = hop_target()
                if hop is None:
                    print("no unused unique pairs and hop unavailable; stop", flush=True)
                    break
                continue
            print("reserve/mill/publish failed", flush=True)
            return 5
        done += 1
        published.append(f"gor-{n}")
        print(f"published git-ops r{n} ({done}/{max_rounds})", flush=True)
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "hops": hops,
                "frontier": frontier(FACTORY),
                "unused_pairs": unused_count(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
