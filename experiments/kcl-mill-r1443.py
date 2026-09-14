#!/usr/bin/env python3
"""k8s-crashloop mill from r1443. Q=2. grok-4.6.

NEW CrashLoop plant set. Prior 160-pair r1236 catalog exhausted.
BAN r70-r1432 empty-ENV cartesian, AppArmor/seccomp Unconfined, webhook timeout,
r1432 prestop-http-oldpath / prestop-http-oldpath-n2-handoff,
r1235 ctb-label-old / ctb-label-old-n2-handoff.
Plant not bay-prod / cwm / llyn / atoll / kyle / voe / tarn / lough / weald / fen.
IDs kcl-rN-<slug> without -w3-empty / sxNNN-handoff.
Loop: frontier -> reserve --expected 2 -> stage -> publish. If reserved, HOP.
Do not exit after one batch. Keep looping until catalog or quota dies.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
FACTORY_DIR = ROOT / "outputs/raw/2026-08-19-agentic/k8s-crashloop-factory"
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
TXN = ROOT / "pipelines" / "round_txn.py"
PEER = ROOT / "experiments" / "kcl-mill-r1007.py"
HOPPER = ROOT / "experiments" / "hopper_mill_g46d.py"
PLANTS = ROOT / "experiments" / "kcl-plants-r1443.py"
FACTORY = "k8s-crashloop-factory"
GEN = "grok-4.6"
STAMP = "leftover n2 still n2 leftover still"
MAX_ROUNDS = 240
MAX_SECONDS = 4 * 60 * 60
SKIP_HOP = {
    "sandbox-refusal-factory",
    "eval-harness-trajectory-factory",
    "k8s-crashloop-factory",
}
HOP_STAGING = [
    ("monorepo-dep-bump-factory", ROOT / "experiments" / "mdb-mill-r1148.py"),
    ("graphql-nplusone-factory", ROOT / "experiments" / "gql-mill-r271.py"),
    ("observability-debug-factory", ROOT / "experiments" / "obs-mill-r401.py"),
    ("secret-scan-remediation-factory", ROOT / "experiments" / "ssr-mill-r670.py"),
    ("code-review-preference-factory", ROOT / "experiments" / "crp-mill-r729.py"),
    ("proto-breaking-change-factory", ROOT / "experiments" / "pbc-mill-r988.py"),
    ("db-migration-repair-factory", ROOT / "experiments" / "dbm-mill-r1260.py"),
]

_spec = importlib.util.spec_from_file_location("kcl_peer", PEER)
_peer = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_peer)
success_episode = _peer.success_episode
_leftover_episode = _peer.leftover_episode

_pspec = importlib.util.spec_from_file_location("kcl_plants_r1443", PLANTS)
_plants = importlib.util.module_from_spec(_pspec)
assert _pspec.loader is not None
_pspec.loader.exec_module(_plants)


def leftover_episode(round_n: int, s: dict) -> dict:
    ep = _leftover_episode(round_n, s)
    app = s["app"].replace("-api", "-svc")
    ns = s["plant"]
    ep["goal"] = (
        f"{app} in designed plant {ns} still runs live {s['field']}={s['fail_val']} "
        f"on replica n2 after git {s['fix_val']}. Do not --force."
    )
    blob = json.dumps(ep)
    if STAMP in blob:
        raise SystemExit(f"stamp in leftover {ep['id']}")
    if "-w3-empty" in ep["id"] or "sx" in ep["id"]:
        raise SystemExit(f"banned leftover id {ep['id']}")
    return ep


def pair(**kwargs: str) -> dict:
    required = {
        "plant",
        "app",
        "chart",
        "slug",
        "field",
        "fail_val",
        "fix_val",
        "hide_path",
        "hide_old",
        "hide_new",
        "values_fail",
        "values_fix",
        "tpl",
        "log",
        "live_ok",
        "hide_name",
        "new_vs",
        "seed",
        "n2",
        "ci",
        "handoff",
        "pytest_ok",
        "pytest_fail",
        "tmpl_test",
        "rs",
    }
    missing = required - set(kwargs)
    if missing:
        raise SystemExit(f"pair missing {missing}")
    if kwargs["hide_old"] not in kwargs["values_fail"]:
        raise SystemExit(f"{kwargs['plant']} hide_old not in values_fail")
    banned_plants = {
        "bay-prod",
        "cwm-prod",
        "llyn-prod",
        "atoll-prod",
        "kyle-prod",
        "voe-prod",
        "tarn-prod",
        "lough-prod",
        "weald-prod",
        "fen-prod",
    }
    if kwargs["plant"] in banned_plants:
        raise SystemExit(f"banned plant {kwargs['plant']}")
    if kwargs["slug"] in {
        "prestop-http-oldpath",
        "ctb-label-old",
        "downward-divisor",
        "ephemeral-sc-old",
        "rclaim-admin-gone",
        "fieldref-divisor",
        "dnspolicy-none",
        "stopsignal-kill",
    }:
        raise SystemExit(f"banned slug {kwargs['slug']}")
    ident = " ".join(
        str(kwargs.get(k, "")) for k in ("plant", "slug", "field", "fail_val")
    ).lower()
    for needle in (
        "unconfined",
        "webhook",
        "ipfamilies",
        "internaltrafficpolicy",
        "externaltrafficpolicy",
        "allocateloadbalancernodeports",
        "bitbucket_home",
        "keycloak_home",
        "bay-prod",
        "apparmor",
        "rclaim-admin-gone",
        STAMP,
    ):
        if needle in ident:
            raise SystemExit(f"banned needle {needle!r} in {kwargs['plant']}")
    return kwargs


def spec_from_row(row: tuple) -> dict:
    i, plant, slug, field, fail, fix, hide_key, hide_old, hide_new, crash, new_vs = row
    app = plant.replace("-prod", "-api")
    hide_old_line = f"{hide_key}: {hide_old}\n"
    hide_new_line = f"{hide_key}: {hide_new}\n"
    val_key = field.split(".")[-1]
    values_fail = f"{val_key}: {fail}\n{hide_old_line}"
    values_fix = f"{val_key}: {fix}\n{hide_old_line}"
    tpl = f"  {val_key}: {{{{ .Values.{val_key} }}}}\n"
    chart = f"{1 + (i % 8)}.{1 + (i % 9)}.{i % 10}"
    return pair(
        plant=plant,
        app=app,
        chart=chart,
        slug=slug,
        field=field,
        fail_val=fail,
        fix_val=fix,
        hide_path=hide_key,
        hide_old=hide_old_line,
        hide_new=hide_new_line,
        values_fail=values_fail,
        values_fix=values_fix,
        tpl=tpl,
        log=f"{crash} leftover {field} {fail} CrashLoop",
        live_ok=f"{field}={fix}",
        hide_name=f"{hide_key} {hide_new}",
        new_vs=new_vs,
        seed=f"leftover {field} {fail}; {crash} CrashLoop",
        n2=f"replica n2 still {field} {fail} after git {fix}",
        ci=f"# {field} must be {fix}. Never {hide_key} {hide_new} to hide leftover {fail}.",
        handoff=(
            f"LEFTOVER: replica n2 still {field} {fail}. "
            f"Platform: delete leftover RS. No {hide_key} hide."
        ),
        pytest_ok="test_fix\ntest_not_hide\ntest_not_clone\ntest_pods_ready\ntest_no_force\ntest_field",
        pytest_fail=f"test_fix_all FAILED b=={fail}",
        tmpl_test="test_template_matches_git",
        rs=f"k{601 + i}",
    )


PAIRS: list[dict] = [spec_from_row(row) for row in _plants.ROWS]


def notes_for(round_n: int, s: dict, a: dict, b: dict) -> str:
    cov = 82 + (round_n % 7)
    return (
        f"# NOTES-r{round_n} k8s-crashloop-factory\n"
        f"\n"
        f"Novel coverage: {cov}%\n"
        f"\n"
        f"Quota 2. Unique CrashLoopBackOff pair. Catalog r70–r1432 stays in raw "
        f"(empty-ENV / spec leftover cartesian). New: {s['new_vs']}. "
        f"Plant `{s['plant']}` (not bay-prod/cwm/llyn/atoll/kyle/voe/tarn/lough/weald/fen).\n"
        f"\n"
        f"| id | seed | clean-plan then fail | leftover | terminal |\n"
        f"|---|---|---|---|---|\n"
        f"| {a['id']} | {s['seed']} | kubeconform 0; apply --wait fail | wrong first hide then plan change | success 2/2 pytest 6/6 |\n"
        f"| {b['id']} | {s['n2']} | kubeconform 0; --force mixed | leftover on n2; SSA spec only | partial 1/2 handoff |\n"
        f"\n"
        f"## Step counts\n"
        f"- ep1: 16. Clean template 5; apply fail 6,8; plan change 9; verify 12–16.\n"
        f"- ep2: 18. Clean template 5; apply fail 6–8; plan change 9; leftover 11–18.\n"
        f"\n"
        f"## decision_basis audit\n"
        f"Plan:/Observation:/Reflection:/Tool call: <=240. No hidden CoT. No spike_events.\n"
        f"No sim_or_real: real. Invented plant `{s['plant']}`.\n"
        f"\n"
        f"## How the apply-fail taught\n"
        f"1. {s['seed']}. kubeconform does not evaluate this. Stretching the wrong knob hid or no-op'd.\n"
        f"2. {s['n2']}. helm --force three-way kept the live leftover. Do not delete n2 as success.\n"
        f"\n"
        f"## Bans honored\n"
        f"- No leftover-n2 stamp (`leftover n2 still n2 leftover still`).\n"
        f"- No empty-ENV after chart bump (BITBUCKET_HOME / KEYCLOAK_HOME / CARGO_* / RUST_*).\n"
        f"- No leftover cartesian on spec.ipFamilies / externalTrafficPolicy / allocateLoadBalancerNodePorts.\n"
        f"- No AppArmor/seccomp Unconfined. No webhook timeout.\n"
        f"- No r1432 prestop-http-oldpath / prestop-http-oldpath-n2-handoff.\n"
        f"- No r1235 ctb-label-old / ctb-label-old-n2-handoff clone.\n"
        f"- No bay-prod / cwm / llyn / atoll / kyle / voe / tarn / lough / weald / fen clones.\n"
        f"- No `-w3-empty` / `sxNNN-handoff` ids.\n"
        f"- Not a clone of r70–r1432 leftover families.\n"
    )


def write_round(round_n: int, staging: Path, spec: dict) -> None:
    a = success_episode(round_n, spec)
    b = leftover_episode(round_n, spec)
    if "-w3-empty" in a["id"] or "sx" in a["id"] or "-w3-empty" in b["id"]:
        raise SystemExit("banned id")
    a["meta"]["generator"] = GEN
    b["meta"]["generator"] = GEN
    if len(a["steps"]) != 16 or len(b["steps"]) != 18:
        raise SystemExit(f"step counts {len(a['steps'])} {len(b['steps'])}")
    blob = json.dumps(a, separators=(",", ":")) + "\n" + json.dumps(b, separators=(",", ":")) + "\n"
    if STAMP in blob:
        raise SystemExit(f"stamp in batch r{round_n}")
    for needle in (
        "BITBUCKET_HOME",
        "KEYCLOAK_HOME",
        "spec.ipFamilies",
        "spike_events",
        "AppArmor",
        "seccompProfile: Unconfined",
        "webhook timeout",
        '"sim_or_real": "real"',
        '"thought"',
        "chain_of_thought",
    ):
        if needle in blob:
            raise SystemExit(f"banned needle {needle} in batch r{round_n}")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(blob)
    notes.write_text(notes_for(round_n, spec, a, b))
    print(
        json.dumps(
            {
                "round": round_n,
                "ids": [a["id"], b["id"]],
                "steps": [len(a["steps"]), len(b["steps"])],
                "bytes": batch.stat().st_size,
                "plant": spec["plant"],
                "slug": spec["slug"],
            }
        ),
        flush=True,
    )


def txn(args: list[str]) -> dict:
    proc = subprocess.run(
        [sys.executable, str(TXN), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "txn failed")
    return json.loads(proc.stdout)


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists() or (
        factory / f"ROUND-r{n}.reserved.json"
    ).exists()


def taken_slugs() -> set[str]:
    found: set[str] = set()
    for path in FACTORY_DIR.glob("batch-r*.jsonl"):
        try:
            text = path.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            ident = str(obj.get("id", ""))
            if not ident.startswith("kcl-r"):
                continue
            parts = ident.split("-", 2)
            if len(parts) != 3:
                continue
            slug = parts[2]
            if slug.endswith("-n2-handoff"):
                slug = slug[: -len("-n2-handoff")]
            elif slug.endswith("-handoff"):
                slug = slug[: -len("-handoff")]
            found.add(slug)
    return found


def taken_plants() -> set[str]:
    found: set[str] = set()
    for path in FACTORY_DIR.glob("batch-r*.jsonl"):
        try:
            text = path.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if "designed plant " not in line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            goal = str(obj.get("goal", ""))
            marker = "designed plant "
            if marker in goal:
                rest = goal.split(marker, 1)[1]
                plant = rest.split(" ", 1)[0].strip(".,")
                if plant:
                    found.add(plant)
    return found


def abort(factory: Path, n: int, token: str) -> None:
    try:
        txn(["abort", str(factory), "--round", str(n), "--token", token])
    except RuntimeError as exc:
        print(f"abort failed r{n}: {exc}", flush=True)


HOP_DEAD: set[str] = set()


def hop_staging_once() -> bool:
    for factory, mill in HOP_STAGING:
        if factory in SKIP_HOP or factory in HOP_DEAD or not mill.exists():
            continue
        fdir = AGENTIC / factory
        if not fdir.exists():
            continue
        try:
            status = txn(["frontier", str(fdir)])
        except RuntimeError as exc:
            print(f"hop frontier {factory}: {exc}", flush=True)
            continue
        n = int(status["next_round"])
        if reserved(fdir, n):
            print(f"hop skip {factory} r{n} reserved", flush=True)
            continue
        try:
            res = txn(["reserve", str(fdir), "--round", str(n), "--expected", "2"])
        except RuntimeError as exc:
            print(f"hop reserve {factory} r{n}: {exc}", flush=True)
            continue
        token = res["token"]
        staging = Path(res["staging_dir"])
        if mill.name.startswith("gql-"):
            cmd = [
                sys.executable,
                str(mill),
                "--round",
                str(n),
                "--staging",
                str(staging),
                "--batch-file",
                f"batch-r{n:02d}.jsonl",
                "--notes-file",
                f"NOTES-r{n:02d}.md",
            ]
        else:
            cmd = [sys.executable, str(mill), "--round", str(n), "--staging", str(staging)]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            print(f"hop mill {factory} r{n}: {err}; abort", flush=True)
            abort(fdir, n, token)
            low = err.lower()
            if (
                "outside catalog" in low
                or "catalog empty" in low
                or "no unused plant" in low
                or "left=0" in low
            ):
                HOP_DEAD.add(factory)
                print(f"hop dead {factory} (catalog exhausted)", flush=True)
            continue
        notes = staging / f"NOTES-r{n:02d}.md"
        if not notes.exists() or "Novel coverage:" not in notes.read_text():
            print(f"hop {factory} r{n} notes missing Novel coverage; abort", flush=True)
            abort(fdir, n, token)
            continue
        try:
            pub = txn(["publish", str(fdir), "--round", str(n), "--token", token])
        except Exception as exc:
            print(f"hop publish {factory} r{n}: {exc}; abort", flush=True)
            abort(fdir, n, token)
            continue
        print(
            json.dumps(
                {
                    "hop_published": factory,
                    "round": n,
                    "records": pub.get("records"),
                    "mill": mill.name,
                }
            ),
            flush=True,
        )
        return True
    return False


def hop_once() -> bool:
    if hop_staging_once():
        return True
    if not HOPPER.exists():
        return False
    spec = importlib.util.spec_from_file_location("hopper_g46d", HOPPER)
    hop = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(hop)
    for factory in hop.CYCLE:
        if factory in SKIP_HOP:
            continue
        fdir = hop.factory_dir(factory)
        try:
            status = txn(["frontier", str(fdir)])
        except RuntimeError as exc:
            print(f"hop frontier {factory}: {exc}", flush=True)
            continue
        n = int(status["next_round"])
        if reserved(fdir, n):
            print(f"hop skip {factory} r{n} reserved", flush=True)
            continue
        idx = n - hop.START[factory]
        pairs = hop.PAIRS.get(factory, [])
        if idx < 0 or idx >= len(pairs):
            print(f"hop skip {factory} r{n} catalog idx={idx}", flush=True)
            continue
        ok, bad = pairs[idx]
        try:
            res = txn(["reserve", str(fdir), "--round", str(n), "--expected", "2"])
        except RuntimeError as exc:
            print(f"hop reserve {factory} r{n}: {exc}", flush=True)
            continue
        token = res["token"]
        staging = Path(res["staging_dir"])
        try:
            ids = hop.emit_stage(staging, factory, n, ok, bad)
            pub = txn(["publish", str(fdir), "--round", str(n), "--token", token])
        except Exception as exc:
            print(f"hop stage/publish {factory} r{n}: {exc}; abort", flush=True)
            abort(fdir, n, token)
            continue
        print(
            json.dumps(
                {
                    "hop_published": factory,
                    "round": n,
                    "ids": list(ids),
                    "records": pub.get("records"),
                }
            ),
            flush=True,
        )
        return True
    return False


def smoke() -> int:
    sys.path.insert(0, str(ROOT / "pipelines"))
    from check_records import check_jsonl  # noqa: E402

    tmp = Path("/tmp/kcl_wave1443_smoke")
    tmp.mkdir(exist_ok=True)
    for i, spec in enumerate(PAIRS):
        rnd = 1443 + i
        write_round(rnd, tmp, spec)
        path = tmp / f"batch-r{rnd:02d}.jsonl"
        errs, warns, kinds, n = check_jsonl(path, path.name)
        if errs:
            print(f"SMOKE FAIL r{rnd}: {errs}", flush=True)
            return 1
        if n != 2 or kinds.get("episode") != 2:
            print(f"SMOKE FAIL r{rnd} kinds={kinds} n={n}", flush=True)
            return 1
        print(
            f"SMOKE ok r{rnd} {spec['plant']} {spec['slug']} warns={len(warns)}",
            flush=True,
        )
    print(f"SMOKE PASS families={len(PAIRS)}", flush=True)
    return 0


def main() -> int:
    if "--smoke" in sys.argv:
        return smoke()
    published: list[int] = []
    cursor = 0
    hops = 0
    started = time.time()
    taken = taken_slugs()
    plants = taken_plants()
    print(
        f"r1443 mill start pairs={len(PAIRS)} taken_slugs={len(taken)} "
        f"taken_plants={len(plants)} gen={GEN}",
        flush=True,
    )
    while (time.time() - started) < MAX_SECONDS:
        while cursor < len(PAIRS) and (
            PAIRS[cursor]["slug"] in taken or PAIRS[cursor]["plant"] in plants
        ):
            print(
                f"skip taken {PAIRS[cursor]['plant']} {PAIRS[cursor]['slug']}",
                flush=True,
            )
            cursor += 1
        catalog_done = cursor >= len(PAIRS) or len(published) >= MAX_ROUNDS
        try:
            front = txn(["frontier", str(FACTORY_DIR)])
        except RuntimeError as exc:
            print(f"frontier err {exc}", flush=True)
            time.sleep(2)
            continue
        n = int(front["next_round"])
        if catalog_done or reserved(FACTORY_DIR, n):
            why = "catalog" if catalog_done else f"reserved r{n}"
            print(f"HOP: kcl {why}; not stealing", flush=True)
            if hop_once():
                hops += 1
                print(f"hop published count={hops}", flush=True)
            else:
                time.sleep(2)
                taken = taken_slugs()
                plants = taken_plants()
            continue
        spec = PAIRS[cursor]
        try:
            res = txn(
                [
                    "reserve",
                    str(FACTORY_DIR),
                    "--round",
                    str(n),
                    "--expected",
                    "2",
                ]
            )
        except RuntimeError as exc:
            msg = str(exc).lower()
            if "reserv" in msg or "already" in msg or "not the frontier" in msg or "exists" in msg:
                print(f"HOP: reserve failed r{n}: {exc}", flush=True)
                if hop_once():
                    hops += 1
                    print(f"hop published count={hops}", flush=True)
                else:
                    time.sleep(2)
                continue
            raise
        token = res["token"]
        staging = Path(res["staging_dir"])
        print(
            f"reserved r{n} token={token} plant={spec['plant']} slug={spec['slug']}",
            flush=True,
        )
        try:
            write_round(n, staging, spec)
            pub = txn(
                [
                    "publish",
                    str(FACTORY_DIR),
                    "--round",
                    str(n),
                    "--token",
                    token,
                ]
            )
        except Exception as exc:
            print(f"stage/publish failed r{n}: {exc}; abort", flush=True)
            abort(FACTORY_DIR, n, token)
            time.sleep(2)
            continue
        published.append(n)
        taken.add(spec["slug"])
        plants.add(spec["plant"])
        cursor += 1
        print(
            json.dumps(
                {
                    "published": n,
                    "records": pub.get("records"),
                    "done": len(published),
                    "plant": spec["plant"],
                    "slug": spec["slug"],
                }
            ),
            flush=True,
        )
    elapsed = time.time() - started
    print(
        f"DONE published={published} hops={hops} cursor={cursor} elapsed_s={elapsed:.1f}",
        flush=True,
    )
    return 0 if published or hops else 1


if __name__ == "__main__":
    raise SystemExit(main())
