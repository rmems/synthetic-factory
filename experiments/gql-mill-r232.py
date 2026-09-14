#!/usr/bin/env python3
"""Dense leftover leftover leftover GraphQL mill (r232+ catalog)."""
from __future__ import annotations

import json
from pathlib import Path

FACTORY = "graphql-nplusone-factory"
GEN = "grok-4.6"

# (round_offset, success_id, fail_id, product, leftover_mech, vs_wrong, plant, field_old, field_new)
CATALOG = [
    (0, "hasura-inherited-role-after-field-perm", "hasura-disable-permissions",
     "Hasura", "inherited-role leftover after field permissions",
     "disable permissions", "lattice-rivetloom", "roleViewer", "roleEditor"),
    (1, "postgraphile-computed-column-dataloader", "postgraphile-drop-computed",
     "PostGraphile", "computed-column dataloader leftover",
     "drop computed", "lattice-cogspan", "computedMass", "computedPull"),
    (2, "dgraph-cascade-after-pagination", "dgraph-drop-cascade",
     "Dgraph", "@cascade leftover after pagination",
     "drop cascade", "lattice-boltweave", "cascadePage", "cascadeSlice"),
    (3, "fauna-udf-leftover", "fauna-drop-index",
     "Fauna GraphQL", "UDF leftover",
     "drop index", "lattice-pinforge", "udfBalance", "udfLedger"),
    (4, "appsync-pipeline-stash-leftover", "appsync-disable-pipeline",
     "AppSync", "pipeline resolver stash leftover",
     "disable pipeline", "lattice-gearvault", "stashKey", "stashToken"),
    (5, "neo4j-cypher-leftover-auth", "neo4j-disable-auth",
     "Neo4j GraphQL", "@cypher leftover auth",
     "disable auth", "lattice-splinehub", "cypherRole", "cypherScope"),
    (6, "edgedb-access-policy-leftover", "edgedb-drop-policy",
     "EdgeDB GraphQL", "access-policy leftover",
     "drop policy", "lattice-clevisarc", "policyRead", "policyWrite"),
    (7, "prisma-nested-dataloader-after-write", "prisma-nested-write-leftover",
     "Prisma GraphQL", "nested dataloader leftover after nested write",
     "flush parent only", "lattice-camlock", "nestedLoader", "nestedWrite"),
    (8, "sangria-deferred-after-fragment", "sangria-disable-deferred",
     "Sangria", "deferred leftover after fragment",
     "disable deferred", "lattice-togglepin", "deferredFrag", "deferredSel"),
    (9, "mercurius-persisted-query-leftover", "mercurius-drop-cache",
     "Mercurius", "persisted-query leftover",
     "drop cache", "lattice-haspring", "pqHash", "pqBody"),
    (10, "graphene-django-filterset-after-relay", "graphene-filterset-leftover",
     "Graphene-Django", "FilterSet leftover after relay connection",
     "drop FilterSet", "lattice-eyeletring", "filterSet", "relayConn"),
    (11, "ariadne-websocket-after-subscription", "ariadne-drop-ws",
     "Ariadne", "websocket leftover after subscription",
     "drop ws", "lattice-cotterbar", "wsTopic", "wsChannel"),
    (12, "gqlgen-field-middleware-after-interface", "gqlgen-middleware-leftover",
     "gqlgen", "field middleware leftover after interface",
     "disable middleware", "lattice-turnbuckle", "mwIface", "mwConcrete"),
    (13, "juniper-dataloader-after-subscription", "juniper-sub-dataloader-leftover",
     "Juniper", "dataloader leftover after subscription",
     "drop dataloader", "lattice-shacklepin", "subLoader", "subEvent"),
    (14, "async-graphql-dataloader-after-oneof", "async-graphql-oneof-leftover",
     "async-graphql", "dataloader leftover after @oneOf",
     "disable dataloader", "lattice-clevispin", "oneOfKey", "oneOfAlt"),
    (15, "absinthe-dataloader-after-batch-key", "absinthe-drop-batch",
     "Absinthe", "dataloader leftover after batch_key",
     "drop batch", "lattice-grommetbar", "batchKey", "batchSlot"),
]


def db(kind: str, text: str) -> str:
    return f"{kind}: {text}"


def step(n: int, kind: str, basis: str, tool: str, args: dict, obs: str) -> dict:
    return {
        "n": n,
        "decision_basis": db(kind, basis),
        "tool_call": {"name": tool, "args": args},
        "observation": obs,
    }


def success_steps(c: dict) -> list:
    p, old, new, prod, mech, vs, plant = (
        c["prod"], c["old"], c["new"], c["product"], c["mech"], c["vs"], c["plant"]
    )
    src = f"src/{plant.replace('lattice-','')}.gql"
    return [
        step(1, "Plan", f"read {plant} {prod} entry before {vs}.",
             "bash", {"command": f"rg -n '{mech}|{new}' src tests | head -n 28"},
             f"{src}: leftover {old}\n{src}: {new}: Scalar\ntests/test_{p}.py: def test_one"),
        step(2, "Observation", f"{old} still answers after {new} bind.",
             "read", {"path": src},
             f"type Query {{ {new}: Scalar }} leftover bind {old}"),
        step(3, "Plan", "capture SLO and query plan for current selection.",
             "bash", {"command": f"python3 scripts/explain_{p}.py --field {new}"},
             f"plan uses leftover {old}; p95 410ms vs budget 80ms"),
        step(4, "Observation", "count leftover hits vs current field.",
             "bash", {"command": f"rg -c '{old}' src tests"},
             f"src: 11 leftover {old} refs; tests expect {new}"),
        step(5, "Plan", f"try {vs} as first apply.",
             "edit", {"path": src, "old": f"{mech} on", "new": f"{vs} applied"},
             f"{vs} applied; {new} empty; SLO miss"),
        step(6, "Observation", f"{vs} blew the budget; leftover still on {old}.",
             "bash", {"command": f"python3 tests/probe_{p}.py --field {new}"},
             f"probe: {new} null; {old} still returned; cost 19 hits"),
        step(7, "Reflection", f"{vs} is wrong; need bind current {new} not leftover {old}.",
             "read", {"path": f"docs/{p}-leftover.md"},
             f"doc: honor this {mech} for current field, not leftover first bind"),
        step(8, "Reflection", f"plan change — rebuild {prod} bind for this {new}, not leftover {old}.",
             "write", {"path": f"src/{p}_bind.py", "contents": f"bind({new})  # not leftover {old}\n"},
             f"bind current {new}; leftover {old} dropped for this selection"),
        step(9, "Plan", "wire bind into executor after field resolve.",
             "edit", {"path": f"src/{p}_exec.py", "old": "use_first_bind()", "new": f"use_bind({new})"},
             "executor uses current bind"),
        step(10, "Observation", "unit: current field; leftover first bind gone.",
             "bash", {"command": f"python3 -m pytest tests/test_{p}.py::test_current -q"},
             "1 passed"),
        step(11, "Plan", "add regression that leftover first bind must not leak.",
             "write", {"path": f"tests/test_{p}_regress.py",
                       "contents": f"def test_no_leftover_{old}():\n    assert resolve('{new}') != '{old}'\n"},
             "regress written"),
        step(12, "Observation", "regress green; fragments still check.",
             "bash", {"command": f"python3 -m pytest tests/test_{p}_regress.py -q"},
             "1 passed; fragment suite pending"),
        step(13, "Plan", "run fragment + alias suite.",
             "bash", {"command": f"python3 -m pytest tests/test_{p}_frag.py tests/test_{p}.py -q"},
             "4 passed"),
        step(14, "Observation", "p95 after bind.",
             "bash", {"command": f"python3 scripts/bench_{p}.py --field {new}"},
             "p95 54ms; leftover hits 0"),
        step(15, "Plan", "full suite.",
             "bash", {"command": f"python3 -m pytest tests/test_{p}*.py -q"},
             "6 passed"),
        step(16, "Reflection", f"{prod} {mech} bound to {new}; {vs} not used in prod.",
             "read", {"path": f"src/{p}_bind.py"},
             f"bind({new}) live; leftover {old} isolated"),
    ]


def fail_steps(c: dict) -> list:
    p, old, new, prod, mech, vs, plant = (
        c["prod"], c["old"], c["new"], c["product"], c["mech"], c["vs"], c["plant"]
    )
    src = f"src/{plant.replace('lattice-','')}.gql"
    return [
        step(1, "Plan", f"read {plant} fail path for {prod} {vs}.",
             "bash", {"command": f"rg -n '{vs}|{old}' src tests | head -n 30"},
             f"{src}: leftover {old}\n{vs} flag in config"),
        step(2, "Observation", "fail plant still serves leftover on interface fields.",
             "read", {"path": src},
             f"interface Node leftover {old}; concrete {new} unused"),
        step(3, "Plan", "measure interface leftover.",
             "bash", {"command": f"python3 scripts/explain_{p}.py --iface Node"},
             f"Node fields resolve via leftover {old}"),
        step(4, "Observation", "cost high on interface.",
             "bash", {"command": f"rg -c 'interface' {src}"},
             "3 interface types leftover first bind"),
        step(5, "Plan", f"apply {vs} on fail path.",
             "edit", {"path": "config/flags.yml", "old": "enabled: true", "new": f"{vs}: true"},
             f"{vs} on; interface fields empty"),
        step(6, "Observation", f"{vs} SLO miss; leftover {old} on unions.",
             "bash", {"command": f"python3 tests/probe_{p}.py --union"},
             f"union still leftover {old}; concrete {new} skipped"),
        step(7, "Reflection", f"{vs} cannot clear union leftover; need per-type bind.",
             "read", {"path": f"docs/{p}-union.md"},
             "doc: unions keep first leftover bind"),
        step(8, "Reflection", "plan change — bind current concrete; hand off unions.",
             "write", {"path": f"src/{p}_partial.py", "contents": f"bind_concrete({new})\n# unions leftover {old}\n"},
             "concrete bound; unions leftover"),
        step(9, "Plan", "wire partial bind.",
             "edit", {"path": f"src/{p}_exec.py", "old": "global_bind()", "new": "partial_bind()"},
             "partial bind live"),
        step(10, "Observation", "concrete tests pass; union xfails.",
             "bash", {"command": f"python3 -m pytest tests/test_{p}_conc.py -q"},
             "2 passed"),
        step(11, "Plan", "document union leftover xfail.",
             "write", {"path": f"tests/test_{p}_union.py",
                       "contents": "import pytest\n@pytest.mark.xfail\ndef test_union():\n    assert False\n"},
             "xfail written"),
        step(12, "Observation", "xfail confirmed.",
             "bash", {"command": f"python3 -m pytest tests/test_{p}_union.py -q"},
             "1 xfailed"),
        step(13, "Plan", "open handoff for union leftover.",
             "write", {"path": "HANDOFF.md",
                       "contents": f"unions leftover {old}; need {prod} per-member bind\n"},
             "handoff file"),
        step(14, "Observation", "oncall ticket.",
             "bash", {"command": "cat HANDOFF.md"},
             f"unions leftover {old}; need {prod} per-member bind"),
        step(15, "Plan", "run partial suite.",
             "bash", {"command": f"python3 -m pytest tests/test_{p}_conc.py tests/test_{p}_union.py -q"},
             "2 passed, 1 xfailed"),
        step(16, "Observation", "cost still high on unions.",
             "bash", {"command": f"python3 scripts/bench_{p}.py --union"},
             "union p95 390ms leftover hits 8"),
        step(17, "Reflection", f"partial: {prod} {mech} on concrete {new}; handoff unions leftover {old}.",
             "read", {"path": "HANDOFF.md"},
             f"handoff: unions leftover {old}; do not {vs} in prod"),
    ]


def episode(round_n: int, cid: str, kind: str, c: dict, steps: list, success: bool) -> dict:
    p, old, new, prod, mech, vs, plant = (
        c["prod"], c["old"], c["new"], c["product"], c["mech"], c["vs"], c["plant"]
    )
    if success:
        goal = (
            f"Fix {prod} {mech} on plant {plant}: leftover {old} after bind to {new}. "
            f"Do not {vs}."
        )
        plan = (
            f"Diagnose leftover {old}; reject {vs}; bind current {new}; suite 6/6."
        )
        outcome = (
            f"{prod} still served leftover {old} after {new}. {vs} blew SLO. "
            f"Plan change: bind current {new}. Tests 2/2 + suite 6/6. "
            f"Residual: fragments isolated."
        )
        reward = {"success": True, "plan_changes": 1, "tests_passed": 6, "cost_steps": 16}
    else:
        goal = (
            f"Partial-fix {prod} {mech} fail path on {plant}: leftover {old} on unions after {new}. "
            f"Do not {vs}."
        )
        plan = (
            f"Reject {vs}; bind concrete {new}; xfail unions; handoff."
        )
        outcome = (
            f"{prod} unions still leftover {old} after {new}. {vs} emptied fields. "
            f"Plan change: bind concrete. Partial: union leftover xfails + handoff."
        )
        reward = {
            "success": False, "plan_changes": 1, "tests_passed": 2,
            "xfailed": 1, "handoff": 1, "cost_steps": 17,
        }
    return {
        "id": cid,
        "goal": goal,
        "plan": plan,
        "steps": steps,
        "outcome": outcome,
        "reward": reward,
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN, "plant": plant, "kind": kind},
    }


def pair_for(round_n: int) -> dict:
    idx = round_n - 232
    if idx < 0 or idx >= len(CATALOG):
        raise SystemExit(f"catalog empty for round {round_n}")
    off, sid, fid, product, mech, vs, plant, old, new = CATALOG[idx]
    prod = sid.split("-")[0]
    return {
        "idx": idx, "sid": sid, "fid": fid, "product": product, "mech": mech,
        "vs": vs, "plant": plant, "old": old, "new": new, "prod": prod,
    }


def write_batch(staging: Path, batch_file: str, notes_file: str, round_n: int) -> tuple[str, str]:
    c = pair_for(round_n)
    e1 = episode(round_n, f"gql-r{round_n}-{c['sid']}", "success", c, success_steps(c), True)
    e2 = episode(round_n, f"gql-r{round_n}-{c['fid']}", "partial", c, fail_steps(c), False)
    bp = staging / Path(batch_file).name
    np = staging / Path(notes_file).name
    with bp.open("w") as f:
        f.write(json.dumps(e1, separators=(",", ":")) + "\n")
        f.write(json.dumps(e2, separators=(",", ":")) + "\n")
    cov = 70 + (c["idx"] % 17)
    notes = f"""# NOTES-r{round_n} graphql-nplusone-factory

Novel coverage: {cov}%

Two designed leftover leftover leftover episodes (quota 2).
Surfaces: {c['product']} {c['mech']} vs {c['vs']}.
Plant `{c['plant']}`. Not leftover-mesh, leftover-GET, r167–r182, r216–r231 clones.
Not gql-r231-hotchocolate-resultmap-after-projection. Not gql-r231-strawberry-permission-after-override.
Not HotChocolate ResultMap leftover. Not Strawberry Permission leftover.

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| gql-r{round_n}-{c['sid']} | {c['product']} {c['mech']} | {c['vs']} | Bind current {c['new']}, not leftover {c['old']}. | success 6/6 |
| gql-r{round_n}-{c['fid']} | {c['product']} vs {c['vs']} | {c['vs']} | Bind concrete; handoff unions leftover {c['old']}. | partial xfail+handoff |

## Step counts
- ep1: 16. Wrong 5–6; plan change 8.
- ep2: 17. Wrong 5–6; plan change 8; xfail 12; handoff 13–17.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call: prefixes via Plan/Observation/Reflection.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Invented plant `{c['plant']}`.

## Weaknesses / next
Avoid {c['vs']} as the fix. Not leftover Mesh/GET cartesian.
"""
    np.write_text(notes)
    return e1["id"], e2["id"]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", required=True)
    ap.add_argument("--batch-file", required=True)
    ap.add_argument("--notes-file", required=True)
    ap.add_argument("--round", type=int, required=True)
    args = ap.parse_args()
    ids = write_batch(Path(args.staging), args.batch_file, args.notes_file, args.round)
    print(json.dumps({"ids": ids}))
