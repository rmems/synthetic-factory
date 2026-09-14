#!/usr/bin/env python3
"""Reserve → mill → publish git-ops-recovery-factory until catalog or quota.

Never steal. Never rewrite raw. If git-ops is reserved, hop another
unreserved named factory (infra-as-code, then graphql-nplusone).
Never hop sandbox-refusal if it is reserved or writing.
Never hop eval-harness.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "gor-mill-r1127.py"
IAC_MILL = ROOT / "experiments" / "iac-mill-r709.py"
GQL_MILL = ROOT / "experiments" / "gql-mill-r216.py"
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
FACTORY = AGENTIC / "git-ops-recovery-factory"
HOP_IAC = AGENTIC / "infra-as-code-factory"
HOP_GQL = AGENTIC / "graphql-nplusone-factory"
SBOX = AGENTIC / "sandbox-refusal-factory"
EVALH = AGENTIC / "eval-harness-trajectory-factory"


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


def staging_empty(payload: dict) -> bool:
    stag = Path(payload["staging_dir"])
    if not stag.is_dir():
        return True
    return not any(stag.iterdir())


def sandbox_busy() -> bool:
    if not SBOX.is_dir():
        return False
    n = frontier(SBOX)
    return reserved(SBOX, n) or any(SBOX.glob("ROUND-r*.reserved.json"))


def unused_count() -> int:
    gor = load(MILL, "gor_mill_r1127")
    used = gor._published_slugs()
    return sum(
        1
        for a, b in gor.PAIRS
        if a["slug"] not in used and b["slug"] not in used
    )


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


def publish_one(factory: Path, n: int, mill: Path, expected: int = 2) -> None:
    existing = reserved_payload(factory, n)
    if existing is not None:
        if not staging_empty(existing):
            raise subprocess.CalledProcessError(1, ["occupied"], "", "occupied staging")
        mill_publish(
            factory, n, mill, existing["token"], existing["staging_dir"]
        )
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
    for factory, mill in ((HOP_IAC, IAC_MILL), (HOP_GQL, GQL_MILL)):
        if factory.resolve() in skip:
            continue
        if not factory.is_dir() or not mill.is_file():
            continue
        n = frontier(factory)
        if reserved(factory, n):
            continue
        return factory, mill
    return None


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    done = 0
    hops = 0
    published: list[str] = []

    while done < max_rounds:
        n = frontier(FACTORY)
        payload = reserved_payload(FACTORY, n)
        if payload is not None and not staging_empty(payload):
            print(f"git-ops r{n} occupied; hop", flush=True)
            hop = hop_target()
            if hop is None:
                print("hop unavailable; never steal; retry git-ops", flush=True)
                continue
            hf, hm = hop
            hn = frontier(hf)
            try:
                publish_one(hf, hn, hm, expected=2)
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
