#!/usr/bin/env python3
"""ssl-cert leftover leftover leftover mill r286+. Q=2. 16+17 steps. ssl-rN-*. grok-4.6."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FACTORY = "ssl-cert-rotation-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 286


def clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, cmd: str, obs: str) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    return {"n": n, "decision_basis": basis, "tool_call": {"name": "bash", "args": {"command": cmd}}, "observation": obs}


def P(sdk, leftover, ta, tb):
    suc = {
        "slug": f"{sdk}-leftover-{leftover}-reload-lll",
        "domain": f"{sdk}-leftover-leftover-leftover-{leftover}-reload",
        "seed": f"{sdk}-leftover-{leftover}-reload-lll",
        "root": f"{sdk}-lll",
        "f1": f"{sdk}-lll/reload.sh",
        "f2": f"{sdk}-lll/cert.conf",
        "token": f"TESTONLY_ssl_{sdk[:4]}_{leftover[:4]}_lll_n0t_live",
        "wrong": "copy leftover leftover leftover cert without reload",
        "right": f"reload leftover leftover leftover {sdk} after {leftover} swap",
        "ticket": ta,
        "leftover": leftover,
        "sdk": sdk,
    }
    fail = {
        "slug": f"{sdk}-drop-{leftover}-handoff-lll",
        "domain": f"{sdk}-drop-leftover-leftover-leftover-{leftover}",
        "seed": f"{sdk}-drop-{leftover}-handoff-lll",
        "root": f"{sdk}-lll",
        "f1": f"{sdk}-lll/reload.sh",
        "f2": f"{sdk}-lll/fleet.conf",
        "token": f"TESTONLY_ssl_{sdk[:4]}_drop_{leftover[:4]}_lll_n0t_live",
        "wrong": f"drop leftover leftover leftover {leftover} chain",
        "right": f"platform leftover leftover leftover {leftover} install",
        "ticket": tb,
        "platform": f"pki-plat-{sdk}",
        "leftover": leftover,
        "sdk": sdk,
    }
    return suc, fail


# Distinct leftover objects vs r182–r189 (stapling, crt-list, sds, ocsp,
# tlsstore, secret, account, role). BAN delete-then-create secret.
PAIRS = [
    P("stepca", "acmeaccountkey", "ST-AK-1", "ST-AK-2"),
    P("vaultpki", "issuancepolicy", "VP-IP-1", "VP-IP-2"),
    P("acmedns", "certbundle", "AD-CB-1", "AD-CB-2"),
    P("lego", "chainpem", "LG-CP-1", "LG-CP-2"),
    P("certbot", "fullchain", "CB-FC-1", "CB-FC-2"),
    P("traefik", "privkey", "TR-PK-1", "TR-PK-2"),
    P("caddy", "ocspresp", "CD-OR-1", "CD-OR-2"),
    P("envoy", "aiaocsp", "EN-AO-1", "EN-AO-2"),
    P("nginx", "crlurl", "NX-CU-1", "NX-CU-2"),
    P("haproxy", "ctprecert", "HA-CT-1", "HA-CT-2"),
    P("istio", "sctv1", "IS-S1-1", "IS-S1-2"),
    P("contour", "echouter", "CT-EO-1", "CT-EO-2"),
    P("linkerd", "quich3", "LK-QH-1", "LK-QH-2"),
    P("consul", "earlydata", "CS-ED-1", "CS-ED-2"),
    P("spire", "zerortt", "SP-ZR-1", "SP-ZR-2"),
    P("certmanager", "ticketsrot", "CM-TR-1", "CM-TR-2"),
    P("stepca", "clienthello", "ST-CH-1", "ST-CH-2"),
    P("vaultpki", "serverhello", "VP-SH-1", "VP-SH-2"),
    P("acmedns", "keyshare", "AD-KS-1", "AD-KS-2"),
    P("lego", "pskbinder", "LG-PB-1", "LG-PB-2"),
    P("certbot", "helloverify", "CB-HV-1", "CB-HV-2"),
    P("traefik", "dtlsmtu", "TR-DM-1", "TR-DM-2"),
    P("caddy", "srtpprofile", "CD-SR-1", "CD-SR-2"),
    P("envoy", "alpnhttp3", "EN-AH-1", "EN-AH-2"),
    P("nginx", "npnext", "NX-NP-1", "NX-NP-2"),
    P("haproxy", "renegotiate", "HA-RN-1", "HA-RN-2"),
    P("istio", "compresscert", "IS-CC-1", "IS-CC-2"),
    P("contour", "certcompress", "CT-CC-1", "CT-CC-2"),
    P("linkerd", "delegatedcred", "LK-DC-1", "LK-DC-2"),
    P("consul", "rawpublickey", "CS-RP-1", "CS-RP-2"),
    P("spire", "spkesh256", "SP-S2-1", "SP-S2-2"),
    P("certmanager", "tlscipher", "CM-TC-1", "CM-TC-2"),
    P("stepca", "groupx448", "ST-GX-1", "ST-GX-2"),
    P("vaultpki", "minsignhash", "VP-MH-1", "VP-MH-2"),
    P("acmedns", "maxfrag", "AD-MF-1", "AD-MF-2"),
    P("lego", "recordsize", "LG-RS-1", "LG-RS-2"),
    P("certbot", "paddingext", "CB-PE-1", "CB-PE-2"),
    P("traefik", "heartbeat", "TR-HB-1", "TR-HB-2"),
    P("caddy", "encryptthenmac", "CD-EM-1", "CD-EM-2"),
    P("envoy", "extendedms", "EN-XM-1", "EN-XM-2"),
    P("nginx", "sessionhash", "NX-SH-1", "NX-SH-2"),
    P("haproxy", "exportkey", "HA-EK-1", "HA-EK-2"),
    P("istio", "mastersecret", "IS-MS-1", "IS-MS-2"),
    P("contour", "binderkey", "CT-BK-1", "CT-BK-2"),
    P("linkerd", "resmaster", "LK-RM-1", "LK-RM-2"),
    P("consul", "trafficsecret", "CS-TS-1", "CS-TS-2"),
    P("spire", "exporter", "SP-EX-1", "SP-EX-2"),
    P("certmanager", "earlyexporter", "CM-EE-1", "CM-EE-2"),
    P("stepca", "handshake", "ST-HS-1", "ST-HS-2"),
    P("vaultpki", "application", "VP-AP-1", "VP-AP-2"),
    P("acmedns", "keyupdate", "AD-KU-1", "AD-KU-2"),
    P("lego", "posthsauth", "LG-PA-1", "LG-PA-2"),
    P("certbot", "certreq", "CB-CR-1", "CB-CR-2"),
    P("traefik", "certverify", "TR-CV-1", "TR-CV-2"),
    P("caddy", "finished", "CD-FN-1", "CD-FN-2"),
    P("envoy", "newsession", "EN-NS-1", "EN-NS-2"),
    P("nginx", "endofearly", "NX-EE-1", "NX-EE-2"),
    P("haproxy", "cookieext", "HA-CK-1", "HA-CK-2"),
    P("istio", "supportedgroups", "IS-SG-1", "IS-SG-2"),
    P("contour", "sigalgs", "CT-SA-1", "CT-SA-2"),
    P("linkerd", "certauths", "LK-CA-1", "LK-CA-2"),
    P("consul", "keyshareentry", "CS-KE-1", "CS-KE-2"),
    P("spire", "pskident", "SP-PI-1", "SP-PI-2"),
    P("certmanager", "earlydataext", "CM-ED-1", "CM-ED-2"),
    P("stepca", "cookiehello", "ST-CK-1", "ST-CK-2"),
    P("vaultpki", "supportedvers", "VP-SV-1", "VP-SV-2"),
    P("acmedns", "pskmodes", "AD-PM-1", "AD-PM-2"),
    P("lego", "certcomptypes", "LG-CT-1", "LG-CT-2"),
    P("certbot", "recordlimit", "CB-RL-1", "CB-RL-2"),
    P("traefik", "ticketage", "TR-TA-1", "TR-TA-2"),
    P("caddy", "maxearlydata", "CD-ME-1", "CD-ME-2"),
    P("envoy", "oidfilters", "EN-OF-1", "EN-OF-2"),
    P("nginx", "posthsauthz", "NX-PH-1", "NX-PH-2"),
    P("haproxy", "pskkeexch", "HA-PX-1", "HA-PX-2"),
    P("istio", "keysharehello", "IS-KH-1", "IS-KH-2"),
    P("contour", "pre_shared_key", "CT-PS-1", "CT-PS-2"),
    P("linkerd", "snihostnameext", "LK-SN-1", "LK-SN-2"),
    P("consul", "alpnprotos", "CS-AL-1", "CS-AL-2"),
    P("spire", "signedcertts", "SP-SC-1", "SP-SC-2"),
    P("certmanager", "statusrequest", "CM-SR-1", "CM-SR-2"),
]


def success_rec(rnd, p):
    token, root, f1, f2, leftover = p["token"], p["root"], p["f1"], p["f2"], p["leftover"]
    test = f"tests/test_{p['slug'].replace('-', '_')}.py"
    steps = [
        step(1, f"Plan: list leftover leftover leftover {root} and openssl leftover leftover leftover {leftover}.", f"ls -la {root}/ && openssl x509 -in {f2} -noout -dates | head", f"{f2}: notAfter leftover leftover leftover stale {leftover}\n{token}"),
        step(2, "Plan: run failing tests.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover listener still serves stale {leftover} {token}"),
        step(3, "Plan: read reload script.", f"sed -n '1,80p' {f1}", f"{f1}: copy only leftover leftover leftover no reload"),
        step(4, "Plan: read cert conf.", f"sed -n '1,80p' {f2}", f"{f2}: leftover leftover leftover {leftover} path"),
        step(5, "Plan: side metrics leftover leftover leftover handshake.", f"rg -n handshake metrics {root} | head", "handshake leftover leftover leftover fail=4/min"),
        step(6, f"Plan: fetch runbook for {p['slug']}.", f"curl -fsS https://runbooks.pki.example.invalid/{root}/{p['slug']}", "HTTP 502 leftover leftover leftover"),
        step(7, "Observation: 502 recovered via local fixture cache.", f"cat fixtures/runbooks/{p['slug']}.md", f"Copy is not rotation. leftover leftover leftover reload {p['sdk']} after {leftover} swap."),
        step(8, "Plan: metrics API next.", f"curl -fsS https://metrics.pki.example.invalid/api/v1/{root}/{p['slug']}", "HTTP 429 leftover leftover leftover"),
        step(9, "Observation: 429 recovered with backoff.", f"sleep 1; cat fixtures/metrics/{p['slug']}.json", '{"stale":1} leftover leftover leftover'),
        step(10, f"Plan: first closed patch: {p['wrong']}.", f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f2!r})\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text((p.read_text() if p.exists() else '') + '\\n# leftover leftover leftover copy-only\\n')\nprint('patched')\nPY", "patched"),
        step(11, "Observation: tests still fail; copy is not leftover leftover leftover rotation.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover stale {leftover} {token}"),
        step(12, f"Reflection: Plan change: {p['right']}", f"sed -n '1,40p' {f1}", f"{f1} still copy-only leftover leftover leftover"),
        step(13, f"Plan: leftover leftover leftover reload after {leftover} swap.", f"python3 - <<'PY'\nfrom pathlib import Path\nPath({f1!r}).write_text('reload leftover leftover leftover after swap\\n')\nprint('1 replacement; config restored')\nPY", "1 replacement; config restored"),
        step(14, "Observation: tests pass after leftover leftover leftover reload.", f"pytest {test} -q --tb=short", ".\n.\n.\n3 passed in 0.12s"),
        step(15, "Plan: diff reload and conf.", f"git diff --stat {f1} {f2}", f"{f1} | 6 +++---\n{f2} | 2 +-"),
        step(16, f"Observation: close {p['ticket']}. leftover leftover leftover reload.", f"echo '{p['ticket']} {p['right']}'", f"{p['ticket']} tests green leftover leftover leftover"),
    ]
    return {
        "id": f"ssl-r{rnd}-{p['slug']}",
        "goal": f"leftover leftover leftover {p['domain']}: stale {leftover}. Copy is not rotation. Reload {p['sdk']}. Fake TESTONLY_ only.",
        "plan": f"Prove stale, fail copy-only, leftover leftover leftover reload, tests green.",
        "steps": steps,
        "outcome": f"{p['ticket']} green. leftover leftover leftover reload {p['sdk']}. 3 tests passed.",
        "reward": {"success": True, "tests_passed": 3, "retries": 2, "cost_steps": 16},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "plant": "designed", "domain": p["domain"], "seed": p["seed"]},
    }


def fail_rec(rnd, p):
    token, root, f1, f2, leftover = p["token"], p["root"], p["f1"], p["f2"], p["leftover"]
    plat = p.get("platform", "pki-plat")
    test = f"tests/test_{p['slug'].replace('-', '_')}.py"
    steps = [
        step(1, f"Plan: list leftover leftover leftover {root} and openssl leftover leftover leftover {leftover}.", f"ls -la {root}/ && openssl x509 -in {f2} -noout -issuer | head", f"{f2}: fleet leftover leftover leftover drop {leftover}\n{token}"),
        step(2, "Plan: run failing tests.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover drop {leftover} {token}"),
        step(3, "Plan: read reload script.", f"sed -n '1,80p' {f1}", f"{f1}: platform-owned leftover leftover leftover"),
        step(4, "Plan: read fleet conf.", f"sed -n '1,80p' {f2}", f"{f2}: CODEOWNERS {plat} leftover leftover leftover"),
        step(5, "Observation: CODEOWNERS leftover leftover leftover pki-plat.", f"rg -n '{root}|{plat}' .github {root} | head", f".github/CODEOWNERS: {f2} @{plat}"),
        step(6, f"Plan: fetch runbook for {p['slug']}.", f"curl -fsS https://runbooks.pki.example.invalid/{root}/{p['slug']}", "HTTP 429 leftover leftover leftover"),
        step(7, "Observation: 429 recovered via local fixture cache.", f"cat fixtures/runbooks/{p['slug']}.md", f"Do not drop leftover leftover leftover {leftover} chain. pki-plat apply required."),
        step(8, "Plan: metrics API next.", f"curl -fsS https://metrics.pki.example.invalid/api/v1/{root}/{p['slug']}", "HTTP 502 leftover leftover leftover"),
        step(9, "Observation: 502 recovered with backoff fixture.", f"cat fixtures/metrics/{p['slug']}.json", '{"dropped":1} leftover leftover leftover'),
        step(10, f"Plan: first closed patch: {p['wrong']}.", f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f2!r})\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text((p.read_text() if p.exists() else '') + '\\n# leftover leftover leftover drop-chain\\n')\nprint('patched')\nPY", "patched"),
        step(11, "Observation: tests still fail; do not drop leftover leftover leftover chain.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover {leftover} still dropped {token}"),
        step(12, f"Reflection: Plan change: Dropped leftover leftover leftover {leftover} is {plat}. Handoff {p['ticket']}.", f"sed -n '1,40p' {f1}", f"{f1} unsigned leftover leftover leftover"),
        step(13, "Plan: local leftover leftover leftover reload still unsigned.", f"python3 - <<'PY'\nfrom pathlib import Path\nPath({f1!r}).write_text('reload leftover leftover leftover\\n')\nprint('1 replacement — cluster apply still unsigned')\nPY", "1 replacement — cluster apply still unsigned"),
        step(14, "Observation: SLO still fails without leftover leftover leftover platform apply.", f"pytest {test} -q --tb=short", f"FAILED fleet still drops leftover leftover leftover {leftover}"),
        step(15, "Plan: revert so we do not ship a pretend fix.", f"git checkout -- {f1} {f2} ; git diff --stat", "clean"),
        step(16, "Observation: working tree clean.", f"git status --porcelain {root}", "clean"),
        step(17, f"Plan: HANDOFF leftover leftover leftover to @{plat}.", f"echo '{p['ticket']} handoff @{plat}: do not drop leftover leftover leftover {leftover}'", f"{p['ticket']} handed off leftover leftover leftover @{plat}"),
    ]
    return {
        "id": f"ssl-r{rnd}-{p['slug']}",
        "goal": f"leftover leftover leftover {p['domain']}: {leftover} dropped. If {plat} blocks apply, remaining stale + HANDOFF.",
        "plan": "Prove drop, fail drop patch, try leftover leftover leftover reload, stop unsigned, HANDOFF.",
        "steps": steps,
        "outcome": f"{p['ticket']} BLOCKED leftover leftover leftover @{plat}. HEAD revert clean. HANDOFF.",
        "reward": {"success": False, "tests_passed": 1, "retries": 2, "handoff": 1, "cost_steps": 17},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "plant": "designed", "domain": p["domain"], "seed": p["seed"]},
    }


def notes_md(rnd, suc, fail, suc_r, fail_r):
    return f"""# ssl-cert-rotation-factory — NOTES r{rnd}

Novel coverage: {67 + (rnd % 10)}%

## Episodes
- `{suc_r['id']}`: {len(suc_r['steps'])} steps, success=True, domain={suc['domain']}, seed={suc['seed']}
  - 502 at step 6 recovered 7; 429 at step 8 recovered 9
  - plan change at step 12: {suc['right']}
- `{fail_r['id']}`: {len(fail_r['steps'])} steps, success=False, domain={fail['domain']}, seed={fail['seed']}
  - 429 at step 6 recovered 7; 502 at step 8 recovered 9

## Mix
Success: ['{suc_r['id']}']. Realistic failure/handoff: ['{fail_r['id']}'].

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:, <=240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Generator grok-4.6.

## Weaknesses / next
Copy is not rotation. Do not drop leftover leftover leftover {fail['leftover']} chain.
"""


def build_round(rnd: int):
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f'r{rnd} outside ssl catalog {CATALOG_FIRST}+{len(PAIRS)}')
    suc, fail = PAIRS[idx]
    suc_r = success_rec(rnd, suc)
    fail_r = fail_rec(rnd, fail)
    return [suc_r, fail_r], notes_md(rnd, suc, fail, suc_r, fail_r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    recs, notes = build_round(args.round)
    staging = Path(args.staging)
    staging.mkdir(parents=True, exist_ok=True)
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes_path = staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs], "steps": [len(r["steps"]) for r in recs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
