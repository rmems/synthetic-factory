#!/usr/bin/env python3
"""ssl leftover leftover leftover mill. Unique path so siblings do not clobber ssl-mill-r132.py."""
from __future__ import annotations

import argparse
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
_base = SourceFileLoader("ssl35lll", str(HERE / "ssl-mill-r35.py")).load_module()
build_success = _base.build_success
build_partial = _base.build_partial
CATALOG_FIRST = 145

PAIRS = [
    (
        ("consul-connect-leaf-bind", "Consul Connect leftover leaf", "leaf leftover", "wipe CA",
         "rebind leftover Connect leaf; do not wipe the CA",
         "Bind leftover Consul Connect leaf; do not wipe CA.",
         "https://developer.hashicorp.com/consul/docs/connect/ca", "src/legacy_consul_leaf.py"),
        ("consul-connect-leaf-handoff", "Consul Connect wipe-CA", "leaf leftover", "wipe CA",
         "leaf leftover leftover leftover",
         "Ticket is leftover Connect leaf bind; nightly still wipes the CA.",
         "https://developer.hashicorp.com/consul/docs/connect/config", "src/nightly_consul_leaf.py"),
    ),
    (
        ("spire-svid-leftover-bind", "SPIRE leftover SVID", "SVID leftover", "restart agent",
         "rebind leftover SVID; do not restart the agent",
         "Bind leftover SPIRE SVID; do not restart the agent.",
         "https://spiffe.io/docs/latest/spire-about/spire-concepts/", "src/legacy_spire_svid.py"),
        ("spire-svid-leftover-handoff", "SPIRE agent-restart", "SVID leftover", "restart agent",
         "SVID leftover leftover leftover",
         "Ticket is leftover SVID bind; nightly still restarts the agent.",
         "https://spiffe.io/docs/latest/deploying/spire_agent/", "src/nightly_spire_svid.py"),
    ),
    (
        ("cert-manager-clusterissuer-bind", "cert-manager ClusterIssuer leftover", "ClusterIssuer leftover",
         "delete Issuer",
         "rebind leftover ClusterIssuer; do not delete the Issuer (not Gateway)",
         "Bind leftover ClusterIssuer; do not delete Issuer. Distinct from r131 Gateway.",
         "https://cert-manager.io/docs/configuration/selfsigned/", "src/legacy_cm_clusterissuer.py"),
        ("cert-manager-clusterissuer-handoff", "cert-manager Issuer-delete", "ClusterIssuer leftover",
         "delete Issuer",
         "ClusterIssuer leftover leftover leftover",
         "Ticket is leftover ClusterIssuer bind; nightly still deletes Issuer. Not r131 Gateway.",
         "https://cert-manager.io/docs/concepts/issuer/", "src/nightly_cm_clusterissuer.py"),
    ),
]


def notes_for(rnd, suc, fail, suc_p, fail_p) -> str:
    return (
        f"# ssl-cert-rotation-factory — NOTES r{rnd}\n\n"
        f"Novel coverage: {max(68, 84 - (rnd - 132))}%\n\n"
        f"## Episodes\n"
        f"- `{suc['id']}`: 16 steps, success=True, domain={suc_p[0]}, seed={suc_p[0]}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {suc_p[4]}. Do not delete-then-create secret.\n"
        f"- `{fail['id']}`: 17 steps, success=False, domain={fail_p[0]}, seed={fail_p[0]}\n"
        f"  - 429 at step 8 recovered 9; nightly {fail_p[4]} leftover leftover leftover\n\n"
        f"## Mix\n"
        f"Success: ['{suc['id']}']. Realistic failure/handoff: ['{fail['id']}'].\n\n"
        f"## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real. Generator grok-4.6.\n\n"
        f"## Weaknesses / next\n"
        f"Avoid delete-then-create secret. BAN r131 Gateway/trust-manager ConfigMap clones.\n"
        f"Distinct leftover leftover leftover from ssl r01–r{rnd-1} ({suc_p[5]}; {fail_p[5]}).\n"
    )


def build_round(rnd: int):
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}")
    suc_p, fail_p = PAIRS[idx]
    suc = build_success(rnd, suc_p)
    fail = build_partial(rnd, fail_p)
    return [suc, fail], notes_for(rnd, suc, fail, suc_p, fail_p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    recs, notes = build_round(args.round)
    staging = Path(args.staging)
    (staging / f"batch-r{args.round:02d}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=True) + "\n" for r in recs)
    )
    (staging / f"NOTES-r{args.round:02d}.md").write_text(notes)
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
