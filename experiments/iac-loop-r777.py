#!/usr/bin/env python3
"""Reserve → mill → publish infra-as-code-factory r1132+ until catalog or max.

If IAC reserved by us, mill that staging. If reserved by someone else, hop
another unreserved named factory. Never steal. Never sandbox-refusal if it is
reserved or writing. Never eval-harness.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "iac-mill-r1514.py"
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
FACTORY = AGENTIC / "infra-as-code-factory"


def load_mill():
    import importlib.util

    spec = importlib.util.spec_from_file_location("iac_mill_r1514", MILL)
    mill = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mill)
    return mill


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
    return json.loads(proc.stdout)["next_round"]


def reserved_payload(factory: Path, n: int) -> dict | None:
    path = factory / f"ROUND-r{n:02d}.reserved.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def sandbox_writing() -> bool:
    sbox = AGENTIC / "sandbox-refusal-factory"
    if not sbox.is_dir():
        return False
    n = frontier(sbox)
    return reserved_payload(sbox, n) is not None or any(sbox.glob("ROUND-r*.reserved.json"))


def hop_target() -> Path | None:
    skip = {
        FACTORY.resolve(),
        (AGENTIC / "eval-harness-trajectory-factory").resolve(),
    }
    if sandbox_writing():
        skip.add((AGENTIC / "sandbox-refusal-factory").resolve())
    for child in sorted(p for p in AGENTIC.iterdir() if p.is_dir()):
        if child.resolve() in skip:
            continue
        n = frontier(child)
        if reserved_payload(child, n) is not None:
            continue
        return child
    return None


def mill_and_publish(factory: Path, n: int, token: str, staging: str) -> None:
    mill_proc = run([sys.executable, str(MILL), "--round", str(n), "--staging", staging])
    sys.stdout.write(mill_proc.stdout or "")
    if mill_proc.stderr:
        sys.stderr.write(mill_proc.stderr)
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


def publish_existing_or_new(n: int) -> None:
    existing = reserved_payload(FACTORY, n)
    if existing is not None:
        print(
            f"using existing reservation r{n} token={existing['token']} staging={existing['staging_dir']}",
            flush=True,
        )
        try:
            mill_and_publish(FACTORY, n, existing["token"], existing["staging_dir"])
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            print(f"mill/publish failed for reserved r{n}; abort reservation", flush=True)
            run(
                [
                    sys.executable,
                    str(TXN),
                    "abort",
                    str(FACTORY),
                    "--round",
                    str(n),
                    "--token",
                    existing["token"],
                ],
                check=False,
            )
            raise
        return
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(FACTORY),
            "--round",
            str(n),
            "--expected",
            "2",
        ]
    )
    payload = json.loads(proc.stdout)
    token = payload["token"]
    staging = payload["staging_dir"]
    print(f"reserved r{n} token={token} staging={staging}", flush=True)
    try:
        mill_and_publish(FACTORY, n, token, staging)
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, exc.stderr, flush=True)
        print(f"mill/publish failed for r{n}; abort reservation", flush=True)
        run(
            [
                sys.executable,
                str(TXN),
                "abort",
                str(FACTORY),
                "--round",
                str(n),
                "--token",
                token,
            ],
            check=False,
        )
        raise


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    done = 0
    hops = 0
    published: list[int] = []
    mill = load_mill()
    while done < max_rounds:
        mill = load_mill()
        catalog_first = mill.CATALOG_FIRST
        catalog_len = len(mill.PAIRS)
        n = frontier(FACTORY)
        last = catalog_first + catalog_len - 1
        if n > last:
            print(f"catalog exhausted at frontier {n} (last {last})", flush=True)
            tgt = hop_target()
            if tgt is None:
                print("no unreserved hop target; stop", flush=True)
                break
            print(
                f"hop candidate {tgt.name} unreserved; IAC catalog exhausted; stop rather than idle",
                flush=True,
            )
            break
        existing = reserved_payload(FACTORY, n)
        if existing is not None:
            staging = Path(existing.get("staging_dir", ""))
            ours = staging.exists() and "infra-as-code-factory" in str(staging)
            if not ours:
                print(f"infra-as-code r{n} reserved by another mill; never steal", flush=True)
                hops += 1
                tgt = hop_target()
                if tgt is None:
                    print("no unreserved hop target; stop", flush=True)
                    break
                print(
                    f"hop candidate {tgt.name} unreserved; IAC reserved; stop rather than steal",
                    flush=True,
                )
                break
        try:
            publish_existing_or_new(n)
        except subprocess.CalledProcessError as exc:
            err = (exc.stderr or "") + (exc.stdout or "")
            if reserved_payload(FACTORY, n) is not None and "already reserved" in err:
                print("lost race on reserve; never steal", flush=True)
                return 6
            print("reserve/mill/publish failed", flush=True)
            print(err, flush=True)
            return 7
        done += 1
        published.append(n)
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "hops": hops,
                "frontier": frontier(FACTORY),
                "catalog_last": mill.CATALOG_FIRST + len(mill.PAIRS) - 1,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
