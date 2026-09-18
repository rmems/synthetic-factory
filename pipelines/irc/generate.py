#!/usr/bin/env python3
"""Designed leftover3 IRC episodes from the AST-extracted r3366 catalog.

Faithful reconstruction of ``episode`` / ``notes`` from
``experiments/irc_r3366_leftover3_mill.py``. Does not import or execute the
mill, does not hop factories, and does not call ``round_txn``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    BANNED_KEYS,
    CATALOG_FIRST,
    CATALOG_LAST,
    FACTORY,
    FINDING_BANNED_KEY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_USAGE,
    GENERATOR,
    NOTES_FILENAME,
    NOVEL_COVERAGE,
    QUOTA_PER_ROUND,
    RECORDS_FILENAME,
    RUN_FILENAME,
    RUN_FORMAT,
    SOURCE_MILL_ID,
    STEPS,
    TICKET_BASE,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse_vendor_paths,
    refuse_when,
    require_round,
)

__all__ = [
    "GenerateRequest",
    "build_episode",
    "episode_id",
    "notes_for",
    "pair_records",
    "run",
    "ticket_number",
]


@dataclass(frozen=True)
class GenerateRequest:
    out_dir: Path
    round: int | None = None
    slug: str | None = None
    index: int | None = None
    window: bool = False


def ticket_number(rnd: int, ticket_off: int) -> int:
    return TICKET_BASE + (rnd - CATALOG_FIRST) * QUOTA_PER_ROUND + int(ticket_off)


def episode_id(rnd: int, slug: str, ticket_n: int) -> str:
    ticket = f"W2-{ticket_n}"
    hid = hashlib.sha256(f"{rnd}-{slug}-{ticket}".encode()).hexdigest()[:4]
    return f"irc-r{rnd}-{slug}-{ticket_n}-{hid}"


def _step(n: int, basis: str, tool: dict[str, Any], obs: str, reflection: str) -> dict[str, Any]:
    refuse_when(not basis.startswith(("Plan:", "Observation:")), FINDING_USAGE, f"step {n} prefix")
    refuse_when(len(basis) > 240, FINDING_USAGE, f"step {n} decision_basis")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": tool,
        "observation": obs,
        "reflection": reflection,
    }


def _walk_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        keys = list(value)
        for item in value.values():
            keys.extend(_walk_keys(item))
        return keys
    if isinstance(value, list):
        found: list[str] = []
        for item in value:
            found.extend(_walk_keys(item))
        return found
    return []


def _refuse_banned(record: dict[str, Any]) -> None:
    hits = sorted(BANNED_KEYS.intersection(_walk_keys(record)))
    refuse_when(bool(hits), FINDING_BANNED_KEY, f"{record.get('id')!r} carries {hits[0] if hits else ''}")
    refuse_when("reward" in json.dumps(record.get("steps")), FINDING_BANNED_KEY, "step reward")


def build_episode(rnd: int, rec: dict[str, Any], remediate: str) -> dict[str, Any]:
    """17-step leftover3 on-call episode. Both remediations stay success=True."""

    require_round(rnd)
    refuse_when(remediate not in {"rollback", "patch"}, FINDING_USAGE, remediate)
    ticket_n = ticket_number(rnd, rec["ticket_off"])
    ticket = f"W2-{ticket_n}"
    svc, ns, cluster, node = rec["svc"], rec["ns"], rec["cluster"], rec["node"]
    slug, herring, rca = rec["slug"], rec["herring"], rec["rca"]
    eid = episode_id(rnd, slug, ticket_n)
    mimir = f"https://mimir.{cluster}.obs.internal/prometheus/api/v1/query"
    loki = f"https://loki.{cluster}.obs.internal/loki/api/v1/query_range"
    helm = f"helm -n {ns} {'rollback ' + svc + ' 3' if remediate == 'rollback' else 'upgrade ' + svc + ' charts/' + svc}"
    steps = [
        _step(
            1,
            f"Plan: page {ticket} {svc} leftover leftover leftover; read alert.",
            {"name": "read", "args": {"path": f"alerts/{ticket.lower()}-{svc}.json"}},
            json.dumps(
                {
                    "id": ticket,
                    "urgency": "high",
                    "service": svc,
                    "cluster": cluster,
                    "ns": ns,
                    "node": node,
                    "title": f"{svc} leftover leftover leftover {slug}",
                },
                indent=2,
            ),
            "Read runbook.",
        ),
        _step(
            2,
            f"Observation: alert names {svc} on {cluster} (step 1). Read runbook.",
            {"name": "read", "args": {"path": f"runbooks/{svc}.md"}},
            f"# {svc}\n1. Check {herring}.\n2. Apply that fix if leftover leftover leftover.\n"
            f"3. If still burning, inspect leftover {rec['file']}.\n",
            "Pull metric with retry.",
        ),
        _step(
            3,
            f"Observation: runbook leads with {herring} (step 2). Query {rec['query']}.",
            {"name": "fetch", "args": {"url": mimir, "query": rec["query"]}},
            f"GET {mimir}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\n"
            '{"status":"error","errorType":"rate_limited"}\n',
            "Retry after 429.",
        ),
        _step(
            4,
            "Observation: mimir 429 (step 3). Retry once.",
            {"name": "fetch", "args": {"url": mimir, "query": rec["query"], "retry": True}},
            f"GET {mimir}\nHTTP/1.1 502 Bad Gateway\n"
            '{"status":"error","errorType":"upstream"}\n',
            "Second retry after 502.",
        ),
        _step(
            5,
            "Observation: mimir 502 (step 4). Retry then Loki.",
            {"name": "fetch", "args": {"url": mimir, "query": rec["query"], "retry": True}},
            (
                f"GET {mimir}\nHTTP/1.1 200 OK\n"
                f'{{"status":"success","result":[{{"metric":{{"svc":"{svc}","node":"{node}"}},'
                f'"value":[1710000000,"hint={herring}"]}}]}}\n'
            ),
            "Logs next.",
        ),
        _step(
            6,
            f"Observation: metric hint {herring} (step 5). Chase herring cmd.",
            {"name": "bash", "args": {"command": rec["herring_cmd"]}},
            f"{rec['herring_cmd']}: leftover leftover leftover no change to {rec['metric']}",
            "Herring action 1.",
        ),
        _step(
            7,
            f"Observation: {rec['herring_cmd']} did not clear SLO (step 6). Inspect logs.",
            {"name": "fetch", "args": {"url": loki, "query": f'{{app="{svc}"}} |= "leftover"'}},
            f"GET {loki}\n{node} {svc}: log lines agree with first lead '{herring}'\n"
            f"also mention leftover leftover leftover {rec['fail']}\n",
            "Herring action 2.",
        ),
        _step(
            8,
            "Observation: logs still name herring (step 7). Bounce sidecar.",
            {"name": "bash", "args": {"command": f"kubectl -n {ns} rollout restart deploy/{svc}"}},
            f'deployment "{svc}" restarted; {rec["metric"]} still high',
            "Herring survived 3 steps; falsify.",
        ),
        _step(
            9,
            f"Observation: bounce did not help (step 8). Re-query {rec['metric']}.",
            {"name": "fetch", "args": {"url": mimir, "query": rec["metric"]}},
            f"GET {mimir}\nHTTP/1.1 200 OK\n"
            '{"status":"success","result":[{"value":[1710000100,"still_burning"]}]}\n',
            "Herring falsified.",
        ),
        _step(
            10,
            f"Observation: SLO still burning (step 9). Grep {rec['file']}.",
            {"name": "bash", "args": {"command": f"grep {rec['grep']} {rec['file']}"}},
            rec["fail"],
            f"RCA is {rca}",
        ),
        _step(
            11,
            f"Observation: leftover leftover leftover in {rec['file']} (step 10). Helm history.",
            {"name": "bash", "args": {"command": f"helm -n {ns} history {svc} | head -5"}},
            "REVISION  STATUS\n3  superseded\n4  deployed leftover leftover leftover",
            f"Remediate={remediate}.",
        ),
        _step(
            12,
            f"Observation: chart rev 4 has leftover leftover leftover (step 11). {remediate}.",
            {"name": "bash", "args": {"command": helm}},
            f"{remediate} applied; {rec['file']} now {rec['fix']}",
            "Confirm grep.",
        ),
        _step(
            13,
            f"Observation: {remediate} applied (step 12). Confirm {rec['grep']}.",
            {"name": "bash", "args": {"command": f"grep {rec['grep']} {rec['file']} || echo fixed"}},
            rec["fix"],
            "Write incident.",
        ),
        _step(
            14,
            f"Observation: config now {rec['fix']} (step 13). Write incident note.",
            {
                "name": "write",
                "args": {
                    "path": f"incidents/{ticket}.md",
                    "contents": (
                        f"# {ticket} {svc}\nherring: {herring}\nrca: {rca}\n"
                        f"remediate: {remediate}\nsuccess: True\n"
                    ),
                },
            },
            f"wrote incidents/{ticket}.md",
            "Workload check.",
        ),
        _step(
            15,
            f"Observation: note written (step 14). List {ns} workloads.",
            {"name": "bash", "args": {"command": f"kubectl -n {ns} get deploy,po 2>/dev/null | head -40"}},
            f"{svc} 1/1 Ready leftover leftover leftover cleared",
            "Slack.",
        ),
        _step(
            16,
            f"Observation: {svc} Ready (step 15). Final metric.",
            {"name": "fetch", "args": {"url": mimir, "query": rec["metric"]}},
            f"GET {mimir}\nHTTP/1.1 200 OK\n"
            '{"status":"success","result":[{"value":[1710000200,"0"]}]}\n',
            "Page closed.",
        ),
        _step(
            17,
            f"Observation: {rec['metric']}=0 (step 16). Slack #oncall.",
            {
                "name": "bash",
                "args": {
                    "command": f"echo POST slack #oncall {ticket} herring_survived=3 rca_ok=true service={svc}"
                },
            },
            f"slack ok {ticket}",
            "Done.",
        ),
    ]
    refuse_when(len(steps) != STEPS, FINDING_USAGE, f"{eid} steps {len(steps)}")
    record = {
        "id": eid,
        "kind": "episode",
        "goal": (
            f"Page {ticket}: {svc} in {ns} on {cluster} is burning {rec['metric']} because "
            f"leftover leftover leftover {slug}. Restore {rec['fix']}; do not disable the tool."
        ),
        "plan": (
            f"Read the page and runbook, pull {rec['query']} (retry 429/502), chase {herring} "
            f"only while it fits, then {remediate}."
        ),
        "false_lead": {"claim": herring, "survived_steps": [6, 7, 8], "falsified_at": 10},
        "rca": rca,
        "remediate": remediate,
        "steps": steps,
        "outcome": (
            f"False lead: {herring}. RCA: {rca}. Remediate={remediate}. "
            f"{rec['file']} now {rec['fix']}."
        ),
        "reward": {
            "success": True,
            "steps": STEPS,
            "false_lead_steps": 3,
            "http_retries": 2,
        },
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GENERATOR,
            "plant": "designed",
            "alert_source": "opsgenie",
            "ticket": ticket,
            "mill_id": SOURCE_MILL_ID,
        },
    }
    _refuse_banned(record)
    return record


def pair_records(rnd: int) -> tuple[dict[str, Any], dict[str, Any]]:
    require_round(rnd)
    refuse_when(not CATALOG_FIRST <= rnd <= CATALOG_LAST, FINDING_USAGE, f"round {rnd}")
    pair = cat.pair_for_round(rnd)
    ok = build_episode(rnd, pair["ok"], "rollback")
    bad = build_episode(rnd, pair["bad"], "patch")
    refuse_when(ok["id"] == bad["id"], FINDING_USAGE, "duplicate episode ids")
    return ok, bad


def notes_for(rnd: int, ok: dict[str, Any], bad: dict[str, Any]) -> str:
    return (
        f"# incident-response-oncall-factory NOTES r{rnd}\n\n"
        f"Novel coverage: {NOVEL_COVERAGE}%. Unique service+cluster+symptom leftover leftover leftover "
        f"goals; RCA pair {ok['id']} / {bad['id']}. No OpenSRE stamp, no fraud-graph/sip-proxy, "
        f"not r2920–r3355 clones. BAN ypbind/oddjob. Hop mill: SRL was reserved; this wave is "
        f"leftover leftover leftover tool forks. Later mills stay on {SOURCE_MILL_ID}'s lane.\n\n"
        f"OpenSRE designed: 429 then 502 retries, 3-step herring, unique RCA, mix patch/rollback. "
        f"plant=designed. generator={GENERATOR}.\n\n"
        f"| id | ticket | herring (steps 6-8) | remediate | success | steps |\n"
        f"|---|---|---|---|---|---|\n"
        f"| `{ok['id']}` | {ok['meta']['ticket']} | {ok['false_lead']['claim']} | {ok['remediate']} | True | {len(ok['steps'])} |\n"
        f"| `{bad['id']}` | {bad['meta']['ticket']} | {bad['false_lead']['claim']} | {bad['remediate']} | True | {len(bad['steps'])} |\n\n"
        f"## Contract audit\n"
        f"- Q=2 episodes, kind=episode, ids irc-r{rnd}-*.\n"
        f"- Unique goal service+cluster+symptom; 3 false-lead actions; 429/502 retries.\n"
        f"- Residual: designed excerpts, not live dispatcher traces.\n"
    )


def _jobs(request: GenerateRequest) -> list[int]:
    if request.window:
        refuse_when(request.slug is not None or request.index is not None, FINDING_USAGE, "window")
        start = CATALOG_FIRST if request.round is None else require_round(request.round)
        refuse_when(not CATALOG_FIRST <= start <= CATALOG_LAST, FINDING_USAGE, f"round {start}")
        return list(range(start, CATALOG_LAST + 1))
    if request.slug is not None:
        pair = cat.pair_by_ok_slug(request.slug)
        index = slugs_index(pair["ok"]["slug"])
        rnd = CATALOG_FIRST + index if request.round is None else require_round(request.round)
        return [rnd]
    if request.index is not None:
        pair = cat.pair_at(request.index)
        rnd = CATALOG_FIRST + request.index if request.round is None else require_round(request.round)
        return [rnd]
    refuse_when(request.round is None, FINDING_USAGE, "pass --round, --slug/--index, or --window")
    return [require_round(request.round)]


def slugs_index(slug: str) -> int:
    return cat.slugs().index(slug)


def run(request: GenerateRequest) -> dict[str, Any]:
    """Write one brand-new destination. Refuses ``outputs/raw/`` and existing paths."""

    out_dir = Path(request.out_dir)
    refuse_vendor_paths((out_dir,))
    refuse_when(is_under_raw(out_dir), FINDING_DESTINATION_UNDER_RAW, str(out_dir))
    refuse_when(out_dir.exists(), FINDING_DESTINATION_EXISTS, str(out_dir))
    rounds = _jobs(request)
    out_dir.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    notes: list[str] = []
    try:
        for rnd in rounds:
            ok, bad = pair_records(rnd)
            records.extend((ok, bad))
            notes.append(notes_for(rnd, ok, bad))
        lines = [dumps_exact_json(record, ensure_ascii=False, sort_keys=True) for record in records]
        text = "\n".join(lines) + "\n"
        (out_dir / RECORDS_FILENAME).write_text(text, encoding="utf-8")
        (out_dir / NOTES_FILENAME).write_text("\n".join(notes), encoding="utf-8")
        summary = {
            "format": RUN_FORMAT,
            "factory": FACTORY,
            "generator": GENERATOR,
            "mill_id": SOURCE_MILL_ID,
            "pairs": len(rounds),
            "quota_per_round": QUOTA_PER_ROUND,
            "records": len(records),
            "records_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "destination": str(out_dir),
        }
        (out_dir / RUN_FILENAME).write_text(
            dumps_exact_json(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except BaseException:
        for name in (RECORDS_FILENAME, NOTES_FILENAME, RUN_FILENAME):
            path = out_dir / name
            if path.exists():
                path.unlink()
        if out_dir.exists():
            out_dir.rmdir()
        raise
    return summary


bind_import_twin(__name__)
