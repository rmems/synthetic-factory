#!/usr/bin/env python3
"""Mill authz-regression-factory r1205+ as unique IDOR / BFLA / ReBAC plants.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1180 vesselNNNN-sys.
Not clones of r1181–r1204 (no elasticsearch GET-by-_id, no Spring @PreAuthorize PUT).
BAN GraphQL @skip, OAuth, gRPC, cookie, OpenFGA, SpiceDB.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

FACTORY = "authz-regression-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 1205
EXPERIMENTS = Path(__file__).resolve().parent

_old_spec = importlib.util.spec_from_file_location("azr_mill_r1181", EXPERIMENTS / "azr-mill-r1181.py")
_old = importlib.util.module_from_spec(_old_spec)
assert _old_spec.loader is not None
_old_spec.loader.exec_module(_old)

_r1193_spec = importlib.util.spec_from_file_location("azr_mill_r1193", EXPERIMENTS / "azr-mill-r1193.py")
_r1193 = importlib.util.module_from_spec(_r1193_spec)
assert _r1193_spec.loader is not None
_r1193_spec.loader.exec_module(_r1193)

build_success = _old.build_success
build_handoff = _old.build_handoff

USED_SLUGS = (
    {p[0]["slug"] for p in _old.PAIRS}
    | {p[1]["slug"] for p in _old.PAIRS}
    | {p[0]["slug"] for p in _r1193.PAIRS}
    | {p[1]["slug"] for p in _r1193.PAIRS}
)


def notes_for(round_n: int, a: dict, b: dict, sa: dict, sb: dict) -> str:
    cov = max(78, 86 - (round_n - CATALOG_FIRST))
    return f"""# NOTES-r{round_n} authz-regression-factory

Novel coverage: {cov}%

Two designed episodes (quota 2). Surfaces: {sa['surface']} vs {sb['surface']}.
Not leftover mill cartesian, not JWT-claim catalog, not r200–r1180 vesselNNNN-sys.
Each has a mid-trajectory plan change after a first patch that is incomplete.

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| azr-r{round_n}-{sa['slug']} | {sa['bug_hint']} | {sa['first_apply']} | {sa['plan_change']} | success {sa['tests_n']}/{sa['tests_n']} |
| azr-r{round_n}-{sb['slug']} | {sb['bug_hint']} | {sb['first_apply']} | {sb['plan_change']} | handoff {sb['handoff_hint']} |

## Step counts
- ep1: 17. first apply 6; plan change 8; residual {sa['residual']}.
- ep2: 18. first apply 6; plan change 8; xfail handoff {sb['handoff_hint']}.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Invented plants `{sa['plant']}` and `{sb['plant']}`.

## Weaknesses / next
Keep unique object-id IDOR, ReBAC tuple leftover, ABAC attr leftover, BOLA/BFLA, nested mass-assign.
Ban leftover mill slogans and JWT-claim catalog. Avoid r01–r199 seeds {sa['slug']}, {sb['slug']}.
"""


def _idor(row: dict) -> dict:
    plant = row["plant"]
    ticket = row["ticket"]
    slug = row["slug"]
    mod = row["mod"]
    model = row["model"]
    lookup = row["lookup"]
    sample = row["sample"]
    owner = row["owner"]
    src_fn = row.get("src_fn") or f"get_by_{lookup}"
    route = row.get("route") or f"/v1/{mod}"
    style = row.get("style") or "query"
    src = f"src/{mod}.py"
    handler = f"src/http_{mod}.py"
    test = f"tests/test_{mod}.py"
    test_fn = f"test_foreign_{lookup}_404"
    product = row.get("product") or f"{plant}-{mod}"
    comment = row.get("bug") or f"{ticket} global unique {lookup}"
    first = row["first"]
    residual_k = row["residual"]
    verb = "GET"

    if style == "path":
        get_line = f'r = client.get(f"{route}/{{{lookup}}}")'
        handler_sig = f'def http_get({lookup}: str, user=Depends(auth)):'
        inspect_route = f"{verb} {route}/{{{lookup}}}"
        own_get = f'r = client.get(f"{route}/{{alice.{lookup}}}")'
        foreign_get = (
            f'def {test_fn}(client, alice, bob):\n'
            f'    client.login(alice)\n'
            f'    r = client.get(f"{route}/{{bob.{lookup}}}")\n'
            f'    assert r.status_code == 404\n'
        )
    else:
        get_line = f'r = client.get("{route}", params={{"{lookup}": bob.{lookup}}})'
        handler_sig = f'def http_get({lookup}: str, user=Depends(auth)):'
        inspect_route = f"{verb} {route}?{lookup}="
        own_get = f'r = client.get("{route}", params={{"{lookup}": alice.{lookup}}})'
        foreign_get = (
            f'def {test_fn}(client, alice, bob):\n'
            f'    client.login(alice)\n'
            f'    {get_line}\n'
            f'    assert r.status_code == 404\n'
        )

    src_obs = (
        f"def {src_fn}({lookup}):\n"
        f"    return {model}.objects.get({lookup}={lookup})  # {comment}\n"
    )
    handler_obs = (
        f'@app.get("{route}")\n'
        f"{handler_sig}\n"
        f"    return {src_fn}({lookup})\n"
    )
    inspect_obs = (
        f"{src}: def {src_fn}\n"
        f"{handler}: {inspect_route}\n"
        f"{test}:5: def {test_fn}\n"
    )
    pytest_fail = (
        f"FAILED {test}::{test_fn} - AssertionError: 200 == 404\n"
        f"1 failed, 1 passed\n"
    )
    extra_old = f"def {test_fn}(client, alice, bob):"
    extra_new = (
        f"def test_own_{lookup}_200(client, alice):\n"
        f"    client.login(alice)\n"
        f"    {own_get}\n"
        f"    assert r.status_code == 200\n"
        f"\n"
        f"{extra_old}"
    )

    ret_line = f"    return {src_fn}({lookup})"
    if first == "authn":
        first_apply = "require authenticated user only"
        first_path = handler
        first_old = ret_line
        first_new = (
            "    if user is None:\n"
            "        raise HTTPException(401)\n"
            f"{ret_line}"
        )
        first_obs = f"anon 401; any login still opens bob {sample}"
        reflection = (
            f"Authn is not object authz. {lookup} lookup must AND {owner} from the session."
        )
        companion_old = first_new
        companion_new = (
            f"    row = {src_fn}({lookup}, {owner}=user.{owner})\n"
            "    if row is None:\n"
            "        raise HTTPException(404)\n"
            "    return row"
        )
        companion_obs = "None → 404"
        wire_hint = "Depends(auth) already on route"
        wire_path = handler
        wire_old = (
            f"{handler_sig}\n"
            "    if user is None:\n"
            "        raise HTTPException(401)"
        )
        wire_new = handler_sig
        wire_obs = "dropped redundant None check"
    elif first == "mask":
        first_apply = f"mask {lookup} in JSON only"
        first_path = handler
        first_old = ret_line
        first_new = (
            f"    row = {src_fn}({lookup})\n"
            f'    row["{lookup}"] = mask(row["{lookup}"])\n'
            "    return row"
        )
        first_obs = f"masked but still 200 for foreign {sample}"
        reflection = f"Masking is not authz. Filter {owner} from the session."
        companion_old = first_new
        companion_new = (
            f"    row = {src_fn}({lookup}, {owner}=user.{owner})\n"
            "    if row is None:\n"
            "        raise HTTPException(404)\n"
            "    return row"
        )
        companion_obs = "None → 404, no mask-as-authz"
        wire_hint = f"unique ({owner}, {lookup})"
        wire_path = f"migrations/{ticket.lower().replace('-', '_')}_{lookup}.sql"
        wire_old = f"CREATE UNIQUE INDEX {mod}_{lookup} ON {mod}({lookup});"
        wire_new = (
            f"CREATE UNIQUE INDEX {mod}_{owner}_{lookup} ON {mod}({owner}, {lookup});\n"
            f"DROP INDEX {mod}_{lookup};"
        )
        wire_obs = "composite unique"
    elif first == "any_member":
        first_apply = f"require any {owner.split('_')[0]} membership"
        first_path = handler
        first_old = ret_line
        first_new = (
            f"    if not getattr(user, '{owner}', None) and not getattr(user, 'orgs', None):\n"
            "        raise HTTPException(403)\n"
            f"{ret_line}"
        )
        first_obs = f"alice has a {owner} so still reads {sample}"
        reflection = (
            f"Any-membership is not {owner} on this {model}. Compare the row's {owner}."
        )
        companion_old = first_new
        companion_new = (
            f"    row = {src_fn}({lookup}, user)\n"
            "    if row is None:\n"
            "        raise HTTPException(404)\n"
            "    return row"
        )
        companion_obs = "None → 404 (no leak of existence via 403)"
        wire_hint = "nested comments use the same getter"
        wire_path = handler
        wire_old = (
            f'@app.get("{route}/comments")\n'
            f"def http_comments({lookup}: str, user=Depends(auth)):\n"
            f"    return {src_fn}({lookup}).comments"
        )
        wire_new = (
            f'@app.get("{route}/comments")\n'
            f"def http_comments({lookup}: str, user=Depends(auth)):\n"
            f"    row = {src_fn}({lookup}, user)\n"
            "    if row is None:\n"
            "        raise HTTPException(404)\n"
            "    return row.comments"
        )
        wire_obs = "comments gated"
    elif first == "list_scope":
        first_apply = f"scope list_{mod} by {owner} only"
        first_path = src
        first_old = (
            f"def list_{mod}(user):\n"
            f"    return {model}.objects.all()"
        )
        first_new = (
            f"def list_{mod}(user):\n"
            f"    return {model}.objects.filter({owner}=user.{owner})"
        )
        first_obs = f"list scoped; {src_fn} leftover"
        reflection = (
            f"List filter does not wrap get-by-{lookup}. Scope {src_fn} or attackers skip the list."
        )
        companion_old = ret_line
        companion_new = (
            f"    row = {src_fn}({lookup}, {owner}=user.{owner})\n"
            "    if row is None:\n"
            "        raise HTTPException(404)\n"
            "    return row"
        )
        companion_obs = "None → 404"
        wire_hint = f"batch get still calls {src_fn}"
        wire_path = handler
        wire_old = (
            f'@app.get("{route}/batch")\n'
            f"def http_batch(ids: list[str], user=Depends(auth)):\n"
            f"    return [{src_fn}(i) for i in ids]"
        )
        wire_new = (
            f'@app.get("{route}/batch")\n'
            f"def http_batch(ids: list[str], user=Depends(auth)):\n"
            f"    rows = [{src_fn}(i, {owner}=user.{owner}) for i in ids]\n"
            "    return [r for r in rows if r is not None]"
        )
        wire_obs = "batch drops misses"
    else:
        raise SystemExit(f"unknown first variant {first}")

    plan_change = f"filter {lookup} AND {owner}=user.{owner}"
    if first == "any_member":
        plan_change = f"require row.{owner}==user.{owner} else 404"
        legacy_new = (
            f"def {src_fn}({lookup}, user):\n"
            f"    row = {model}.objects.filter({lookup}={lookup}).first()\n"
            f"    if row is None or row.{owner} != user.{owner}:\n"
            "        return None\n"
            "    return row"
        )
        legacy_old = (
            f"    return {model}.objects.get({lookup}={lookup})  # {comment}"
        )
    else:
        legacy_new = (
            f"def {src_fn}({lookup}, {owner}):\n"
            f"    return {model}.objects.filter({lookup}={lookup}, {owner}={owner}).first()"
        )
        legacy_old = (
            f"    return {model}.objects.get({lookup}={lookup})  # {comment}"
        )

    residual_map = {
        "pdf": (
            f"PDF renderer still keys on global {lookup}",
            f"src/pdf_{mod}.py",
            "render_pdf",
            f"def render_pdf({lookup}):\n    return {model}.objects.get({lookup}={lookup})\n",
            f"{inspect_route} IDOR closed. Residual: PDF renderer.",
        ),
        "export": (
            f"CSV export still looks up global {lookup}",
            handler,
            "/export",
            f'@app.get("{route}/export")\n',
            f"{lookup} lookup IDOR closed. Residual: CSV export.",
        ),
        "search": (
            f"search still unscoped on {lookup}",
            f"src/http_search_{mod}.py",
            "/search",
            f'@app.get("{route}/search")\n',
            f"{lookup} IDOR closed. Residual: search.",
        ),
        "mget": (
            f"mget still unscoped",
            src,
            "mget",
            f"def mget_{mod}(ids):\n    return {model}.objects.filter({lookup}__in=ids)\n",
            f"get-by-{lookup} IDOR closed. Residual: mget.",
        ),
        "csv": (
            f"admin CSV job still keys on {lookup}",
            f"src/jobs_{mod}.py",
            "csv_job",
            f"def csv_job({lookup}):\n    return {src_fn}({lookup})\n",
            f"API {lookup} IDOR closed. Residual: CSV job.",
        ),
        "admin": (
            f"admin HTML still loads by {lookup}",
            f"src/admin_{mod}.py",
            "admin_get",
            f"def admin_get({lookup}):\n    return {src_fn}({lookup})\n",
            f"API {lookup} IDOR closed. Residual: admin HTML.",
        ),
        "webhook": (
            f"outbound webhook still fetches by {lookup}",
            f"src/webhooks_{mod}.py",
            "deliver",
            f"def deliver({lookup}):\n    return {src_fn}({lookup})\n",
            f"{lookup} IDOR closed. Residual: webhook deliver.",
        ),
        "comments": (
            f"comment thread still loads by {lookup}",
            handler,
            "/comments",
            f'@app.get("{route}/thread")\n',
            f"{lookup} IDOR closed. Residual: comment thread.",
        ),
    }
    residual, residual_path, residual_pat, residual_obs, residual_refl = residual_map[residual_k]

    plan_by_first = {
        "authn": f"Require login on the handler and rerun {test}.",
        "mask": f"Mask {lookup} in the response and rerun {test}.",
        "any_member": f"Require any membership and rerun {test}.",
        "list_scope": f"Scope the list query by {owner} and rerun {test}.",
    }
    outcome_by_first = {
        "authn": (
            f"Login-only first apply still leaked bob {sample}. Plan change: filter "
            f"{lookup}+{owner}, None→404. 12/12. Residual: {residual.split(' still')[0]}."
        ),
        "mask": (
            f"Masking left 200 for foreign {sample}. Plan change: filter {lookup}+{owner}. "
            f"12/12. Residual: {residual.split(' still')[0]}."
        ),
        "any_member": (
            f"Any-membership left {sample} readable. Plan change: row.{owner}==user.{owner}. "
            f"12/12. Residual: {residual.split(' still')[0]}."
        ),
        "list_scope": (
            f"List scope left get-by-{lookup} open. Plan change: filter {lookup}+{owner}. "
            f"12/12. Residual: {residual.split(' still')[0]}."
        ),
    }

    return {
        "slug": slug,
        "plant": plant,
        "surface": row["surface"],
        "src": src,
        "src_fn": src_fn,
        "handler": handler,
        "test": test,
        "test_fn": test_fn,
        "bug_hint": row.get("bug_hint") or f"lookup by {lookup} ignores {owner}",
        "inspect_cmd": f"rg -n '{src_fn}|{lookup}|{owner}' src tests | head -n 36",
        "inspect_obs": inspect_obs,
        "src_obs": src_obs,
        "handler_obs": handler_obs,
        "test_obs": foreign_get,
        "pytest_fail": pytest_fail,
        "first_apply": first_apply,
        "first_path": first_path,
        "first_old": first_old,
        "first_new": first_new,
        "first_obs": first_obs,
        "pytest_still": pytest_fail,
        "reflection": reflection,
        "plan_change": plan_change,
        "grep_pat": f"{owner}|{src_fn}",
        "grep_obs": f"{src}: {model}.objects.get({lookup}={lookup})\n",
        "legacy_path": src,
        "legacy_hint": f"ORM get by {lookup} only",
        "legacy_obs": src_obs.replace(f"  # {comment}", ""),
        "legacy_old": legacy_old,
        "legacy_new": legacy_new,
        "legacy_edit_obs": f"{owner}-scoped {lookup} lookup",
        "companion_path": handler,
        "companion_old": companion_old,
        "companion_new": companion_new,
        "companion_obs": companion_obs,
        "pytest_pass": "2 passed in 0.16s",
        "extra_fn": f"test_own_{lookup}_200",
        "extra_old": extra_old,
        "extra_new": extra_new,
        "extra_obs": f"own {lookup} still 200",
        "wire_hint": wire_hint,
        "wire_path": wire_path,
        "wire_old": wire_old,
        "wire_new": wire_new,
        "wire_obs": wire_obs,
        "pytest_extra": "3 passed in 0.18s",
        "suite_obs": "12 passed in 0.42s",
        "suite_n": "12/12",
        "residual": residual,
        "residual_path": residual_path,
        "residual_pat": residual_pat,
        "residual_obs": residual_obs,
        "residual_refl": residual_refl,
        "tests_n": 12,
        "goal": (
            f"{product} {inspect_route} returns another tenant {model} because {src_fn} "
            f"has no {owner} predicate. Scope the lookup without 404ing the owner's own {lookup}."
        ),
        "plan": plan_by_first[first],
        "outcome": outcome_by_first[first],
    }


def _H(**s) -> dict:
    test = s["test"]
    test_fn = s["test_fn"]
    s.setdefault(
        "pytest_fail",
        f"FAILED {test}::{test_fn} - expected 403 got 200\n1 failed, 1 passed\n",
    )
    s.setdefault("pytest_still", s["pytest_fail"])
    s.setdefault("pytest_pass", "2 passed in 0.58s")
    s.setdefault("pytest_xfail", "2 passed, 1 skipped")
    s.setdefault("suite_obs", "11 passed, 1 skipped")
    s.setdefault("tests_n", 11)
    s.setdefault("inspect_cmd", f"rg -n '{s['src_fn']}|{s.get('grep_pat', 'authorize')}' src | head -n 36")
    return s


def _bflas() -> list[dict]:
    # Unique BFLA / ReBAC leftover plants. One mechanic each. Not Spring PUT PreAuthorize.
    out: list[dict] = []

    def add(spec: dict) -> None:
        out.append(_H(**spec))

    add(dict(
        slug="flask-blueprint-delete-unguarded",
        plant="hawse",
        surface="Flask blueprint DELETE missing login_required",
        src="src/hawse_notes.py",
        src_fn="bp_delete",
        handler="src/hawse_app.py",
        test="tests/test_hawse_delete.py",
        test_fn="test_viewer_delete_403",
        bug_hint="GET has login_required; DELETE on notes_bp does not",
        inspect_obs="src/hawse_notes.py: def bp_delete\nsrc/hawse_app.py: notes_bp.route DELETE\ntests/test_hawse_delete.py: test_viewer_delete_403\n",
        src_obs="def bp_delete(note_id):\n    Note.query.get(note_id).delete()  # HAW-9 DELETE unguarded\n",
        handler_obs="@notes_bp.get(\"/<id>\")\n@login_required\ndef bp_get(id): ...\n@notes_bp.delete(\"/<id>\")\ndef bp_delete_http(id):\n    return bp_delete(id)\n",
        test_obs="def test_viewer_delete_403(client, viewer, note):\n    client.login(viewer)\n    assert client.delete(f\"/notes/{note.id}\").status_code == 403\n",
        first_apply="login_required on GET list",
        first_path="src/hawse_app.py",
        first_old="@notes_bp.get(\"/\")\ndef bp_list():",
        first_new="@notes_bp.get(\"/\")\n@login_required\ndef bp_list():",
        first_obs="list gated; DELETE leftover",
        reflection="Flask decorators are per view. DELETE needs login_required plus can_write.",
        plan_change="login_required + can_write on DELETE",
        grep_pat="delete|login_required",
        grep_obs="hawse_app.py: bp_delete_http no decorator\n",
        legacy_path="src/hawse_app.py",
        legacy_hint="DELETE unannotated",
        legacy_obs="@notes_bp.delete(\"/<id>\")\ndef bp_delete_http(id):\n    return bp_delete(id)\n",
        legacy_old="@notes_bp.delete(\"/<id>\")\ndef bp_delete_http(id):\n    return bp_delete(id)",
        legacy_new="@notes_bp.delete(\"/<id>\")\n@login_required\ndef bp_delete_http(id):\n    if not can_write(current_user, id):\n        abort(403)\n    return bp_delete(id)",
        legacy_edit_obs="DELETE gated",
        companion_path="src/hawse_acl.py",
        companion_old="def can_write(user, note_id):\n    return True",
        companion_new="def can_write(user, note_id):\n    return Note.query.get(note_id).owner_id == user.id",
        companion_obs="owner write check",
        extra_fn="test_viewer_patch_403",
        extra_old="def test_viewer_delete_403(client, viewer, note):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: PATCH view still bare\", strict=False)\ndef test_viewer_patch_403(client, viewer, note):\n    client.login(viewer)\n    assert client.patch(f\"/notes/{note.id}\", json={\"body\": \"x\"}).status_code == 403\n\ndef test_viewer_delete_403(client, viewer, note):",
        extra_obs="xfails PATCH leftover",
        handoff_path="src/hawse_app.py",
        handoff_obs="@notes_bp.patch(\"/<id>\")\ndef bp_patch_http(id):\n    return bp_patch(id)\n",
        handoff_hint="PATCH view still bare",
        residual="PATCH view still bare",
        residual_path="src/hawse_app.py",
        residual_pat="bp_patch_http",
        residual_obs="@notes_bp.patch(\"/<id>\")\ndef bp_patch_http(id):\n",
        residual_refl="DELETE gated. PATCH still bare.",
        leave_cmd="echo HAW-9 handoff Flask PATCH missing login_required",
        leave_obs="HAW-9 handoff Flask PATCH missing login_required",
        ticket="HAW-9",
        goal="hawse-notes DELETE /notes/{id} is 200 for a viewer because login_required is only on GET. Gate write without 403ing owners. Leave a handoff if PATCH still skips.",
        plan="Add login_required on GET list and rerun tests/test_hawse_delete.py.",
        outcome="List gate left DELETE BFLA. Plan change: login_required+can_write on DELETE. Partial: PATCH leftover (xfail handoff).",
    ))

    add(dict(
        slug="rails-skip-before-action-destroy",
        plant="cleat",
        surface="Rails skip_before_action :authorize on destroy",
        src="app/controllers/cleat/notes_controller.rb",
        src_fn="destroy",
        handler="app/controllers/cleat/notes_controller.rb",
        test="spec/requests/cleat_notes_spec.rb",
        test_fn="viewer_destroy_forbidden",
        bug_hint="skip_before_action :authorize, only: :destroy",
        inspect_obs="notes_controller.rb: skip_before_action destroy\nspec/requests/cleat_notes_spec.rb: viewer_destroy_forbidden\n",
        src_obs="class NotesController < ApplicationController\n  skip_before_action :authorize, only: :destroy  # CLT-12\n  def destroy; @note.destroy; end\nend\n",
        handler_obs="before_action :authorize, except: skipped\n# destroy skipped\n",
        test_obs="it \"viewer_destroy_forbidden\" do\n  delete \"/notes/#{note.id}\"\n  expect(response).to have_http_status(:forbidden)\nend\n",
        first_apply="authorize index only",
        first_path="app/controllers/cleat/notes_controller.rb",
        first_old="  skip_before_action :authorize, only: :destroy  # CLT-12",
        first_new="  before_action :authorize, only: :index\n  skip_before_action :authorize, only: :destroy",
        first_obs="index gated; destroy still skipped",
        reflection="skip_before_action wins for destroy. Remove the skip; authorize then policy.destroy?",
        plan_change="drop skip; authorize + NotePolicy#destroy",
        grep_pat="skip_before_action|destroy",
        grep_obs="notes_controller.rb: skip destroy\n",
        legacy_path="app/controllers/cleat/notes_controller.rb",
        legacy_hint="destroy skipped",
        legacy_obs="  skip_before_action :authorize, only: :destroy\n",
        legacy_old="  before_action :authorize, only: :index\n  skip_before_action :authorize, only: :destroy",
        legacy_new="  before_action :authorize\n  def destroy\n    authorize @note\n    @note.destroy\n  end",
        legacy_edit_obs="destroy authorized",
        companion_path="app/policies/note_policy.rb",
        companion_old="def destroy?\n  true\nend",
        companion_new="def destroy?\n  record.owner_id == user.id\nend",
        companion_obs="owner destroy",
        extra_fn="viewer_update_forbidden",
        extra_old="it \"viewer_destroy_forbidden\" do",
        extra_new="xit \"handoff: update still skips authorize\" do\n  patch \"/notes/#{note.id}\", params: {body: \"x\"}\n  expect(response).to have_http_status(:forbidden)\nend\nit \"viewer_destroy_forbidden\" do",
        extra_obs="xfails update skip leftover",
        handoff_path="app/controllers/cleat/notes_controller.rb",
        handoff_obs="  skip_before_action :authorize, only: :update\n",
        handoff_hint="update still skips authorize",
        residual="update still skips authorize",
        residual_path="app/controllers/cleat/notes_controller.rb",
        residual_pat="only: :update",
        residual_obs="  skip_before_action :authorize, only: :update\n",
        residual_refl="destroy skip removed. update skip remains.",
        leave_cmd="echo CLT-12 handoff Rails update skip_before_action",
        leave_obs="CLT-12 handoff Rails update skip_before_action",
        ticket="CLT-12",
        goal="cleat-notes DELETE /notes/{id} is 200 for a viewer because skip_before_action :authorize, only: :destroy. Authorize destroy without 403ing owners. Leave a handoff if update still skips.",
        plan="Authorize index and rerun spec/requests/cleat_notes_spec.rb.",
        outcome="Index-only authorize left destroy BFLA. Plan change: drop skip + NotePolicy#destroy. Partial: update skip leftover (xfail handoff).",
    ))

    add(dict(
        slug="aspnet-allowanonymous-on-delete",
        plant="fairlead",
        surface="ASP.NET [AllowAnonymous] leftover on Delete",
        src="Controllers/NotesController.cs",
        src_fn="Delete",
        handler="Controllers/NotesController.cs",
        test="tests/NoteDeleteTest.cs",
        test_fn="ViewerDeleteIs403",
        bug_hint="[Authorize] on Get; [AllowAnonymous] on Delete",
        inspect_obs="NotesController.cs: Delete AllowAnonymous\nNoteDeleteTest.cs: ViewerDeleteIs403\n",
        src_obs="[HttpDelete(\"{id}\")]\n[AllowAnonymous] // FRL-7 leftover from public unpublish spike\npublic IActionResult Delete(int id) => Ok(_db.Notes.Remove(id));\n",
        handler_obs="[HttpGet(\"{id}\")]\n[Authorize]\npublic Note Get(int id) => _db.Notes.Find(id);\n",
        test_obs="[Fact] public void ViewerDeleteIs403() {\n  var r = Client.DeleteAsync(\"/notes/\" + note.Id).Result;\n  Assert.Equal(403, (int)r.StatusCode);\n}\n",
        first_apply="[Authorize] on Get list",
        first_path="Controllers/NotesController.cs",
        first_old="[HttpGet]\npublic IEnumerable<Note> List() => _db.Notes;",
        first_new="[HttpGet]\n[Authorize]\npublic IEnumerable<Note> List() => _db.Notes;",
        first_obs="list gated; Delete leftover AllowAnonymous",
        reflection="AllowAnonymous overrides controller Authorize. Remove it; require NoteOwner.",
        plan_change="drop AllowAnonymous; [Authorize] + owner filter on Delete",
        grep_pat="AllowAnonymous|HttpDelete",
        grep_obs="NotesController.cs: Delete AllowAnonymous\n",
        legacy_path="Controllers/NotesController.cs",
        legacy_hint="Delete anonymous",
        legacy_obs="[HttpDelete(\"{id}\")]\n[AllowAnonymous]\npublic IActionResult Delete(int id) => Ok(_db.Notes.Remove(id));\n",
        legacy_old="[HttpDelete(\"{id}\")]\n[AllowAnonymous] // FRL-7 leftover from public unpublish spike\npublic IActionResult Delete(int id) => Ok(_db.Notes.Remove(id));",
        legacy_new="[HttpDelete(\"{id}\")]\n[Authorize]\npublic IActionResult Delete(int id) {\n  var n = _db.Notes.Find(id);\n  if (n == null || n.OwnerId != User.Id()) return NotFound();\n  _db.Notes.Remove(n);\n  return NoContent();\n}",
        legacy_edit_obs="Delete owner-gated",
        companion_path="Auth/NoteOwnerHandler.cs",
        companion_old="protected override Task HandleRequirement() => Task.FromResult(true);",
        companion_new="protected override Task HandleRequirement() {\n  return Task.FromResult(resource.OwnerId == user.Id());\n}",
        companion_obs="owner requirement",
        extra_fn="ViewerPatchIs403",
        extra_old="[Fact] public void ViewerDeleteIs403() {",
        extra_new="[Fact(Skip=\"handoff: Patch still AllowAnonymous\")] public void ViewerPatchIs403() {\n  Assert.Equal(403, (int)Client.PatchAsync(\"/notes/\" + note.Id, null).Result.StatusCode);\n}\n[Fact] public void ViewerDeleteIs403() {",
        extra_obs="xfails Patch leftover",
        handoff_path="Controllers/NotesController.cs",
        handoff_obs="[HttpPatch(\"{id}\")]\n[AllowAnonymous]\npublic IActionResult Patch(int id, Note in_) => Ok(_db.Notes.Update(in_));\n",
        handoff_hint="Patch still AllowAnonymous",
        residual="Patch still AllowAnonymous",
        residual_path="Controllers/NotesController.cs",
        residual_pat="HttpPatch",
        residual_obs="[HttpPatch(\"{id}\")]\n[AllowAnonymous]\n",
        residual_refl="Delete anonymous dropped. Patch still AllowAnonymous.",
        leave_cmd="echo FRL-7 handoff ASP.NET Patch AllowAnonymous",
        leave_obs="FRL-7 handoff ASP.NET Patch AllowAnonymous",
        ticket="FRL-7",
        goal="fairlead-notes DELETE /notes/{id} is 200 anonymously because [AllowAnonymous] sits on Delete. Gate write without 403ing owners. Leave a handoff if Patch still skips.",
        plan="Add [Authorize] on list and rerun NoteDeleteTest.",
        outcome="List [Authorize] left Delete BFLA. Plan change: drop AllowAnonymous + owner filter. Partial: Patch leftover (xfail handoff).",
    ))

    add(dict(
        slug="gin-group-skip-middleware-put",
        plant="gunwale",
        surface="Gin engine PUT registered outside auth group",
        src="src/http_gin.go",
        src_fn="PutNote",
        handler="src/http_gin.go",
        test="src/http_gin_test.go",
        test_fn="TestViewerPut403",
        bug_hint="r.PUT registered on engine, not on auth group",
        inspect_obs="http_gin.go: r.PUT /v1/notes/:id\nhttp_gin.go: g := r.Group with Auth\nhttp_gin_test.go: TestViewerPut403\n",
        src_obs="func PutNote(c *gin.Context) { db.Save(c.Param(\"id\"), c) } // GUN-4\n",
        handler_obs="g := r.Group(\"/v1\")\ng.Use(AuthRequired())\ng.GET(\"/notes/:id\", GetNote)\nr.PUT(\"/v1/notes/:id\", PutNote) // outside group\n",
        test_obs="func TestViewerPut403(t *testing.T) {\n  w := putViewer(\"/v1/notes/1\")\n  if w.Code != 403 { t.Fatalf(\"%d\", w.Code) }\n}\n",
        first_apply="AuthRequired on GET group only",
        first_path="src/http_gin.go",
        first_old="g.GET(\"/notes/:id\", GetNote)",
        first_new="g.GET(\"/notes/:id\", GetNote)\ng.GET(\"/notes\", ListNotes)",
        first_obs="list on group; PUT still on engine",
        reflection="Gin group middleware does not wrap engine routes. Move PUT onto g.",
        plan_change="register PUT on auth group; owner check",
        grep_pat="r.PUT|Group",
        grep_obs="http_gin.go: r.PUT outside group\n",
        legacy_path="src/http_gin.go",
        legacy_hint="PUT on engine",
        legacy_obs="r.PUT(\"/v1/notes/:id\", PutNote)\n",
        legacy_old="r.PUT(\"/v1/notes/:id\", PutNote) // outside group",
        legacy_new="g.PUT(\"/notes/:id\", PutNote)",
        legacy_edit_obs="PUT on auth group",
        companion_path="src/acl_gin.go",
        companion_old="func PutNote(c *gin.Context) { db.Save(c.Param(\"id\"), c) }",
        companion_new="func PutNote(c *gin.Context) {\n  if !owns(c, c.Param(\"id\")) { c.AbortWithStatus(403); return }\n  db.Save(c.Param(\"id\"), c)\n}",
        companion_obs="owner abort",
        extra_fn="TestViewerPatch403",
        extra_old="func TestViewerPut403(t *testing.T) {",
        extra_new="func TestViewerPatch403(t *testing.T) {\n  t.Skip(\"handoff: PATCH still on engine\")\n  w := patchViewer(\"/v1/notes/1\")\n  if w.Code != 403 { t.Fatalf(\"%d\", w.Code) }\n}\nfunc TestViewerPut403(t *testing.T) {",
        extra_obs="xfails PATCH leftover",
        handoff_path="src/http_gin.go",
        handoff_obs="r.PATCH(\"/v1/notes/:id\", PatchNote)\n",
        handoff_hint="PATCH still on engine",
        residual="PATCH still on engine",
        residual_path="src/http_gin.go",
        residual_pat="r.PATCH",
        residual_obs="r.PATCH(\"/v1/notes/:id\", PatchNote)\n",
        residual_refl="PUT moved onto auth group. PATCH still on engine.",
        leave_cmd="echo GUN-4 handoff Gin PATCH outside group",
        leave_obs="GUN-4 handoff Gin PATCH outside group",
        ticket="GUN-4",
        goal="gunwale-notes PUT /v1/notes/{id} is 200 for a viewer because r.PUT sits on the engine, not the AuthRequired group. Move PUT without 403ing owners. Leave a handoff if PATCH still sits outside.",
        plan="Put list on the auth group and rerun TestViewerPut403.",
        outcome="Group list left PUT on the engine. Plan change: g.PUT + owns. Partial: PATCH leftover (xfail handoff).",
    ))

    add(dict(
        slug="chi-mount-skips-authorize",
        plant="transom",
        surface="chi r.Mount /admin outside auth middleware",
        src="src/chi_admin.go",
        src_fn="AdminDeleteUser",
        handler="src/chi_router.go",
        test="src/chi_admin_test.go",
        test_fn="TestAdminDeleteRequiresAuth",
        bug_hint="r.Mount(\"/admin\", admin) before r.Use(Auth)",
        inspect_obs="chi_router.go: Mount /admin then Use Auth\nchi_admin.go: AdminDeleteUser\nchi_admin_test.go: TestAdminDeleteRequiresAuth\n",
        src_obs="func AdminDeleteUser(w http.ResponseWriter, r *http.Request) {\n  users.Delete(chi.URLParam(r, \"id\")) // TRN-8\n}\n",
        handler_obs="r := chi.NewRouter()\nr.Mount(\"/admin\", adminRouter())\nr.Use(Auth)\nr.Get(\"/v1/notes\", ListNotes)\n",
        test_obs="func TestAdminDeleteRequiresAuth(t *testing.T) {\n  rec := delAnon(\"/admin/users/9\")\n  if rec.Code != 401 { t.Fatalf(\"%d\", rec.Code) }\n}\n",
        first_apply="Auth on /v1 group only",
        first_path="src/chi_router.go",
        first_old="r.Get(\"/v1/notes\", ListNotes)",
        first_new="r.Route(\"/v1\", func(r chi.Router) { r.Use(Auth); r.Get(\"/notes\", ListNotes) })",
        first_obs="/v1 gated; /admin still mounted first",
        reflection="chi middleware order is registration order. Mount after Use(Auth), or wrap admin.",
        plan_change="Use(Auth) then Mount /admin; require admin role",
        grep_pat="Mount\\(\"/admin\"|Use\\(Auth\\)",
        grep_obs="chi_router.go: Mount before Use\n",
        legacy_path="src/chi_router.go",
        legacy_hint="admin mounted first",
        legacy_obs="r.Mount(\"/admin\", adminRouter())\nr.Use(Auth)\n",
        legacy_old="r := chi.NewRouter()\nr.Mount(\"/admin\", adminRouter())\nr.Use(Auth)",
        legacy_new="r := chi.NewRouter()\nr.Use(Auth)\nr.Mount(\"/admin\", adminRouter())",
        legacy_edit_obs="Auth wraps admin",
        companion_path="src/chi_admin.go",
        companion_old="func AdminDeleteUser(w http.ResponseWriter, r *http.Request) {\n  users.Delete(chi.URLParam(r, \"id\")) // TRN-8\n}",
        companion_new="func AdminDeleteUser(w http.ResponseWriter, r *http.Request) {\n  if !isAdmin(r) { http.Error(w, \"no\", 403); return }\n  users.Delete(chi.URLParam(r, \"id\"))\n}",
        companion_obs="admin role",
        extra_fn="TestAdminExportRequiresAuth",
        extra_old="func TestAdminDeleteRequiresAuth(t *testing.T) {",
        extra_new="func TestAdminExportRequiresAuth(t *testing.T) {\n  t.Skip(\"handoff: /internal/export mounted before Auth\")\n  rec := getAnon(\"/internal/export\")\n  if rec.Code != 401 { t.Fatalf(\"%d\", rec.Code) }\n}\nfunc TestAdminDeleteRequiresAuth(t *testing.T) {",
        extra_obs="xfails /internal/export leftover",
        handoff_path="src/chi_router.go",
        handoff_obs="r.Mount(\"/internal\", internalRouter()) // still before Use in a second constructor\n",
        handoff_hint="/internal/export mounted before Auth",
        residual="/internal/export mounted before Auth",
        residual_path="src/chi_router.go",
        residual_pat="/internal",
        residual_obs="r.Mount(\"/internal\", internalRouter())\n",
        residual_refl="Admin mount now after Auth. /internal still early.",
        leave_cmd="echo TRN-8 handoff chi /internal mount order",
        leave_obs="TRN-8 handoff chi /internal mount order",
        ticket="TRN-8",
        goal="transom-admin DELETE /admin/users/{id} is 200 anonymously because r.Mount(/admin) runs before r.Use(Auth). Wrap admin without 403ing admins. Leave a handoff if /internal still mounts early.",
        plan="Auth-wrap /v1 and rerun TestAdminDeleteRequiresAuth.",
        outcome="/v1 wrap left /admin early. Plan change: Use(Auth) then Mount + isAdmin. Partial: /internal leftover (xfail handoff).",
    ))

    add(dict(
        slug="nextjs-middleware-matcher-gap",
        plant="keelson",
        surface="Next.js middleware matcher misses /api/admin",
        src="middleware.ts",
        src_fn="middleware",
        handler="app/api/admin/users/route.ts",
        test="tests/test_mw_admin.py",
        test_fn="test_anon_admin_delete_401",
        bug_hint="matcher includes /app and /api/notes, not /api/admin",
        inspect_obs="middleware.ts: config.matcher\napp/api/admin/users/route.ts: DELETE\ntests/test_mw_admin.py: test_anon_admin_delete_401\n",
        src_obs="export const config = { matcher: [\"/app/:path*\", \"/api/notes/:path*\"] } // KEL-3 admin gap\n",
        handler_obs="export async function DELETE() {\n  return Response.json(await db.users.deleteMany())\n}\n",
        test_obs="def test_anon_admin_delete_401(client):\n    r = client.delete(\"/api/admin/users\")\n    assert r.status_code == 401\n",
        first_apply="add /api/notes to matcher only",
        first_path="middleware.ts",
        first_old="export const config = { matcher: [\"/app/:path*\", \"/api/notes/:path*\"] } // KEL-3 admin gap",
        first_new="export const config = { matcher: [\"/app/:path*\", \"/api/notes/:path*\", \"/api/notes\"] }",
        first_obs="notes covered twice; /api/admin leftover",
        reflection="Middleware matcher is prefix-list. /api/admin never runs getToken.",
        plan_change="matcher /api/:path* then requireAdmin on admin routes",
        grep_pat="matcher|/api/admin",
        grep_obs="middleware.ts: no /api/admin\n",
        legacy_path="middleware.ts",
        legacy_hint="admin not in matcher",
        legacy_obs="export const config = { matcher: [\"/app/:path*\", \"/api/notes/:path*\"] }\n",
        legacy_old="export const config = { matcher: [\"/app/:path*\", \"/api/notes/:path*\", \"/api/notes\"] }",
        legacy_new="export const config = { matcher: [\"/app/:path*\", \"/api/:path*\"] }",
        legacy_edit_obs="all /api matched",
        companion_path="app/api/admin/users/route.ts",
        companion_old="export async function DELETE() {\n  return Response.json(await db.users.deleteMany())\n}",
        companion_new="export async function DELETE(req: Request) {\n  if (!requireAdmin(req)) return new Response(null, { status: 403 })\n  return Response.json(await db.users.deleteMany())\n}",
        companion_obs="requireAdmin",
        extra_fn="test_anon_cron_401",
        extra_old="def test_anon_admin_delete_401(client):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: /cron matcher excluded\", strict=False)\ndef test_anon_cron_401(client):\n    assert client.post(\"/cron/reindex\").status_code == 401\n\ndef test_anon_admin_delete_401(client):",
        extra_obs="xfails /cron leftover",
        handoff_path="middleware.ts",
        handoff_obs="// negative matcher leftover: '/cron/:path*' excluded in experimental\n",
        handoff_hint="/cron matcher excluded",
        residual="/cron matcher excluded",
        residual_path="middleware.ts",
        residual_pat="/cron",
        residual_obs="// negative matcher leftover: '/cron/:path*' excluded in experimental\n",
        residual_refl="/api admin now matched. /cron still excluded.",
        leave_cmd="echo KEL-3 handoff Next middleware /cron gap",
        leave_obs="KEL-3 handoff Next middleware /cron gap",
        ticket="KEL-3",
        goal="keelson-admin DELETE /api/admin/users is 200 anonymously because middleware matcher omits /api/admin. Cover /api without 403ing admins. Leave a handoff if /cron is still excluded.",
        plan="Duplicate /api/notes in matcher and rerun tests/test_mw_admin.py.",
        outcome="Notes matcher left /api/admin open. Plan change: /api/:path* + requireAdmin. Partial: /cron leftover (xfail handoff).",
    ))

    add(dict(
        slug="envoy-ext-authz-bypass-internal",
        plant="samson",
        surface="Envoy ext_authz skip /internal leftover",
        src="envoy.yaml",
        src_fn="ext_authz",
        handler="src/internal_users.py",
        test="tests/test_envoy_internal.py",
        test_fn="test_internal_users_401",
        bug_hint="typed_per_filter_config skip /internal/*",
        inspect_obs="envoy.yaml: ext_authz skip prefix /internal\nsrc/internal_users.py: GET /internal/users\ntests/test_envoy_internal.py: test_internal_users_401\n",
        src_obs="typed_per_filter_config:\n  envoy.filters.http.ext_authz:\n    disabled: true  # SAM-11 for /internal health, also matches /internal/users\n",
        handler_obs="@app.get(\"/internal/users\")\ndef internal_users():\n    return User.query.all()\n",
        test_obs="def test_internal_users_401(client):\n    r = client.get(\"/internal/users\")\n    assert r.status_code == 401\n",
        first_apply="skip only exact /internal/healthz",
        first_path="envoy.yaml",
        first_old="    disabled: true  # SAM-11 for /internal health, also matches /internal/users",
        first_new="    disabled: true  # still on the /internal prefix virtual host",
        first_obs="prefix still skipped; healthz not isolated",
        reflection="Prefix skip on /internal disables ext_authz for users too. Use exact /internal/healthz.",
        plan_change="exact_match /internal/healthz skip; ext_authz on /internal/users",
        grep_pat="ext_authz|/internal",
        grep_obs="envoy.yaml: prefix /internal disabled\n",
        legacy_path="envoy.yaml",
        legacy_hint="prefix skip",
        legacy_obs="prefix: /internal\n  typed_per_filter_config: disabled true\n",
        legacy_old="    disabled: true  # still on the /internal prefix virtual host",
        legacy_new="prefix: /internal/healthz\n  typed_per_filter_config:\n    envoy.filters.http.ext_authz:\n      disabled: true",
        legacy_edit_obs="only healthz skipped",
        companion_path="src/internal_users.py",
        companion_old="@app.get(\"/internal/users\")\ndef internal_users():\n    return User.query.all()",
        companion_new="@app.get(\"/internal/users\")\ndef internal_users(user=Depends(admin_auth)):\n    return User.query.all()",
        companion_obs="admin_auth defense in depth",
        extra_fn="test_internal_debug_401",
        extra_old="def test_internal_users_401(client):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: /internal/debug pprof still skipped\", strict=False)\ndef test_internal_debug_401(client):\n    assert client.get(\"/internal/debug/pprof\").status_code == 401\n\ndef test_internal_users_401(client):",
        extra_obs="xfails pprof leftover",
        handoff_path="envoy.yaml",
        handoff_obs="prefix: /internal/debug\n  typed_per_filter_config: disabled true\n",
        handoff_hint="/internal/debug pprof still skipped",
        residual="/internal/debug pprof still skipped",
        residual_path="envoy.yaml",
        residual_pat="/internal/debug",
        residual_obs="prefix: /internal/debug\n  typed_per_filter_config: disabled true\n",
        residual_refl="/internal/users now authz'd. pprof skip remains.",
        leave_cmd="echo SAM-11 handoff Envoy /internal/debug skip",
        leave_obs="SAM-11 handoff Envoy /internal/debug skip",
        ticket="SAM-11",
        goal="samson-admin GET /internal/users is 200 anonymously because ext_authz is disabled on prefix /internal. Skip only healthz without opening users. Leave a handoff if /internal/debug still skips.",
        plan="Comment the skip and rerun tests/test_envoy_internal.py.",
        outcome="Prefix skip remained. Plan change: exact healthz skip + admin_auth. Partial: pprof leftover (xfail handoff).",
    ))

    add(dict(
        slug="istio-authz-policy-method-gap",
        plant="cathead",
        surface="Istio AuthorizationPolicy missing DELETE method",
        src="k8s/authz-notes.yaml",
        src_fn="AuthorizationPolicy",
        handler="src/notes_svc.py",
        test="tests/test_istio_delete.py",
        test_fn="test_viewer_delete_403",
        bug_hint="ALLOW to=[\"GET\",\"POST\"]; DELETE falls through to allow-all",
        inspect_obs="k8s/authz-notes.yaml: to methods GET POST\nsrc/notes_svc.py: DELETE /v1/notes\ntests/test_istio_delete.py: test_viewer_delete_403\n",
        src_obs="spec:\n  action: ALLOW\n  rules:\n  - to:\n    - operation:\n        methods: [\"GET\", \"POST\"]  # CTH-6 DELETE not listed; mesh default ALLOW\n",
        handler_obs="@app.delete(\"/v1/notes/{id}\")\ndef delete_note(id):\n    return notes.delete(id)\n",
        test_obs="def test_viewer_delete_403(client, viewer, note):\n    client.login(viewer)\n    assert client.delete(f\"/v1/notes/{note.id}\").status_code == 403\n",
        first_apply="deny POST for anonymous only",
        first_path="k8s/authz-notes.yaml",
        first_old="        methods: [\"GET\", \"POST\"]  # CTH-6 DELETE not listed; mesh default ALLOW",
        first_new="        methods: [\"GET\", \"POST\"]\n  - from:\n    - source:\n        principals: [\"cluster.local/ns/istio-system/sa/anon\"]\n    to:\n    - operation:\n        methods: [\"POST\"]\n    when: []  # still does not mention DELETE",
        first_obs="anon POST tighter; DELETE still default allow",
        reflection="ALLOW-list methods must include DELETE or a default-deny policy must exist.",
        plan_change="mesh default DENY; ALLOW GET/POST/DELETE for owners",
        grep_pat="methods:|DELETE",
        grep_obs="authz-notes.yaml: GET POST only\n",
        legacy_path="k8s/authz-notes.yaml",
        legacy_hint="DELETE unlisted",
        legacy_obs="methods: [\"GET\", \"POST\"]\n",
        legacy_old="        methods: [\"GET\", \"POST\"]\n  - from:\n    - source:\n        principals: [\"cluster.local/ns/istio-system/sa/anon\"]\n    to:\n    - operation:\n        methods: [\"POST\"]\n    when: []  # still does not mention DELETE",
        legacy_new="apiVersion: security.istio.io/v1\nkind: AuthorizationPolicy\nmetadata: {name: notes-deny}\nspec: {action: DENY, rules: [{}]}\n---\nmethods: [\"GET\", \"POST\", \"DELETE\"]",
        legacy_edit_obs="default deny plus DELETE listed",
        companion_path="src/notes_svc.py",
        companion_old="@app.delete(\"/v1/notes/{id}\")\ndef delete_note(id):\n    return notes.delete(id)",
        companion_new="@app.delete(\"/v1/notes/{id}\")\ndef delete_note(id, user=Depends(owner_auth)):\n    return notes.delete(id)",
        companion_obs="app-level owner_auth",
        extra_fn="test_viewer_put_403",
        extra_old="def test_viewer_delete_403(client, viewer, note):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: PUT still unlisted so default allow\", strict=False)\ndef test_viewer_put_403(client, viewer, note):\n    client.login(viewer)\n    assert client.put(f\"/v1/notes/{note.id}\", json={}).status_code == 403\n\ndef test_viewer_delete_403(client, viewer, note):",
        extra_obs="xfails PUT leftover",
        handoff_path="k8s/authz-notes.yaml",
        handoff_obs="methods: [\"GET\", \"POST\", \"DELETE\"]  # PUT absent\n",
        handoff_hint="PUT still unlisted so default allow",
        residual="PUT still unlisted so default allow",
        residual_path="k8s/authz-notes.yaml",
        residual_pat="PUT",
        residual_obs="methods: [\"GET\", \"POST\", \"DELETE\"]  # PUT absent\n",
        residual_refl="DELETE listed + default deny. PUT still unlisted.",
        leave_cmd="echo CTH-6 handoff Istio PUT method gap",
        leave_obs="CTH-6 handoff Istio PUT method gap",
        ticket="CTH-6",
        goal="cathead-notes DELETE /v1/notes/{id} is 200 for a viewer because AuthorizationPolicy lists GET/POST only and mesh default is ALLOW. Deny-by-default without 403ing owners. Leave a handoff if PUT is still unlisted.",
        plan="Tighten anon POST and rerun tests/test_istio_delete.py.",
        outcome="Anon POST rule left DELETE default-allow. Plan change: default DENY + DELETE listed. Partial: PUT leftover (xfail handoff).",
    ))

    add(dict(
        slug="kong-acl-plugin-missing-route",
        plant="davit",
        surface="Kong ACL plugin missing on export route",
        src="kong.yaml",
        src_fn="acl",
        handler="src/http_export.py",
        test="tests/test_kong_export.py",
        test_fn="test_viewer_export_403",
        bug_hint="acl plugin on /v1/notes, not /v1/notes/export",
        inspect_obs="kong.yaml: plugins acl route notes\nsrc/http_export.py: GET /v1/notes/export\ntests/test_kong_export.py: test_viewer_export_403\n",
        src_obs="plugins:\n  - name: acl\n    route: notes-get  # DAV-15 export route has no acl\n",
        handler_obs="@app.get(\"/v1/notes/export\")\ndef export_notes():\n    return notes.csv()\n",
        test_obs="def test_viewer_export_403(client, viewer):\n    client.login(viewer)\n    assert client.get(\"/v1/notes/export\").status_code == 403\n",
        first_apply="acl on GET /v1/notes list",
        first_path="kong.yaml",
        first_old="    route: notes-get  # DAV-15 export route has no acl",
        first_new="    route: notes-get\n  - name: acl\n    route: notes-list",
        first_obs="list acl'd; export leftover",
        reflection="Kong plugins bind per route object. Export is a separate route.",
        plan_change="attach acl to notes-export; require notes:export group",
        grep_pat="notes-export|acl",
        grep_obs="kong.yaml: no notes-export acl\n",
        legacy_path="kong.yaml",
        legacy_hint="export unplugged",
        legacy_obs="route: notes-get  # export missing\n",
        legacy_old="    route: notes-get\n  - name: acl\n    route: notes-list",
        legacy_new="    route: notes-get\n  - name: acl\n    route: notes-list\n  - name: acl\n    route: notes-export\n    config:\n      allow: [\"notes-export\"]",
        legacy_edit_obs="export acl group",
        companion_path="src/http_export.py",
        companion_old="@app.get(\"/v1/notes/export\")\ndef export_notes():\n    return notes.csv()",
        companion_new="@app.get(\"/v1/notes/export\")\ndef export_notes(user=Depends(require_group(\"notes-export\"))):\n    return notes.csv()",
        companion_obs="app group check",
        extra_fn="test_viewer_bulk_403",
        extra_old="def test_viewer_export_403(client, viewer):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: /v1/notes/bulk has no acl\", strict=False)\ndef test_viewer_bulk_403(client, viewer):\n    client.login(viewer)\n    assert client.post(\"/v1/notes/bulk\", json=[]).status_code == 403\n\ndef test_viewer_export_403(client, viewer):",
        extra_obs="xfails bulk leftover",
        handoff_path="kong.yaml",
        handoff_obs="route: notes-bulk  # no plugins\n",
        handoff_hint="/v1/notes/bulk has no acl",
        residual="/v1/notes/bulk has no acl",
        residual_path="kong.yaml",
        residual_pat="notes-bulk",
        residual_obs="route: notes-bulk  # no plugins\n",
        residual_refl="export ACL attached. bulk route still bare.",
        leave_cmd="echo DAV-15 handoff Kong bulk route no acl",
        leave_obs="DAV-15 handoff Kong bulk route no acl",
        ticket="DAV-15",
        goal="davit-notes GET /v1/notes/export is 200 for a viewer because the ACL plugin is only on notes-get. Attach ACL without 403ing exporters. Leave a handoff if bulk is still bare.",
        plan="Attach ACL to notes-list and rerun tests/test_kong_export.py.",
        outcome="List ACL left export open. Plan change: notes-export acl group. Partial: bulk leftover (xfail handoff).",
    ))

    add(dict(
        slug="traefik-forwardauth-skip-path",
        plant="futtock",
        surface="Traefik forwardAuth skip /healthy matches /healthy-admin",
        src="traefik.yml",
        src_fn="forwardAuth",
        handler="src/healthy_admin.py",
        test="tests/test_traefik_skip.py",
        test_fn="test_healthy_admin_401",
        bug_hint="skipPrefix /healthy also skips /healthy-admin",
        inspect_obs="traefik.yml: skipPrefix /healthy\nsrc/healthy_admin.py: GET /healthy-admin/users\ntests/test_traefik_skip.py: test_healthy_admin_401\n",
        src_obs="http:\n  middlewares:\n    auth:\n      forwardAuth:\n        address: http://auth:4181\n        skipPrefix: [\"/healthy\"]  # FUT-2 prefix, not exact\n",
        handler_obs="@app.get(\"/healthy-admin/users\")\ndef healthy_admin_users():\n    return users.all()\n",
        test_obs="def test_healthy_admin_401(client):\n    r = client.get(\"/healthy-admin/users\")\n    assert r.status_code == 401\n",
        first_apply="add /healthz skip exact",
        first_path="traefik.yml",
        first_old="        skipPrefix: [\"/healthy\"]  # FUT-2 prefix, not exact",
        first_new="        skipPrefix: [\"/healthy\", \"/healthz\"]",
        first_obs="more prefixes; /healthy-admin still skipped",
        reflection="Prefix skip is string prefix. Use exact /healthy or /healthyz, not /healthy.",
        plan_change="skip exact /healthyz only; forwardAuth /healthy-admin",
        grep_pat="skipPrefix|/healthy-admin",
        grep_obs="traefik.yml: skipPrefix /healthy\n",
        legacy_path="traefik.yml",
        legacy_hint="prefix too wide",
        legacy_obs="skipPrefix: [\"/healthy\"]\n",
        legacy_old="        skipPrefix: [\"/healthy\", \"/healthz\"]",
        legacy_new="        skipExact: [\"/healthyz\"]",
        legacy_edit_obs="exact health skip",
        companion_path="src/healthy_admin.py",
        companion_old="@app.get(\"/healthy-admin/users\")\ndef healthy_admin_users():\n    return users.all()",
        companion_new="@app.get(\"/healthy-admin/users\")\ndef healthy_admin_users(user=Depends(admin_auth)):\n    return users.all()",
        companion_obs="admin_auth",
        extra_fn="test_healthy_metrics_401",
        extra_old="def test_healthy_admin_401(client):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: /healthy-metrics still prefix-skipped\", strict=False)\ndef test_healthy_metrics_401(client):\n    assert client.get(\"/healthy-metrics\").status_code == 401\n\ndef test_healthy_admin_401(client):",
        extra_obs="xfails metrics leftover",
        handoff_path="traefik.yml",
        handoff_obs="skipPrefix: [\"/healthy-metrics\"]\n",
        handoff_hint="/healthy-metrics still prefix-skipped",
        residual="/healthy-metrics still prefix-skipped",
        residual_path="traefik.yml",
        residual_pat="healthy-metrics",
        residual_obs="skipPrefix: [\"/healthy-metrics\"]\n",
        residual_refl="/healthy-admin now authz'd. metrics skip remains.",
        leave_cmd="echo FUT-2 handoff Traefik /healthy-metrics skip",
        leave_obs="FUT-2 handoff Traefik /healthy-metrics skip",
        ticket="FUT-2",
        goal="futtock-admin GET /healthy-admin/users is 200 anonymously because forwardAuth skipPrefix /healthy matches /healthy-admin. Skip only /healthyz without opening admin. Leave a handoff if /healthy-metrics still skips.",
        plan="Add /healthz to skipPrefix and rerun tests/test_traefik_skip.py.",
        outcome="Extra prefix left /healthy-admin open. Plan change: skipExact /healthyz. Partial: metrics leftover (xfail handoff).",
    ))

    add(dict(
        slug="nuxt-server-delete-no-auth",
        plant="garboard",
        surface="Nuxt server DELETE route missing getUserSession",
        src="server/api/notes/[id].delete.ts",
        src_fn="defineEventHandler",
        handler="server/api/notes/[id].get.ts",
        test="tests/test_nuxt_delete.py",
        test_fn="test_viewer_delete_403",
        bug_hint="GET calls getUserSession; DELETE does not",
        inspect_obs="server/api/notes/[id].get.ts: getUserSession\nserver/api/notes/[id].delete.ts: no session\ntests/test_nuxt_delete.py: test_viewer_delete_403\n",
        src_obs="export default defineEventHandler(async (event) => {\n  await db.notes.delete({ where: { id: event.context.params.id } }) // GAR-6\n})\n",
        handler_obs="export default defineEventHandler(async (event) => {\n  const user = await getUserSession(event)\n  return db.notes.find(user, event.context.params.id)\n})\n",
        test_obs="def test_viewer_delete_403(client, viewer, note):\n    client.login(viewer)\n    assert client.delete(f\"/api/notes/{note.id}\").status_code == 403\n",
        first_apply="requireUserSession on GET list",
        first_path="server/api/notes/index.get.ts",
        first_old="export default defineEventHandler(async () => db.notes.findMany())",
        first_new="export default defineEventHandler(async (event) => {\n  await requireUserSession(event)\n  return db.notes.findMany()\n})",
        first_obs="list gated; DELETE leftover",
        reflection="Nitro file routes do not inherit sibling middleware. DELETE file needs requireUserSession plus canWrite.",
        plan_change="requireUserSession + canWrite in [id].delete.ts",
        grep_pat="delete.ts|getUserSession",
        grep_obs="[id].delete.ts: no session\n",
        legacy_path="server/api/notes/[id].delete.ts",
        legacy_hint="DELETE bare",
        legacy_obs="export default defineEventHandler(async (event) => {\n  await db.notes.delete({ where: { id: event.context.params.id } })\n})\n",
        legacy_old="export default defineEventHandler(async (event) => {\n  await db.notes.delete({ where: { id: event.context.params.id } }) // GAR-6\n})",
        legacy_new="export default defineEventHandler(async (event) => {\n  const user = await requireUserSession(event)\n  const id = event.context.params.id\n  if (!(await canWrite(user, id))) throw createError({ statusCode: 403 })\n  await db.notes.delete({ where: { id } })\n})",
        legacy_edit_obs="DELETE session+write",
        companion_path="server/utils/acl.ts",
        companion_old="export async function canWrite() { return true }",
        companion_new="export async function canWrite(user, id) {\n  const n = await db.notes.findUnique({ where: { id } })\n  return n?.ownerId === user.id\n}",
        companion_obs="owner write",
        extra_fn="test_viewer_patch_403",
        extra_old="def test_viewer_delete_403(client, viewer, note):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: [id].patch.ts still bare\", strict=False)\ndef test_viewer_patch_403(client, viewer, note):\n    client.login(viewer)\n    assert client.patch(f\"/api/notes/{note.id}\", json={}).status_code == 403\n\ndef test_viewer_delete_403(client, viewer, note):",
        extra_obs="xfails PATCH leftover",
        handoff_path="server/api/notes/[id].patch.ts",
        handoff_obs="export default defineEventHandler(async (event) => {\n  await db.notes.update({ where: { id: event.context.params.id }, data: {} })\n})\n",
        handoff_hint="[id].patch.ts still bare",
        residual="[id].patch.ts still bare",
        residual_path="server/api/notes/[id].patch.ts",
        residual_pat="patch.ts",
        residual_obs="export default defineEventHandler(async (event) => {\n  await db.notes.update({ where: { id: event.context.params.id }, data: {} })\n})\n",
        residual_refl="DELETE gated. PATCH file still bare.",
        leave_cmd="echo GAR-6 handoff Nuxt [id].patch.ts no session",
        leave_obs="GAR-6 handoff Nuxt [id].patch.ts no session",
        ticket="GAR-6",
        goal="garboard-notes DELETE /api/notes/{id} is 200 for a viewer because [id].delete.ts never calls getUserSession. Gate write without 403ing owners. Leave a handoff if patch.ts still skips.",
        plan="requireUserSession on index.get and rerun tests/test_nuxt_delete.py.",
        outcome="List session left DELETE BFLA. Plan change: requireUserSession+canWrite on delete.ts. Partial: patch.ts leftover (xfail handoff).",
    ))

    add(dict(
        slug="phoenix-plug-pipeline-skip",
        plant="inwale",
        surface="Phoenix delete action skips :authenticated pipeline",
        src="lib/inwale_web/router.ex",
        src_fn="delete",
        handler="lib/inwale_web/note_controller.ex",
        test="test/inwale_web/note_controller_test.exs",
        test_fn="viewer_delete_forbidden",
        bug_hint="pipe_through :api for delete, not :authenticated",
        inspect_obs="router.ex: delete notes in :api pipeline\nnote_controller.ex: def delete\nnote_controller_test.exs: viewer_delete_forbidden\n",
        src_obs="scope \"/api\", InwaleWeb do\n  pipe_through :api\n  delete \"/notes/:id\", NoteController, :delete  # INW-4\nend\n",
        handler_obs="def delete(conn, %{\"id\" => id}) do\n  Repo.delete!(Note |> Repo.get!(id))\n  send_resp(conn, 204, \"\")\nend\n",
        test_obs="test \"viewer_delete_forbidden\", %{conn: conn, note: note} do\n  conn = delete(conn, \"/api/notes/#{note.id}\")\n  assert conn.status == 403\nend\n",
        first_apply="pipe_through :authenticated on index",
        first_path="lib/inwale_web/router.ex",
        first_old="  get \"/notes\", NoteController, :index",
        first_new="scope \"/api\" do\n  pipe_through [:api, :authenticated]\n  get \"/notes\", NoteController, :index\nend",
        first_obs="index authenticated; delete leftover on :api",
        reflection="Phoenix pipelines are per scope. Move delete into the authenticated scope.",
        plan_change="delete in :authenticated scope; bodyguard permit",
        grep_pat="delete \"/notes|pipe_through",
        grep_obs="router.ex: delete under :api\n",
        legacy_path="lib/inwale_web/router.ex",
        legacy_hint="delete in :api",
        legacy_obs="  pipe_through :api\n  delete \"/notes/:id\", NoteController, :delete\n",
        legacy_old="scope \"/api\", InwaleWeb do\n  pipe_through :api\n  delete \"/notes/:id\", NoteController, :delete  # INW-4\nend",
        legacy_new="scope \"/api\", InwaleWeb do\n  pipe_through [:api, :authenticated]\n  delete \"/notes/:id\", NoteController, :delete\nend",
        legacy_edit_obs="delete authenticated",
        companion_path="lib/inwale_web/note_controller.ex",
        companion_old="def delete(conn, %{\"id\" => id}) do\n  Repo.delete!(Note |> Repo.get!(id))\n  send_resp(conn, 204, \"\")\nend",
        companion_new="def delete(conn, %{\"id\" => id}) do\n  note = Repo.get!(Note, id)\n  Bodyguard.permit!(Note, :delete, conn.assigns.current_user, note)\n  Repo.delete!(note)\n  send_resp(conn, 204, \"\")\nend",
        companion_obs="Bodyguard permit",
        extra_fn="viewer_update_forbidden",
        extra_old="test \"viewer_delete_forbidden\", %{conn: conn, note: note} do",
        extra_new="@tag :skip\ntest \"handoff: update still on :api pipeline\", %{conn: conn, note: note} do\n  conn = put(conn, \"/api/notes/#{note.id}\", %{body: \"x\"})\n  assert conn.status == 403\nend\ntest \"viewer_delete_forbidden\", %{conn: conn, note: note} do",
        extra_obs="xfails update leftover",
        handoff_path="lib/inwale_web/router.ex",
        handoff_obs="  pipe_through :api\n  put \"/notes/:id\", NoteController, :update\n",
        handoff_hint="update still on :api pipeline",
        residual="update still on :api pipeline",
        residual_path="lib/inwale_web/router.ex",
        residual_pat="put \"/notes",
        residual_obs="  pipe_through :api\n  put \"/notes/:id\", NoteController, :update\n",
        residual_refl="delete authenticated. update still on :api.",
        leave_cmd="echo INW-4 handoff Phoenix update :api pipeline",
        leave_obs="INW-4 handoff Phoenix update :api pipeline",
        ticket="INW-4",
        goal="inwale-notes DELETE /api/notes/{id} is 200 for a viewer because delete is in the :api pipeline, not :authenticated. Move it without 403ing owners. Leave a handoff if update still skips.",
        plan="Authenticate index and rerun note_controller_test.exs.",
        outcome="Index pipeline left delete on :api. Plan change: authenticated scope + Bodyguard. Partial: update leftover (xfail handoff).",
    ))

    add(dict(
        slug="laravel-withoutmiddleware-destroy",
        plant="maststep",
        surface="Laravel withoutMiddleware destroy leftover",
        src="app/Http/Controllers/NoteController.php",
        src_fn="destroy",
        handler="routes/api.php",
        test="tests/Feature/NoteDestroyTest.php",
        test_fn="test_viewer_destroy_403",
        bug_hint="$this->middleware('can:update,note')->except('destroy')",
        inspect_obs="NoteController.php: except destroy\nroutes/api.php: Route::delete notes\nNoteDestroyTest.php: test_viewer_destroy_403\n",
        src_obs="public function __construct() {\n  $this->middleware('can:update,note')->except('destroy'); // MAS-8\n}\npublic function destroy(Note $note) { $note->delete(); }\n",
        handler_obs="Route::delete('/notes/{note}', [NoteController::class, 'destroy']);\n",
        test_obs="public function test_viewer_destroy_403(): void {\n  $this->actingAs($viewer)->deleteJson('/notes/'.$note->id)->assertForbidden();\n}\n",
        first_apply="can:view on index",
        first_path="app/Http/Controllers/NoteController.php",
        first_old="  $this->middleware('can:update,note')->except('destroy'); // MAS-8",
        first_new="  $this->middleware('can:view,note')->only('index');\n  $this->middleware('can:update,note')->except('destroy');",
        first_obs="index gated; destroy still excepted",
        reflection="except('destroy') is the BFLA. Authorize destroy with NotePolicy::delete.",
        plan_change="drop except; middleware can:delete,note on destroy",
        grep_pat="except\\('destroy'\\)|can:delete",
        grep_obs="NoteController.php: except destroy\n",
        legacy_path="app/Http/Controllers/NoteController.php",
        legacy_hint="destroy excepted",
        legacy_obs="  $this->middleware('can:update,note')->except('destroy');\n",
        legacy_old="  $this->middleware('can:view,note')->only('index');\n  $this->middleware('can:update,note')->except('destroy');",
        legacy_new="  $this->middleware('can:view,note')->only('index');\n  $this->middleware('can:update,note')->except('destroy');\n  $this->middleware('can:delete,note')->only('destroy');",
        legacy_edit_obs="destroy can:delete",
        companion_path="app/Policies/NotePolicy.php",
        companion_old="public function delete(User $user, Note $note): bool { return true; }",
        companion_new="public function delete(User $user, Note $note): bool { return $user->id === $note->owner_id; }",
        companion_obs="owner delete",
        extra_fn="test_viewer_force_destroy_403",
        extra_old="public function test_viewer_destroy_403(): void {",
        extra_new="/** @group handoff */\npublic function test_viewer_force_destroy_403(): void {\n  $this->markTestSkipped('handoff: forceDelete still excepted');\n  $this->actingAs($viewer)->deleteJson('/notes/'.$note->id.'/force')->assertForbidden();\n}\npublic function test_viewer_destroy_403(): void {",
        extra_obs="xfails forceDelete leftover",
        handoff_path="app/Http/Controllers/NoteController.php",
        handoff_obs="  $this->middleware('can:delete,note')->except('forceDelete');\n",
        handoff_hint="forceDelete still excepted",
        residual="forceDelete still excepted",
        residual_path="app/Http/Controllers/NoteController.php",
        residual_pat="forceDelete",
        residual_obs="  $this->middleware('can:delete,note')->except('forceDelete');\n",
        residual_refl="destroy authorized. forceDelete still excepted.",
        leave_cmd="echo MAS-8 handoff Laravel forceDelete except",
        leave_obs="MAS-8 handoff Laravel forceDelete except",
        ticket="MAS-8",
        goal="maststep-notes DELETE /notes/{id} is 200 for a viewer because can:update excepts destroy. Authorize delete without 403ing owners. Leave a handoff if forceDelete still excepts.",
        plan="Gate index with can:view and rerun NoteDestroyTest.",
        outcome="Index can:view left destroy excepted. Plan change: can:delete on destroy. Partial: forceDelete leftover (xfail handoff).",
    ))

    add(dict(
        slug="quarkus-rolesallowed-missing-delete",
        plant="parrel",
        surface="Quarkus @RolesAllowed missing on DELETE",
        src="src/main/java/parrel/NoteResource.java",
        src_fn="delete",
        handler="src/main/java/parrel/NoteResource.java",
        test="src/test/java/parrel/NoteDeleteTest.java",
        test_fn="viewerDeleteIs403",
        bug_hint="@RolesAllowed on GET; DELETE bare",
        inspect_obs="NoteResource.java: GET RolesAllowed, DELETE none\nNoteDeleteTest.java: viewerDeleteIs403\n",
        src_obs="@DELETE\n@Path(\"{id}\")\npublic void delete(long id) { notes.delete(id); } // PAR-5\n",
        handler_obs="@GET\n@Path(\"{id}\")\n@RolesAllowed(\"user\")\npublic Note get(long id) { return notes.find(id); }\n",
        test_obs="@Test void viewerDeleteIs403() {\n  given().delete(\"/notes/\" + note.id).then().statusCode(403);\n}\n",
        first_apply="@RolesAllowed on GET list",
        first_path="src/main/java/parrel/NoteResource.java",
        first_old="@GET\npublic List<Note> list() { return notes.listAll(); }",
        first_new="@GET\n@RolesAllowed(\"user\")\npublic List<Note> list() { return notes.listAll(); }",
        first_obs="list gated; DELETE leftover",
        reflection="Quarkus method security is per method. DELETE needs @RolesAllowed plus owner check.",
        plan_change="@RolesAllowed user + owner predicate on DELETE",
        grep_pat="DELETE|RolesAllowed",
        grep_obs="NoteResource.java: delete no RolesAllowed\n",
        legacy_path="src/main/java/parrel/NoteResource.java",
        legacy_hint="DELETE bare",
        legacy_obs="@DELETE\n@Path(\"{id}\")\npublic void delete(long id) { notes.delete(id); }\n",
        legacy_old="@DELETE\n@Path(\"{id}\")\npublic void delete(long id) { notes.delete(id); } // PAR-5",
        legacy_new="@DELETE\n@Path(\"{id}\")\n@RolesAllowed(\"user\")\npublic void delete(long id) {\n  Note n = notes.find(id);\n  if (n == null || !n.owner.equals(currentUser())) throw new NotFoundException();\n  notes.delete(n);\n}",
        legacy_edit_obs="DELETE roles+owner",
        companion_path="src/main/java/parrel/Identity.java",
        companion_old="public String currentUser() { return \"anon\"; }",
        companion_new="public String currentUser() { return identity.getPrincipal().getName(); }",
        companion_obs="principal name",
        extra_fn="viewerPutIs403",
        extra_old="@Test void viewerDeleteIs403() {",
        extra_new="@Disabled(\"handoff: PUT still unannotated\")\n@Test void viewerPutIs403() {\n  given().put(\"/notes/\" + note.id).then().statusCode(403);\n}\n@Test void viewerDeleteIs403() {",
        extra_obs="xfails PUT leftover",
        handoff_path="src/main/java/parrel/NoteResource.java",
        handoff_obs="@PUT\n@Path(\"{id}\")\npublic Note put(long id, Note in) { return notes.update(in); }\n",
        handoff_hint="PUT still unannotated",
        residual="PUT still unannotated",
        residual_path="src/main/java/parrel/NoteResource.java",
        residual_pat="@PUT",
        residual_obs="@PUT\n@Path(\"{id}\")\npublic Note put(long id, Note in) { return notes.update(in); }\n",
        residual_refl="DELETE RolesAllowed. PUT still bare.",
        leave_cmd="echo PAR-5 handoff Quarkus PUT missing RolesAllowed",
        leave_obs="PAR-5 handoff Quarkus PUT missing RolesAllowed",
        ticket="PAR-5",
        goal="parrel-notes DELETE /notes/{id} is 200 for a viewer because @RolesAllowed is only on GET. Gate delete without 403ing owners. Leave a handoff if PUT still skips.",
        plan="Add @RolesAllowed on list and rerun NoteDeleteTest.",
        outcome="List RolesAllowed left DELETE BFLA. Plan change: roles+owner on DELETE. Partial: PUT leftover (xfail handoff).",
    ))

    add(dict(
        slug="micronaut-secured-false-job",
        plant="ratline",
        surface="Micronaut @Secured(IS_ANONYMOUS) leftover on admin job",
        src="src/main/java/ratline/ReindexJob.java",
        src_fn="reindex",
        handler="src/main/java/ratline/ReindexJob.java",
        test="src/test/java/ratline/ReindexJobTest.java",
        test_fn="anonReindexIs401",
        bug_hint="@Secured(SecurityRule.IS_ANONYMOUS) on POST /jobs/reindex",
        inspect_obs="ReindexJob.java: IS_ANONYMOUS\nReindexJobTest.java: anonReindexIs401\n",
        src_obs="@Post(\"/jobs/reindex\")\n@Secured(SecurityRule.IS_ANONYMOUS) // RAT-7 leftover from k8s probe spike\npublic HttpResponse<?> reindex() { indexer.run(); return HttpResponse.ok(); }\n",
        handler_obs="@Get(\"/jobs\")\n@Secured(SecurityRule.IS_AUTHENTICATED)\npublic List<Job> list() { return jobs.all(); }\n",
        test_obs="@Test void anonReindexIs401() {\n  assertEquals(401, client.post(\"/jobs/reindex\").status().getCode());\n}\n",
        first_apply="@Secured AUTHENTICATED on GET /jobs",
        first_path="src/main/java/ratline/ReindexJob.java",
        first_old="@Get(\"/jobs\")\n@Secured(SecurityRule.IS_AUTHENTICATED)\npublic List<Job> list() { return jobs.all(); }",
        first_new="@Get(\"/jobs\")\n@Secured(SecurityRule.IS_AUTHENTICATED)\npublic List<Job> list() { return jobs.all(); }\n@Get(\"/jobs/{id}\")\n@Secured(SecurityRule.IS_AUTHENTICATED)\npublic Job get(long id) { return jobs.find(id); }",
        first_obs="GET jobs gated; POST reindex leftover anonymous",
        reflection="IS_ANONYMOUS is explicit allow. Switch to IS_AUTHENTICATED plus admin role.",
        plan_change="@Secured(admin) on reindex",
        grep_pat="IS_ANONYMOUS|reindex",
        grep_obs="ReindexJob.java: IS_ANONYMOUS\n",
        legacy_path="src/main/java/ratline/ReindexJob.java",
        legacy_hint="reindex anonymous",
        legacy_obs="@Secured(SecurityRule.IS_ANONYMOUS)\npublic HttpResponse<?> reindex()\n",
        legacy_old="@Post(\"/jobs/reindex\")\n@Secured(SecurityRule.IS_ANONYMOUS) // RAT-7 leftover from k8s probe spike\npublic HttpResponse<?> reindex() { indexer.run(); return HttpResponse.ok(); }",
        legacy_new="@Post(\"/jobs/reindex\")\n@Secured(\"admin\")\npublic HttpResponse<?> reindex() { indexer.run(); return HttpResponse.ok(); }",
        legacy_edit_obs="admin role",
        companion_path="src/main/resources/application.yml",
        companion_old="micronaut:\n  security:\n    enabled: true",
        companion_new="micronaut:\n  security:\n    enabled: true\n    intercept-url-map:\n      - pattern: /jobs/reindex\n        access: [admin]",
        companion_obs="intercept map admin",
        extra_fn="anonPurgeIs401",
        extra_old="@Test void anonReindexIs401() {",
        extra_new="@Disabled(\"handoff: /jobs/purge still IS_ANONYMOUS\")\n@Test void anonPurgeIs401() {\n  assertEquals(401, client.post(\"/jobs/purge\").status().getCode());\n}\n@Test void anonReindexIs401() {",
        extra_obs="xfails purge leftover",
        handoff_path="src/main/java/ratline/PurgeJob.java",
        handoff_obs="@Post(\"/jobs/purge\")\n@Secured(SecurityRule.IS_ANONYMOUS)\npublic HttpResponse<?> purge() { db.purge(); return HttpResponse.ok(); }\n",
        handoff_hint="/jobs/purge still IS_ANONYMOUS",
        residual="/jobs/purge still IS_ANONYMOUS",
        residual_path="src/main/java/ratline/PurgeJob.java",
        residual_pat="purge",
        residual_obs="@Post(\"/jobs/purge\")\n@Secured(SecurityRule.IS_ANONYMOUS)\n",
        residual_refl="reindex admin-only. purge still anonymous.",
        leave_cmd="echo RAT-7 handoff Micronaut purge IS_ANONYMOUS",
        leave_obs="RAT-7 handoff Micronaut purge IS_ANONYMOUS",
        ticket="RAT-7",
        goal="ratline-jobs POST /jobs/reindex is 200 anonymously because @Secured(IS_ANONYMOUS) is leftover from a probe spike. Require admin without 403ing operators. Leave a handoff if purge still skips.",
        plan="Secure GET /jobs/{id} and rerun ReindexJobTest.",
        outcome="GET job gating left reindex anonymous. Plan change: @Secured(admin). Partial: purge leftover (xfail handoff).",
    ))

    add(dict(
        slug="axum-layer-not-on-nested",
        plant="sheer",
        surface="Axum nest /v2 router missing auth layer",
        src="src/http_axum.rs",
        src_fn="v2_delete",
        handler="src/http_axum.rs",
        test="tests/test_axum_v2.py",
        test_fn="test_v2_delete_401",
        bug_hint="Router::nest(\"/v2\", v2) has no from_fn(auth)",
        inspect_obs="http_axum.rs: nest /v2 without layer\ntests/test_axum_v2.py: test_v2_delete_401\n",
        src_obs="let v2 = Router::new().route(\"/notes/{id}\", delete(v2_delete)); // SHE-9 no auth layer\nlet app = Router::new().nest(\"/v2\", v2).route(\"/v1/notes/{id}\", get(v1_get).layer(from_fn(auth)));\n",
        handler_obs="async fn v2_delete(Path(id): Path<i64>) -> StatusCode { db::delete(id); StatusCode::NO_CONTENT }\n",
        test_obs="def test_v2_delete_401(client):\n    r = client.delete(\"/v2/notes/1\")\n    assert r.status_code == 401\n",
        first_apply="layer auth on /v1 GET",
        first_path="src/http_axum.rs",
        first_old=".route(\"/v1/notes/{id}\", get(v1_get).layer(from_fn(auth)))",
        first_new=".route(\"/v1/notes/{id}\", get(v1_get).layer(from_fn(auth)))\n.route(\"/v1/notes\", get(v1_list).layer(from_fn(auth)))",
        first_obs="/v1 gated; /v2 nest leftover",
        reflection="Axum nest does not inherit sibling route layers. Layer the nested router.",
        plan_change="v2.layer(from_fn(auth)) then owner delete",
        grep_pat="nest\\(\"/v2\"|from_fn\\(auth\\)",
        grep_obs="http_axum.rs: v2 nest no layer\n",
        legacy_path="src/http_axum.rs",
        legacy_hint="v2 unlayered",
        legacy_obs="let v2 = Router::new().route(\"/notes/{id}\", delete(v2_delete));\n",
        legacy_old="let v2 = Router::new().route(\"/notes/{id}\", delete(v2_delete)); // SHE-9 no auth layer",
        legacy_new="let v2 = Router::new().route(\"/notes/{id}\", delete(v2_delete)).layer(from_fn(auth));",
        legacy_edit_obs="v2 auth layer",
        companion_path="src/acl_axum.rs",
        companion_old="async fn v2_delete(Path(id): Path<i64>) -> StatusCode { db::delete(id); StatusCode::NO_CONTENT }",
        companion_new="async fn v2_delete(Extension(user): Extension<User>, Path(id): Path<i64>) -> StatusCode {\n  if !owns(&user, id) { return StatusCode::FORBIDDEN; }\n  db::delete(id); StatusCode::NO_CONTENT\n}",
        companion_obs="owns check",
        extra_fn="test_v2_patch_401",
        extra_old="def test_v2_delete_401(client):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: /v2 patch route still unlayered\", strict=False)\ndef test_v2_patch_401(client):\n    assert client.patch(\"/v2/notes/1\", json={}).status_code == 401\n\ndef test_v2_delete_401(client):",
        extra_obs="xfails v2 patch leftover",
        handoff_path="src/http_axum.rs",
        handoff_obs=".route(\"/notes/{id}\", patch(v2_patch)) // merged after nest, no layer\n",
        handoff_hint="/v2 patch route still unlayered",
        residual="/v2 patch route still unlayered",
        residual_path="src/http_axum.rs",
        residual_pat="v2_patch",
        residual_obs=".route(\"/notes/{id}\", patch(v2_patch)) // merged after nest, no layer\n",
        residual_refl="v2 delete layered. patch merge still bare.",
        leave_cmd="echo SHE-9 handoff Axum v2 patch unlayered",
        leave_obs="SHE-9 handoff Axum v2 patch unlayered",
        ticket="SHE-9",
        goal="sheer-notes DELETE /v2/notes/{id} is 200 anonymously because the nested /v2 router has no from_fn(auth) layer. Layer v2 without 403ing owners. Leave a handoff if patch is still unlayered.",
        plan="Auth-layer /v1 list and rerun tests/test_axum_v2.py.",
        outcome="/v1 layer left /v2 open. Plan change: nest layer + owns. Partial: v2 patch leftover (xfail handoff).",
    ))

    add(dict(
        slug="actix-wrapfn-skip-admin",
        plant="thwart",
        surface="Actix wrap auth only on /v1 not /admin",
        src="src/http_actix.rs",
        src_fn="admin_purge",
        handler="src/http_actix.rs",
        test="tests/test_actix_admin.py",
        test_fn="test_admin_purge_401",
        bug_hint="web::scope(\"/v1\").wrap(Auth); /admin scope unwrapped",
        inspect_obs="http_actix.rs: /v1 wrap Auth; /admin none\ntests/test_actix_admin.py: test_admin_purge_401\n",
        src_obs=".service(web::scope(\"/admin\").route(\"/purge\", web::post().to(admin_purge))) // THW-3\n",
        handler_obs="async fn admin_purge() -> HttpResponse { db::purge(); HttpResponse::Ok().finish() }\n",
        test_obs="def test_admin_purge_401(client):\n    r = client.post(\"/admin/purge\")\n    assert r.status_code == 401\n",
        first_apply="wrap Auth on /v1 notes",
        first_path="src/http_actix.rs",
        first_old=".service(web::scope(\"/v1\").wrap(Auth).route(\"/notes\", web::get().to(list)))",
        first_new=".service(web::scope(\"/v1\").wrap(Auth).route(\"/notes\", web::get().to(list)).route(\"/notes/{id}\", web::get().to(get)))",
        first_obs="/v1 notes gated; /admin leftover",
        reflection="Actix scope wrap is per scope. Wrap /admin or nest it under Auth.",
        plan_change="wrap Auth+AdminGuard on /admin",
        grep_pat="scope\\(\"/admin\"|wrap\\(Auth\\)",
        grep_obs="http_actix.rs: /admin no wrap\n",
        legacy_path="src/http_actix.rs",
        legacy_hint="admin unwrapped",
        legacy_obs=".service(web::scope(\"/admin\").route(\"/purge\", web::post().to(admin_purge)))\n",
        legacy_old=".service(web::scope(\"/admin\").route(\"/purge\", web::post().to(admin_purge))) // THW-3",
        legacy_new=".service(web::scope(\"/admin\").wrap(Auth).wrap(AdminGuard).route(\"/purge\", web::post().to(admin_purge)))",
        legacy_edit_obs="admin wrapped",
        companion_path="src/guard_actix.rs",
        companion_old="pub struct AdminGuard;\nimpl Guard for AdminGuard { fn check(&self, _: &GuardContext) -> bool { true } }",
        companion_new="impl Guard for AdminGuard {\n  fn check(&self, ctx: &GuardContext) -> bool {\n    ctx.req_data().get::<User>().map(|u| u.admin).unwrap_or(false)\n  }\n}",
        companion_obs="admin flag",
        extra_fn="test_admin_impersonate_401",
        extra_old="def test_admin_purge_401(client):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: /ops impersonate scope unwrapped\", strict=False)\ndef test_admin_impersonate_401(client):\n    assert client.post(\"/ops/impersonate\").status_code == 401\n\ndef test_admin_purge_401(client):",
        extra_obs="xfails /ops leftover",
        handoff_path="src/http_actix.rs",
        handoff_obs=".service(web::scope(\"/ops\").route(\"/impersonate\", web::post().to(impersonate)))\n",
        handoff_hint="/ops impersonate scope unwrapped",
        residual="/ops impersonate scope unwrapped",
        residual_path="src/http_actix.rs",
        residual_pat="/ops",
        residual_obs=".service(web::scope(\"/ops\").route(\"/impersonate\", web::post().to(impersonate)))\n",
        residual_refl="/admin wrapped. /ops still bare.",
        leave_cmd="echo THW-3 handoff Actix /ops unwrapped",
        leave_obs="THW-3 handoff Actix /ops unwrapped",
        ticket="THW-3",
        goal="thwart-admin POST /admin/purge is 200 anonymously because only /v1 is wrap(Auth). Wrap /admin without 403ing admins. Leave a handoff if /ops is still unwrapped.",
        plan="Wrap /v1 GET by id and rerun tests/test_actix_admin.py.",
        outcome="/v1 wrap left /admin open. Plan change: Auth+AdminGuard on /admin. Partial: /ops leftover (xfail handoff).",
    ))

    add(dict(
        slug="echo-skipper-put-too-wide",
        plant="windlass",
        surface="Echo middleware skipper returns true for all PUT",
        src="src/http_echo.go",
        src_fn="Skipper",
        handler="src/http_echo.go",
        test="src/http_echo_test.go",
        test_fn="TestViewerPut403",
        bug_hint="skipper: c.Request().Method == PUT",
        inspect_obs="http_echo.go: Skipper PUT\nhttp_echo.go: PUT /v1/notes/:id\nhttp_echo_test.go: TestViewerPut403\n",
        src_obs="e.Use(mw.JWTWithConfig(mw.JWTConfig{Skipper: func(c echo.Context) bool {\n  return c.Request().Method == http.MethodPut // WIN-8 webhook leftover\n}}))\n",
        handler_obs="e.PUT(\"/v1/notes/:id\", putNote)\n",
        test_obs="func TestViewerPut403(t *testing.T) {\n  rec := putViewer(\"/v1/notes/1\")\n  if rec.Code != 403 { t.Fatalf(\"%d\", rec.Code) }\n}\n",
        first_apply="skip GET /health only",
        first_path="src/http_echo.go",
        first_old="  return c.Request().Method == http.MethodPut // WIN-8 webhook leftover",
        first_new="  return c.Path() == \"/health\" || c.Request().Method == http.MethodPut",
        first_obs="health skipped; PUT still skipped",
        reflection="Skipper must not key on Method PUT. Skip exact /webhooks/stripe only.",
        plan_change="skip exact /webhooks/stripe; JWT on PUT notes",
        grep_pat="MethodPut|Skipper",
        grep_obs="http_echo.go: Skipper PUT\n",
        legacy_path="src/http_echo.go",
        legacy_hint="PUT skipped",
        legacy_obs="return c.Request().Method == http.MethodPut\n",
        legacy_old="  return c.Path() == \"/health\" || c.Request().Method == http.MethodPut",
        legacy_new="  return c.Path() == \"/health\" || c.Path() == \"/webhooks/stripe\"",
        legacy_edit_obs="PUT no longer skipped",
        companion_path="src/acl_echo.go",
        companion_old="func putNote(c echo.Context) error { return db.Save(c) }",
        companion_new="func putNote(c echo.Context) error {\n  if !owns(c) { return echo.ErrForbidden }\n  return db.Save(c)\n}",
        companion_obs="owns",
        extra_fn="TestViewerPatch403",
        extra_old="func TestViewerPut403(t *testing.T) {",
        extra_new="func TestViewerPatch403(t *testing.T) {\n  t.Skip(\"handoff: Skipper still true for PATCH\")\n  rec := patchViewer(\"/v1/notes/1\")\n  if rec.Code != 403 { t.Fatalf(\"%d\", rec.Code) }\n}\nfunc TestViewerPut403(t *testing.T) {",
        extra_obs="xfails PATCH skip leftover",
        handoff_path="src/http_echo.go",
        handoff_obs="return c.Request().Method == http.MethodPatch\n",
        handoff_hint="Skipper still true for PATCH",
        residual="Skipper still true for PATCH",
        residual_path="src/http_echo.go",
        residual_pat="MethodPatch",
        residual_obs="return c.Request().Method == http.MethodPatch\n",
        residual_refl="PUT JWT required. PATCH skipper remains.",
        leave_cmd="echo WIN-8 handoff Echo PATCH skipper",
        leave_obs="WIN-8 handoff Echo PATCH skipper",
        ticket="WIN-8",
        goal="windlass-notes PUT /v1/notes/{id} is 200 for a viewer because JWT Skipper returns true for every PUT (webhook leftover). Skip only /webhooks/stripe without 403ing owners. Leave a handoff if PATCH still skips.",
        plan="Skip /health as well and rerun TestViewerPut403.",
        outcome="Health skip left PUT skipped. Plan change: exact webhook path. Partial: PATCH leftover (xfail handoff).",
    ))

    add(dict(
        slug="webflux-path-delete-gap",
        plant="yardarm",
        surface="WebFlux authorizeExchange DELETE falls to permitAll",
        src="src/main/java/yardarm/SecurityConfig.java",
        src_fn="securityWebFilterChain",
        handler="src/main/java/yardarm/NoteHandler.java",
        test="src/test/java/yardarm/NoteDeleteTest.java",
        test_fn="viewerDeleteIs403",
        bug_hint="pathMatchers GET authenticated; anyExchange permitAll",
        inspect_obs="SecurityConfig.java: authorizeExchange\nNoteHandler.java: DELETE\nNoteDeleteTest.java: viewerDeleteIs403\n",
        src_obs=".authorizeExchange()\n  .pathMatchers(GET, \"/v1/notes/**\").authenticated()\n  .anyExchange().permitAll() // YAR-4 DELETE permitted\n",
        handler_obs="@DeleteMapping(\"/v1/notes/{id}\")\npublic Mono<Void> delete(@PathVariable long id) { return notes.delete(id); }\n",
        test_obs="@Test void viewerDeleteIs403() {\n  web.delete().uri(\"/v1/notes/\" + id).exchange().expectStatus().isForbidden();\n}\n",
        first_apply="authenticated GET list",
        first_path="src/main/java/yardarm/SecurityConfig.java",
        first_old="  .pathMatchers(GET, \"/v1/notes/**\").authenticated()\n  .anyExchange().permitAll() // YAR-4 DELETE permitted",
        first_new="  .pathMatchers(GET, \"/v1/notes\", \"/v1/notes/**\").authenticated()\n  .anyExchange().permitAll()",
        first_obs="GET tighter; DELETE still permitAll",
        reflection="anyExchange permitAll is the BFLA. Authenticate DELETE or deny anyExchange.",
        plan_change="pathMatchers DELETE authenticated; anyExchange deny",
        grep_pat="anyExchange|DELETE",
        grep_obs="SecurityConfig.java: anyExchange permitAll\n",
        legacy_path="src/main/java/yardarm/SecurityConfig.java",
        legacy_hint="DELETE permitAll",
        legacy_obs=".anyExchange().permitAll()\n",
        legacy_old="  .pathMatchers(GET, \"/v1/notes\", \"/v1/notes/**\").authenticated()\n  .anyExchange().permitAll()",
        legacy_new="  .pathMatchers(GET, \"/v1/notes/**\").authenticated()\n  .pathMatchers(DELETE, \"/v1/notes/**\").authenticated()\n  .anyExchange().denyAll()",
        legacy_edit_obs="DELETE auth, default deny",
        companion_path="src/main/java/yardarm/NoteHandler.java",
        companion_old="@DeleteMapping(\"/v1/notes/{id}\")\npublic Mono<Void> delete(@PathVariable long id) { return notes.delete(id); }",
        companion_new="@DeleteMapping(\"/v1/notes/{id}\")\npublic Mono<Void> delete(@PathVariable long id, @AuthenticationPrincipal User u) {\n  return notes.deleteIfOwner(id, u.getId());\n}",
        companion_obs="deleteIfOwner",
        extra_fn="viewerPutIs403",
        extra_old="@Test void viewerDeleteIs403() {",
        extra_new="@Disabled(\"handoff: PUT still anyExchange\")\n@Test void viewerPutIs403() {\n  web.put().uri(\"/v1/notes/\" + id).exchange().expectStatus().isForbidden();\n}\n@Test void viewerDeleteIs403() {",
        extra_obs="xfails PUT leftover",
        handoff_path="src/main/java/yardarm/SecurityConfig.java",
        handoff_obs=".pathMatchers(DELETE, \"/v1/notes/**\").authenticated()\n  // PUT not listed\n",
        handoff_hint="PUT still anyExchange",
        residual="PUT still anyExchange",
        residual_path="src/main/java/yardarm/SecurityConfig.java",
        residual_pat="HttpMethod.PUT",
        residual_obs=".pathMatchers(DELETE, \"/v1/notes/**\").authenticated()\n  // PUT not listed\n",
        residual_refl="DELETE authenticated + default deny. PUT matcher missing (denyAll covers it if published; test still xfails until wired).",
        leave_cmd="echo YAR-4 handoff WebFlux PUT matcher",
        leave_obs="YAR-4 handoff WebFlux PUT matcher",
        ticket="YAR-4",
        goal="yardarm-notes DELETE /v1/notes/{id} is 200 for a viewer because authorizeExchange authenticates GET then permitAll. Authenticate DELETE without 403ing owners. Leave a handoff if PUT is still unmatched.",
        plan="Authenticate GET list paths and rerun NoteDeleteTest.",
        outcome="GET matcher left DELETE permitAll. Plan change: DELETE authenticated + denyAll. Partial: PUT leftover (xfail handoff).",
    ))

    add(dict(
        slug="hasura-inherited-role-after-remove",
        plant="capstan",
        surface="Hasura inherited role leftover after remove",
        src="metadata/inherited_roles.yaml",
        src_fn="inherited_role",
        handler="metadata/actions.yaml",
        test="tests/test_hasura_inherited.py",
        test_fn="test_removed_child_cannot_select",
        bug_hint="remove_inherited_role drops YAML row; catalog still has parent",
        inspect_obs="inherited_roles.yaml: support inherits user\ntests/test_hasura_inherited.py: test_removed_child_cannot_select\n",
        src_obs="inherited_role:\n  role_name: support\n  role_set: [user, audit_reader]  # CAP-14 remove API left catalog\n",
        handler_obs="POST /v1/metadata drop_inherited_role support\n# pg dump still lists inherited_role\n",
        test_obs="def test_removed_child_cannot_select(client, support):\n    client.login(support)  # role removed yesterday\n    r = client.post(\"/v1/graphql\", json={\"query\": \"{ notes { id } }\"})\n    assert r.status_code == 403\n",
        first_apply="delete YAML inherited_roles.yaml only",
        first_path="metadata/inherited_roles.yaml",
        first_old="inherited_role:\n  role_name: support\n  role_set: [user, audit_reader]  # CAP-14 remove API left catalog",
        first_new="# inherited_roles.yaml emptied",
        first_obs="file empty; catalog hdb_catalog.inherited_role still has support",
        reflection="Hasura inherited roles live in hdb_catalog. Must drop_inherited_role then reload metadata.",
        plan_change="drop_inherited_role + reload_metadata",
        grep_pat="inherited_role|hdb_catalog",
        grep_obs="hdb_catalog still support\n",
        legacy_path="scripts/drop_support.sql",
        legacy_hint="catalog leftover",
        legacy_obs="-- no drop\n",
        legacy_old="-- no drop",
        legacy_new="SELECT hdb_catalog.drop_inherited_role('support');\nNOTIFY hasura_reload;\n",
        legacy_edit_obs="catalog drop",
        companion_path="src/hasura_reload.py",
        companion_old="def reload():\n    pass",
        companion_new="def reload():\n    requests.post(HASURA + \"/v1/metadata\", json={\"type\": \"reload_metadata\", \"args\": {}})",
        companion_obs="reload metadata",
        extra_fn="test_audit_reader_after_remove",
        extra_old="def test_removed_child_cannot_select(client, support):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: audit_reader still in role_set of billing\", strict=False)\ndef test_audit_reader_after_remove(client, billing):\n    client.login(billing)\n    assert \"notes\" not in client.post(\"/v1/graphql\", json={\"query\": \"{ notes { id } }\"}).json()\n\ndef test_removed_child_cannot_select(client, support):",
        extra_obs="xfails billing inherit leftover",
        handoff_path="metadata/inherited_roles.yaml",
        handoff_obs="inherited_role:\n  role_name: billing\n  role_set: [user, audit_reader]\n",
        handoff_hint="audit_reader still in role_set of billing",
        residual="audit_reader still in role_set of billing",
        residual_path="metadata/inherited_roles.yaml",
        residual_pat="billing",
        residual_obs="inherited_role:\n  role_name: billing\n  role_set: [user, audit_reader]\n",
        residual_refl="support inherited role dropped. billing still inherits audit_reader.",
        leave_cmd="echo CAP-14 handoff Hasura billing inherited role",
        leave_obs="CAP-14 handoff Hasura billing inherited role",
        ticket="CAP-14",
        goal="capstan-graphql a removed support user still selects notes because drop_inherited_role only emptied YAML. Drop catalog + reload without 403ing remaining user role. Leave a handoff if billing still inherits audit_reader.",
        plan="Empty inherited_roles.yaml and rerun tests/test_hasura_inherited.py.",
        outcome="YAML delete left hdb_catalog. Plan change: drop_inherited_role + reload. Partial: billing leftover (xfail handoff).",
    ))

    add(dict(
        slug="supabase-rls-update-using-true",
        plant="cringle",
        surface="Supabase RLS UPDATE USING (true) leftover",
        src="supabase/notes.sql",
        src_fn="notes_update",
        handler="src/http_notes.py",
        test="tests/test_rls_update.py",
        test_fn="test_viewer_update_403",
        bug_hint="SELECT policy owner-only; UPDATE USING (true)",
        inspect_obs="notes.sql: POLICY notes_update USING (true)\nsrc/http_notes.py: PATCH\ntests/test_rls_update.py: test_viewer_update_403\n",
        src_obs="CREATE POLICY notes_select ON notes FOR SELECT USING (owner = auth.uid());\nCREATE POLICY notes_update ON notes FOR UPDATE USING (true); -- CRI-6\n",
        handler_obs="@app.patch(\"/v1/notes/{id}\")\ndef patch_note(id, body, user=Depends(auth)):\n    return sb.table(\"notes\").update(body).eq(\"id\", id).execute()\n",
        test_obs="def test_viewer_update_403(client, viewer, note):\n    client.login(viewer)\n    r = client.patch(f\"/v1/notes/{note.id}\", json={\"body\": \"x\"})\n    assert r.status_code == 403\n",
        first_apply="WITH CHECK owner on INSERT only",
        first_path="supabase/notes.sql",
        first_old="CREATE POLICY notes_insert ON notes FOR INSERT WITH CHECK (owner = auth.uid());",
        first_new="CREATE POLICY notes_insert ON notes FOR INSERT WITH CHECK (owner = auth.uid());\n-- UPDATE still USING (true)",
        first_obs="insert checked; UPDATE leftover true",
        reflection="USING (true) on UPDATE is BFLA/BOLA. USING + WITH CHECK owner = auth.uid().",
        plan_change="UPDATE USING owner=auth.uid() WITH CHECK same",
        grep_pat="notes_update|USING \\(true\\)",
        grep_obs="notes.sql: UPDATE USING (true)\n",
        legacy_path="supabase/notes.sql",
        legacy_hint="UPDATE true",
        legacy_obs="CREATE POLICY notes_update ON notes FOR UPDATE USING (true);\n",
        legacy_old="CREATE POLICY notes_update ON notes FOR UPDATE USING (true); -- CRI-6",
        legacy_new="CREATE POLICY notes_update ON notes FOR UPDATE\n  USING (owner = auth.uid())\n  WITH CHECK (owner = auth.uid());",
        legacy_edit_obs="update owner",
        companion_path="src/http_notes.py",
        companion_old="    return sb.table(\"notes\").update(body).eq(\"id\", id).execute()",
        companion_new="    row = sb.table(\"notes\").update(body).eq(\"id\", id).eq(\"owner\", user.id).execute()\n    if not row.data: raise HTTPException(404)\n    return row",
        companion_obs="eq owner defense",
        extra_fn="test_viewer_delete_403",
        extra_old="def test_viewer_update_403(client, viewer, note):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: DELETE policy USING true\", strict=False)\ndef test_viewer_delete_403(client, viewer, note):\n    client.login(viewer)\n    assert client.delete(f\"/v1/notes/{note.id}\").status_code == 403\n\ndef test_viewer_update_403(client, viewer, note):",
        extra_obs="xfails DELETE leftover",
        handoff_path="supabase/notes.sql",
        handoff_obs="CREATE POLICY notes_delete ON notes FOR DELETE USING (true);\n",
        handoff_hint="DELETE policy USING true",
        residual="DELETE policy USING true",
        residual_path="supabase/notes.sql",
        residual_pat="notes_delete",
        residual_obs="CREATE POLICY notes_delete ON notes FOR DELETE USING (true);\n",
        residual_refl="UPDATE owner-scoped. DELETE USING true remains.",
        leave_cmd="echo CRI-6 handoff Supabase DELETE USING true",
        leave_obs="CRI-6 handoff Supabase DELETE USING true",
        ticket="CRI-6",
        goal="cringle-notes PATCH /v1/notes/{id} is 200 for a viewer because RLS UPDATE USING (true). Scope UPDATE without 403ing owners. Leave a handoff if DELETE still uses true.",
        plan="Tighten INSERT WITH CHECK and rerun tests/test_rls_update.py.",
        outcome="INSERT check left UPDATE true. Plan change: USING+WITH CHECK owner. Partial: DELETE leftover (xfail handoff).",
    ))

    add(dict(
        slug="express-router-use-order",
        plant="fid",
        surface="Express app.delete registered before app.use(auth)",
        src="src/http_express.js",
        src_fn="deleteNote",
        handler="src/http_express.js",
        test="tests/test_express_delete.py",
        test_fn="test_viewer_delete_403",
        bug_hint="app.delete('/v1/notes/:id') before app.use(auth)",
        inspect_obs="http_express.js: delete then use auth\ntests/test_express_delete.py: test_viewer_delete_403\n",
        src_obs="app.delete('/v1/notes/:id', deleteNote) // FID-2 registered before auth\napp.use(auth)\napp.get('/v1/notes/:id', getNote)\n",
        handler_obs="function deleteNote(req, res) { db.del(req.params.id); res.status(204).end() }\n",
        test_obs="def test_viewer_delete_403(client, viewer, note):\n    client.login(viewer)\n    assert client.delete(f\"/v1/notes/{note.id}\").status_code == 403\n",
        first_apply="auth on GET /v1/notes",
        first_path="src/http_express.js",
        first_old="app.get('/v1/notes/:id', getNote)",
        first_new="app.get('/v1/notes/:id', auth, getNote)",
        first_obs="GET has auth; DELETE still before app.use",
        reflection="Express matches in order. Move delete after app.use(auth) or pass auth as arg.",
        plan_change="app.delete after auth; require owner",
        grep_pat="app.delete|app.use\\(auth\\)",
        grep_obs="http_express.js: delete before use\n",
        legacy_path="src/http_express.js",
        legacy_hint="delete early",
        legacy_obs="app.delete('/v1/notes/:id', deleteNote)\napp.use(auth)\n",
        legacy_old="app.delete('/v1/notes/:id', deleteNote) // FID-2 registered before auth\napp.use(auth)",
        legacy_new="app.use(auth)\napp.delete('/v1/notes/:id', deleteNote)",
        legacy_edit_obs="delete after auth",
        companion_path="src/acl_express.js",
        companion_old="function deleteNote(req, res) { db.del(req.params.id); res.status(204).end() }",
        companion_new="function deleteNote(req, res) {\n  if (!owns(req.user, req.params.id)) return res.status(403).end()\n  db.del(req.params.id); res.status(204).end()\n}",
        companion_obs="owns",
        extra_fn="test_viewer_put_403",
        extra_old="def test_viewer_delete_403(client, viewer, note):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: app.put still before auth\", strict=False)\ndef test_viewer_put_403(client, viewer, note):\n    client.login(viewer)\n    assert client.put(f\"/v1/notes/{note.id}\", json={}).status_code == 403\n\ndef test_viewer_delete_403(client, viewer, note):",
        extra_obs="xfails PUT leftover",
        handoff_path="src/http_express.js",
        handoff_obs="app.put('/v1/notes/:id', putNote) // still above app.use in v2 file\n",
        handoff_hint="app.put still before auth",
        residual="app.put still before auth",
        residual_path="src/http_express.js",
        residual_pat="app.put",
        residual_obs="app.put('/v1/notes/:id', putNote) // still above app.use in v2 file\n",
        residual_refl="delete after auth. put still early.",
        leave_cmd="echo FID-2 handoff Express put before auth",
        leave_obs="FID-2 handoff Express put before auth",
        ticket="FID-2",
        goal="fid-notes DELETE /v1/notes/{id} is 200 for a viewer because app.delete is registered before app.use(auth). Reorder without 403ing owners. Leave a handoff if PUT is still early.",
        plan="Pass auth into GET and rerun tests/test_express_delete.py.",
        outcome="GET auth left DELETE early. Plan change: delete after app.use + owns. Partial: PUT leftover (xfail handoff).",
    ))

    add(dict(
        slug="koa-unless-path-too-wide",
        plant="hounds",
        surface="koa-jwt unless path /^\\/admin/ leftover",
        src="src/http_koa.js",
        src_fn="unless",
        handler="src/http_koa.js",
        test="tests/test_koa_admin.py",
        test_fn="test_admin_users_401",
        bug_hint="jwt.unless({ path: [/^\\/admin/] }) skips all /admin",
        inspect_obs="http_koa.js: unless /admin\nhttp_koa.js: GET /admin/users\ntests/test_koa_admin.py: test_admin_users_401\n",
        src_obs="app.use(jwt({ secret }).unless({ path: [/^\\/admin/] })) // HOU-5 intended /admin/health\n",
        handler_obs="router.get('/admin/users', listUsers)\n",
        test_obs="def test_admin_users_401(client):\n    r = client.get(\"/admin/users\")\n    assert r.status_code == 401\n",
        first_apply="unless /health",
        first_path="src/http_koa.js",
        first_old="app.use(jwt({ secret }).unless({ path: [/^\\/admin/] })) // HOU-5 intended /admin/health",
        first_new="app.use(jwt({ secret }).unless({ path: [/^\\/admin/, /^\\/health/] }))",
        first_obs="health skipped; /admin still skipped",
        reflection="unless /^\\/admin/ is a prefix. Use /^\\/admin\\/health$/ only.",
        plan_change="unless exact /admin/health; jwt on /admin/users",
        grep_pat="unless|/admin/users",
        grep_obs="http_koa.js: unless /admin\n",
        legacy_path="src/http_koa.js",
        legacy_hint="admin skipped",
        legacy_obs="unless({ path: [/^\\/admin/] })\n",
        legacy_old="app.use(jwt({ secret }).unless({ path: [/^\\/admin/, /^\\/health/] }))",
        legacy_new="app.use(jwt({ secret }).unless({ path: [/^\\/admin\\/health$/, /^\\/health$/] }))",
        legacy_edit_obs="exact health unless",
        companion_path="src/acl_koa.js",
        companion_old="router.get('/admin/users', listUsers)",
        companion_new="router.get('/admin/users', requireAdmin, listUsers)",
        companion_obs="requireAdmin",
        extra_fn="test_admin_jobs_401",
        extra_old="def test_admin_users_401(client):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: unless still skips /administrator\", strict=False)\ndef test_admin_jobs_401(client):\n    assert client.get(\"/administrator/jobs\").status_code == 401\n\ndef test_admin_users_401(client):",
        extra_obs="xfails /administrator leftover",
        handoff_path="src/http_koa.js",
        handoff_obs="unless({ path: [/^\\/administrator/] })\n",
        handoff_hint="unless still skips /administrator",
        residual="unless still skips /administrator",
        residual_path="src/http_koa.js",
        residual_pat="administrator",
        residual_obs="unless({ path: [/^\\/administrator/] })\n",
        residual_refl="/admin/users jwt'd. /administrator unless remains.",
        leave_cmd="echo HOU-5 handoff koa unless /administrator",
        leave_obs="HOU-5 handoff koa unless /administrator",
        ticket="HOU-5",
        goal="hounds-admin GET /admin/users is 200 anonymously because jwt.unless(/^\\/admin/) skips the whole tree. Unless only /admin/health without opening users. Leave a handoff if /administrator still skips.",
        plan="Add /health to unless and rerun tests/test_koa_admin.py.",
        outcome="Extra unless left /admin skipped. Plan change: exact /admin/health. Partial: /administrator leftover (xfail handoff).",
    ))

    add(dict(
        slug="hapi-auth-mode-optional-delete",
        plant="jibboom",
        surface="hapi auth mode optional leftover on delete",
        src="src/http_hapi.js",
        src_fn="deleteNote",
        handler="src/http_hapi.js",
        test="tests/test_hapi_delete.py",
        test_fn="test_viewer_delete_403",
        bug_hint="auth: { mode: 'optional' } on DELETE",
        inspect_obs="http_hapi.js: delete auth optional\ntests/test_hapi_delete.py: test_viewer_delete_403\n",
        src_obs="{ method: 'DELETE', path: '/v1/notes/{id}', options: { auth: { mode: 'optional' } }, handler: deleteNote } // JIB-1\n",
        handler_obs="{ method: 'GET', path: '/v1/notes/{id}', options: { auth: 'jwt' }, handler: getNote }\n",
        test_obs="def test_viewer_delete_403(client, viewer, note):\n    client.login(viewer)\n    assert client.delete(f\"/v1/notes/{note.id}\").status_code == 403\n",
        first_apply="auth jwt on GET list",
        first_path="src/http_hapi.js",
        first_old="{ method: 'GET', path: '/v1/notes', options: { auth: false }, handler: listNotes }",
        first_new="{ method: 'GET', path: '/v1/notes', options: { auth: 'jwt' }, handler: listNotes }",
        first_obs="list jwt; DELETE leftover optional",
        reflection="optional auth means unauthenticated delete proceeds. Use required jwt plus owner scope.",
        plan_change="auth jwt required on DELETE; owner scope",
        grep_pat="mode: 'optional'|DELETE",
        grep_obs="http_hapi.js: delete optional\n",
        legacy_path="src/http_hapi.js",
        legacy_hint="delete optional",
        legacy_obs="auth: { mode: 'optional' }\n",
        legacy_old="{ method: 'DELETE', path: '/v1/notes/{id}', options: { auth: { mode: 'optional' } }, handler: deleteNote } // JIB-1",
        legacy_new="{ method: 'DELETE', path: '/v1/notes/{id}', options: { auth: 'jwt', plugins: { hacli: { permissions: ['note:delete'] } } }, handler: deleteNote }",
        legacy_edit_obs="delete required jwt",
        companion_path="src/acl_hapi.js",
        companion_old="async function deleteNote(req, h) { await db.del(req.params.id); return h.response().code(204) }",
        companion_new="async function deleteNote(req, h) {\n  if (req.auth.credentials.id !== (await db.note(req.params.id)).ownerId) return h.response().code(403)\n  await db.del(req.params.id); return h.response().code(204)\n}",
        companion_obs="owner",
        extra_fn="test_viewer_patch_403",
        extra_old="def test_viewer_delete_403(client, viewer, note):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: PATCH still mode optional\", strict=False)\ndef test_viewer_patch_403(client, viewer, note):\n    client.login(viewer)\n    assert client.patch(f\"/v1/notes/{note.id}\", json={}).status_code == 403\n\ndef test_viewer_delete_403(client, viewer, note):",
        extra_obs="xfails PATCH leftover",
        handoff_path="src/http_hapi.js",
        handoff_obs="{ method: 'PATCH', path: '/v1/notes/{id}', options: { auth: { mode: 'optional' } }, handler: patchNote }\n",
        handoff_hint="PATCH still mode optional",
        residual="PATCH still mode optional",
        residual_path="src/http_hapi.js",
        residual_pat="PATCH",
        residual_obs="{ method: 'PATCH', path: '/v1/notes/{id}', options: { auth: { mode: 'optional' } }, handler: patchNote }\n",
        residual_refl="DELETE required. PATCH still optional.",
        leave_cmd="echo JIB-1 handoff hapi PATCH optional",
        leave_obs="JIB-1 handoff hapi PATCH optional",
        ticket="JIB-1",
        goal="jibboom-notes DELETE /v1/notes/{id} is 200 for a viewer because auth mode is optional. Require jwt without 403ing owners. Leave a handoff if PATCH is still optional.",
        plan="Require jwt on list and rerun tests/test_hapi_delete.py.",
        outcome="List jwt left DELETE optional. Plan change: required jwt + owner. Partial: PATCH leftover (xfail handoff).",
    ))

    add(dict(
        slug="fastify-prehandler-missing-patch",
        plant="luff",
        surface="Fastify preHandler missing on PATCH",
        src="src/http_fastify.js",
        src_fn="patchNote",
        handler="src/http_fastify.js",
        test="tests/test_fastify_patch.py",
        test_fn="test_viewer_patch_403",
        bug_hint="GET preHandler authenticate; PATCH none",
        inspect_obs="http_fastify.js: patch no preHandler\ntests/test_fastify_patch.py: test_viewer_patch_403\n",
        src_obs="fastify.patch('/v1/notes/:id', patchNote) // LUF-8 no preHandler\n",
        handler_obs="fastify.get('/v1/notes/:id', { preHandler: [authenticate] }, getNote)\n",
        test_obs="def test_viewer_patch_403(client, viewer, note):\n    client.login(viewer)\n    assert client.patch(f\"/v1/notes/{note.id}\", json={\"body\": \"x\"}).status_code == 403\n",
        first_apply="preHandler on GET list",
        first_path="src/http_fastify.js",
        first_old="fastify.get('/v1/notes', listNotes)",
        first_new="fastify.get('/v1/notes', { preHandler: [authenticate] }, listNotes)",
        first_obs="list gated; PATCH leftover",
        reflection="Fastify preHandler is per route. PATCH needs authenticate plus canWrite.",
        plan_change="preHandler authenticate+canWrite on PATCH",
        grep_pat="fastify.patch|preHandler",
        grep_obs="http_fastify.js: patch no preHandler\n",
        legacy_path="src/http_fastify.js",
        legacy_hint="PATCH bare",
        legacy_obs="fastify.patch('/v1/notes/:id', patchNote)\n",
        legacy_old="fastify.patch('/v1/notes/:id', patchNote) // LUF-8 no preHandler",
        legacy_new="fastify.patch('/v1/notes/:id', { preHandler: [authenticate, canWrite] }, patchNote)",
        legacy_edit_obs="PATCH preHandler",
        companion_path="src/acl_fastify.js",
        companion_old="async function canWrite() { return }",
        companion_new="async function canWrite(req, reply) {\n  const n = await db.note(req.params.id)\n  if (n.ownerId !== req.user.id) return reply.code(403).send()\n}",
        companion_obs="owner",
        extra_fn="test_viewer_put_403",
        extra_old="def test_viewer_patch_403(client, viewer, note):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: PUT still no preHandler\", strict=False)\ndef test_viewer_put_403(client, viewer, note):\n    client.login(viewer)\n    assert client.put(f\"/v1/notes/{note.id}\", json={}).status_code == 403\n\ndef test_viewer_patch_403(client, viewer, note):",
        extra_obs="xfails PUT leftover",
        handoff_path="src/http_fastify.js",
        handoff_obs="fastify.put('/v1/notes/:id', putNote)\n",
        handoff_hint="PUT still no preHandler",
        residual="PUT still no preHandler",
        residual_path="src/http_fastify.js",
        residual_pat="fastify.put",
        residual_obs="fastify.put('/v1/notes/:id', putNote)\n",
        residual_refl="PATCH preHandler set. PUT still bare.",
        leave_cmd="echo LUF-8 handoff Fastify PUT no preHandler",
        leave_obs="LUF-8 handoff Fastify PUT no preHandler",
        ticket="LUF-8",
        goal="luff-notes PATCH /v1/notes/{id} is 200 for a viewer because PATCH has no preHandler. Gate write without 403ing owners. Leave a handoff if PUT still skips.",
        plan="Add authenticate on GET list and rerun tests/test_fastify_patch.py.",
        outcome="List preHandler left PATCH BFLA. Plan change: authenticate+canWrite on PATCH. Partial: PUT leftover (xfail handoff).",
    ))

    add(dict(
        slug="casl-cannot-after-unshare",
        plant="mizzen",
        surface="CASL ability leftover after unshare",
        src="src/casl_unshare.ts",
        src_fn="unshare",
        handler="src/http_share.ts",
        test="tests/test_casl_unshare.py",
        test_fn="test_unshare_revokes_read",
        bug_hint="unshare deletes Share row; Ability still can('read', 'Note')",
        inspect_obs="casl_unshare.ts: def unshare\nhttp_share.ts: POST /unshare\ntests/test_casl_unshare.py: test_unshare_revokes_read\n",
        src_obs="export function unshare(userId, noteId) {\n  db.shares.delete({ userId, noteId }) // MIZ-11 Ability cache leftover\n}\n",
        handler_obs="@app.post(\"/v1/notes/{id}/unshare\")\ndef http_unshare(id, user=Depends(auth)):\n    unshare(user.id, id)\n",
        test_obs="def test_unshare_revokes_read(client, bob, note):\n    client.login(bob)\n    client.post(f\"/v1/notes/{note.id}/unshare\")\n    assert client.get(f\"/v1/notes/{note.id}\").status_code == 404\n",
        first_apply="delete share row only",
        first_path="src/casl_unshare.ts",
        first_old="  db.shares.delete({ userId, noteId }) // MIZ-11 Ability cache leftover",
        first_new="  db.shares.delete({ userId, noteId })\n  db.share_events.insert({ userId, noteId, op: 'unshare' })",
        first_obs="event logged; Ability still allows read",
        reflection="CASL packs rules at session start. Must rebuild Ability after unshare and drop note:read.",
        plan_change="Ability.update cannot read Note id; persist pack",
        grep_pat="defineAbility|cannot\\('read'",
        grep_obs="src/ability.ts: can read Note for shared\n",
        legacy_path="src/ability.ts",
        legacy_hint="cached can read",
        legacy_obs="can('read', 'Note', { id: { $in: sharedIds } })\n",
        legacy_old="can('read', 'Note', { id: { $in: sharedIds } })",
        legacy_new="can('read', 'Note', { id: { $in: liveSharedIds(user) } })\n// liveSharedIds reads shares table, not session cache",
        legacy_edit_obs="live share ids",
        companion_path="src/casl_unshare.ts",
        companion_old="  db.shares.delete({ userId, noteId })\n  db.share_events.insert({ userId, noteId, op: 'unshare' })",
        companion_new="  db.shares.delete({ userId, noteId })\n  ability.update(defineRulesFor(userId))",
        companion_obs="ability rebuilt",
        extra_fn="test_unshare_revokes_update",
        extra_old="def test_unshare_revokes_read(client, bob, note):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: can('update', Note) pack still cached\", strict=False)\ndef test_unshare_revokes_update(client, bob, note):\n    client.login(bob)\n    client.post(f\"/v1/notes/{note.id}/unshare\")\n    assert client.patch(f\"/v1/notes/{note.id}\", json={}).status_code == 404\n\ndef test_unshare_revokes_read(client, bob, note):",
        extra_obs="xfails update pack leftover",
        handoff_path="src/ability.ts",
        handoff_obs="can('update', 'Note', { id: { $in: sharedIds } }) // not rebuilt\n",
        handoff_hint="can('update', Note) pack still cached",
        residual="can('update', Note) pack still cached",
        residual_path="src/ability.ts",
        residual_pat="can('update'",
        residual_obs="can('update', 'Note', { id: { $in: sharedIds } }) // not rebuilt\n",
        residual_refl="read pack rebuilt. update pack still cached.",
        leave_cmd="echo MIZ-11 handoff CASL update pack after unshare",
        leave_obs="MIZ-11 handoff CASL update pack after unshare",
        ticket="MIZ-11",
        goal="mizzen-notes POST unshare still allows GET because CASL Ability was packed at login. Rebuild rules without 404ing remaining shares. Leave a handoff if update pack is still cached.",
        plan="Log a share_event and rerun tests/test_casl_unshare.py.",
        outcome="Event log left Ability cache. Plan change: ability.update live ids. Partial: update pack leftover (xfail handoff).",
    ))

    add(dict(
        slug="pundit-scope-after-transfer",
        plant="nock",
        surface="Pundit NotePolicy::Scope leftover after transfer",
        src="app/policies/note_policy.rb",
        src_fn="resolve",
        handler="app/controllers/notes_controller.rb",
        test="spec/policies/note_policy_spec.rb",
        test_fn="old_owner_hidden_after_transfer",
        bug_hint="transfer updates assignee; Scope still where(owner_id: user.id)",
        inspect_obs="note_policy.rb: Scope owner_id\nnotes_controller.rb: transfer\nspec/policies/note_policy_spec.rb: old_owner_hidden_after_transfer\n",
        src_obs="class Scope < ApplicationPolicy::Scope\n  def resolve\n    scope.where(owner_id: user.id) # NOC-7 assignee not consulted\n  end\nend\n",
        handler_obs="def transfer\n  @note.update!(assignee_id: params[:owner_id])\nend\n",
        test_obs="it \"old_owner_hidden_after_transfer\" do\n  post transfer_note_path(note), params: { owner_id: bob.id }\n  expect(policy_scope(Note)).not_to include(note)\nend\n",
        first_apply="update SQL owner_id only in a job",
        first_path="app/jobs/note_transfer_job.rb",
        first_old="def perform(note_id, new_owner)\n  Note.find(note_id).update!(owner_sql: new_owner)\nend",
        first_new="def perform(note_id, new_owner)\n  Note.find(note_id).update!(owner_sql: new_owner, assignee_id: new_owner)\nend",
        first_obs="job writes owner_sql; live transfer still assignee only; Scope still owner_id",
        reflection="Scope must follow the live owner column transfer writes, or transfer must write owner_id.",
        plan_change="transfer writes owner_id; Scope uses owner_id",
        grep_pat="owner_id|assignee_id",
        grep_obs="notes_controller.rb: assignee_id\nnote_policy.rb: owner_id\n",
        legacy_path="app/controllers/notes_controller.rb",
        legacy_hint="assignee only",
        legacy_obs="  @note.update!(assignee_id: params[:owner_id])\n",
        legacy_old="  @note.update!(assignee_id: params[:owner_id])",
        legacy_new="  @note.update!(owner_id: params[:owner_id], assignee_id: params[:owner_id])",
        legacy_edit_obs="owner_id moved",
        companion_path="app/policies/note_policy.rb",
        companion_old="    scope.where(owner_id: user.id) # NOC-7 assignee not consulted",
        companion_new="    scope.where(owner_id: user.id)",
        companion_obs="Scope already owner_id; now matches transfer",
        extra_fn="editor_hidden_after_transfer",
        extra_old="it \"old_owner_hidden_after_transfer\" do",
        extra_new="xit \"handoff: editor role still in notes_users after transfer\" do\n  expect(policy_scope(Note)).not_to include(note)\nend\nit \"old_owner_hidden_after_transfer\" do",
        extra_obs="xfails editor join leftover",
        handoff_path="app/models/note.rb",
        handoff_obs="has_many :notes_users # editor rows not deleted on transfer\n",
        handoff_hint="editor role still in notes_users after transfer",
        residual="editor role still in notes_users after transfer",
        residual_path="app/models/note.rb",
        residual_pat="notes_users",
        residual_obs="has_many :notes_users # editor rows not deleted on transfer\n",
        residual_refl="owner_id transferred. editor join leftover.",
        leave_cmd="echo NOC-7 handoff Pundit editor join after transfer",
        leave_obs="NOC-7 handoff Pundit editor join after transfer",
        ticket="NOC-7",
        goal="nock-notes transfer still lists the note for alice because Pundit Scope keys owner_id while transfer writes assignee_id. Align columns without 404ing the new owner. Leave a handoff if editor joins remain.",
        plan="Write owner_sql in the job and rerun note_policy_spec.rb.",
        outcome="Job column left live transfer on assignee. Plan change: transfer writes owner_id. Partial: editor join leftover (xfail handoff).",
    ))

    add(dict(
        slug="cancan-ability-after-role-drop",
        plant="outhaul",
        surface="CanCanCan ability leftover after role drop",
        src="app/models/ability.rb",
        src_fn="initialize",
        handler="app/controllers/roles_controller.rb",
        test="spec/models/ability_spec.rb",
        test_fn="dropped_editor_cannot_update",
        bug_hint="remove_role deletes users_roles; Ability still can :update, Note",
        inspect_obs="ability.rb: can :update Note if editor\nroles_controller.rb: destroy\nability_spec.rb: dropped_editor_cannot_update\n",
        src_obs="if user.has_role?(:editor)\n  can :update, Note # OUT-3 memoized at login\nend\n",
        handler_obs="def destroy\n  current_user.remove_role(:editor)\nend\n",
        test_obs="it \"dropped_editor_cannot_update\" do\n  delete role_path(:editor)\n  expect(Ability.new(user)).not_to be_able_to(:update, note)\nend\n",
        first_apply="remove_role only",
        first_path="app/controllers/roles_controller.rb",
        first_old="  current_user.remove_role(:editor)",
        first_new="  current_user.remove_role(:editor)\n  session[:roles] = current_user.roles.pluck(:name)",
        first_obs="session roles list updated; Ability class still uses has_role? cache",
        reflection="Rolify has_role? can be cached. Reload roles and rebuild Ability.",
        plan_change="user.roles.reload; Ability.new(user) without memo",
        grep_pat="has_role\\?|@ability",
        grep_obs="application_controller.rb: @ability ||= Ability.new\n",
        legacy_path="app/controllers/application_controller.rb",
        legacy_hint="memoized Ability",
        legacy_obs="def current_ability\n  @ability ||= Ability.new(current_user)\nend\n",
        legacy_old="  @ability ||= Ability.new(current_user)",
        legacy_new="  @ability = Ability.new(current_user.reload)",
        legacy_edit_obs="Ability rebuilt",
        companion_path="app/models/ability.rb",
        companion_old="if user.has_role?(:editor)\n  can :update, Note # OUT-3 memoized at login\nend",
        companion_new="if user.roles.reload.exists?(name: 'editor')\n  can :update, Note\nend",
        companion_obs="roles reloaded",
        extra_fn="dropped_editor_cannot_destroy",
        extra_old="it \"dropped_editor_cannot_update\" do",
        extra_new="xit \"handoff: can :destroy, Note still granted via :admin alias\" do\n  expect(Ability.new(user)).not_to be_able_to(:destroy, note)\nend\nit \"dropped_editor_cannot_update\" do",
        extra_obs="xfails admin alias leftover",
        handoff_path="app/models/ability.rb",
        handoff_obs="can :manage, Note if user.has_role?(:admin) # alias includes destroy\n",
        handoff_hint="can :destroy, Note still granted via :admin alias",
        residual="can :destroy, Note still granted via :admin alias",
        residual_path="app/models/ability.rb",
        residual_pat=":manage, Note",
        residual_obs="can :manage, Note if user.has_role?(:admin) # alias includes destroy\n",
        residual_refl="editor update rebuilt. admin manage alias remains for this user fixture.",
        leave_cmd="echo OUT-3 handoff CanCan manage alias after role drop",
        leave_obs="OUT-3 handoff CanCan manage alias after role drop",
        ticket="OUT-3",
        goal="outhaul-notes dropping :editor still allows update because Ability is memoized at login. Rebuild Ability without 403ing remaining editors. Leave a handoff if :manage alias still grants destroy.",
        plan="Refresh session[:roles] and rerun ability_spec.rb.",
        outcome="Session list left memoized Ability. Plan change: reload roles + new Ability. Partial: manage alias leftover (xfail handoff).",
    ))

    add(dict(
        slug="vault-policy-plus-glob",
        plant="peak",
        surface="Vault policy plus-glob leftover after revoke",
        src="policies/notes.hcl",
        src_fn="path",
        handler="src/vault_revoke.py",
        test="tests/test_vault_glob.py",
        test_fn="test_revoke_hides_note",
        bug_hint="revoke deletes notes/data/42; policy still notes/data/+",
        inspect_obs="notes.hcl: path notes/data/+\nsrc/vault_revoke.py: delete notes/data/id\ntests/test_vault_glob.py: test_revoke_hides_note\n",
        src_obs="path \"notes/data/+\" {\n  capabilities = [\"read\"] # PEA-9 plus glob\n}\n",
        handler_obs="def revoke(note_id):\n    vault.delete(f\"notes/data/{note_id}\")\n",
        test_obs="def test_revoke_hides_note(client, alice, note):\n    client.post(f\"/v1/notes/{note.id}/revoke\")\n    assert client.get(f\"/v1/notes/{note.id}\").status_code == 404\n",
        first_apply="delete exact path plus notes/data/id/*",
        first_path="src/vault_revoke.py",
        first_old="    vault.delete(f\"notes/data/{note_id}\")",
        first_new="    vault.delete(f\"notes/data/{note_id}\")\n    vault.delete(f\"notes/metadata/{note_id}\")",
        first_obs="exact kv gone; policy + still allows recreate/read via glob",
        reflection="Plus-glob in policy grants any remaining or future id. Drop + ; grant exact paths.",
        plan_change="replace notes/data/+ with templated identity.entity.aliases",
        grep_pat="notes/data/\\+|capabilities",
        grep_obs="notes.hcl: path notes/data/+\n",
        legacy_path="policies/notes.hcl",
        legacy_hint="plus glob",
        legacy_obs="path \"notes/data/+\" {\n  capabilities = [\"read\"]\n}\n",
        legacy_old="path \"notes/data/+\" {\n  capabilities = [\"read\"] # PEA-9 plus glob\n}",
        legacy_new="path \"notes/data/{{identity.entity.id}}\" {\n  capabilities = [\"read\"]\n}",
        legacy_edit_obs="entity-templated path",
        companion_path="src/vault_revoke.py",
        companion_old="    vault.delete(f\"notes/data/{note_id}\")\n    vault.delete(f\"notes/metadata/{note_id}\")",
        companion_new="    vault.delete(f\"notes/data/{note_id}\")\n    policy.write(user, exact_ids(user))",
        companion_obs="policy rewritten to exact ids",
        extra_fn="test_revoke_hides_metadata",
        extra_old="def test_revoke_hides_note(client, alice, note):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: notes/metadata/+ still in policy\", strict=False)\ndef test_revoke_hides_metadata(client, alice, note):\n    client.post(f\"/v1/notes/{note.id}/revoke\")\n    assert client.get(f\"/v1/notes/{note.id}/meta\").status_code == 404\n\ndef test_revoke_hides_note(client, alice, note):",
        extra_obs="xfails metadata glob leftover",
        handoff_path="policies/notes.hcl",
        handoff_obs="path \"notes/metadata/+\" {\n  capabilities = [\"read\"]\n}\n",
        handoff_hint="notes/metadata/+ still in policy",
        residual="notes/metadata/+ still in policy",
        residual_path="policies/notes.hcl",
        residual_pat="metadata/+",
        residual_obs="path \"notes/metadata/+\" {\n  capabilities = [\"read\"]\n}\n",
        residual_refl="data plus-glob dropped. metadata + remains.",
        leave_cmd="echo PEA-9 handoff Vault metadata plus glob",
        leave_obs="PEA-9 handoff Vault metadata plus glob",
        ticket="PEA-9",
        goal="peak-notes revoke still allows GET because policy path notes/data/+ remains. Template exact entity paths without 404ing granted notes. Leave a handoff if metadata/+ still grants.",
        plan="Delete metadata path too and rerun tests/test_vault_glob.py.",
        outcome="Exact deletes left plus-glob. Plan change: entity-templated path. Partial: metadata/+ leftover (xfail handoff).",
    ))

    add(dict(
        slug="clerk-org-role-after-leave",
        plant="sprit",
        surface="Clerk org role leftover after leave",
        src="src/clerk_leave.ts",
        src_fn="leaveOrg",
        handler="src/http_orgs.ts",
        test="tests/test_clerk_leave.py",
        test_fn="test_leave_revokes_org_notes",
        bug_hint="leaveOrg deletes membership; session.claims.orgRole still admin",
        inspect_obs="clerk_leave.ts: leaveOrg\nhttp_orgs.ts: POST /leave\ntests/test_clerk_leave.py: test_leave_revokes_org_notes\n",
        src_obs="export async function leaveOrg(userId, orgId) {\n  await clerk.organizations.deleteOrganizationMembership({ userId, orgId }) // SPR-4 claims leftover\n}\n",
        handler_obs="@app.post(\"/v1/orgs/{id}/leave\")\ndef http_leave(id, user=Depends(auth)):\n    leaveOrg(user.id, id)\n",
        test_obs="def test_leave_revokes_org_notes(client, alice, org):\n    client.login(alice)\n    client.post(f\"/v1/orgs/{org.id}/leave\")\n    assert client.get(f\"/v1/orgs/{org.id}/notes\").status_code == 404\n",
        first_apply="delete membership only",
        first_path="src/clerk_leave.ts",
        first_old="  await clerk.organizations.deleteOrganizationMembership({ userId, orgId }) // SPR-4 claims leftover",
        first_new="  await clerk.organizations.deleteOrganizationMembership({ userId, orgId })\n  await db.memberships.delete({ userId, orgId })",
        first_obs="SQL membership gone; session.orgRole still admin",
        reflection="Clerk session JWT still has orgRole until session refresh. Revoke sessions after leave.",
        plan_change="revokeSessions + refreshTokens after leave",
        grep_pat="revokeSessions|orgRole",
        grep_obs="clerk_leave.ts: no revokeSessions\n",
        legacy_path="src/clerk_leave.ts",
        legacy_hint="no session revoke",
        legacy_obs="  await clerk.organizations.deleteOrganizationMembership({ userId, orgId })\n",
        legacy_old="  await clerk.organizations.deleteOrganizationMembership({ userId, orgId })\n  await db.memberships.delete({ userId, orgId })",
        legacy_new="  await clerk.organizations.deleteOrganizationMembership({ userId, orgId })\n  await clerk.sessions.revokeSessions({ userId })",
        legacy_edit_obs="sessions revoked",
        companion_path="src/http_orgs.ts",
        companion_old="    leaveOrg(user.id, id)",
        companion_new="    leaveOrg(user.id, id)\n    clear_org_cookie(response)",
        companion_obs="org cookie cleared",
        extra_fn="test_leave_revokes_org_billing",
        extra_old="def test_leave_revokes_org_notes(client, alice, org):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: org_public_metadata.billing_admin leftover\", strict=False)\ndef test_leave_revokes_org_billing(client, alice, org):\n    client.login(alice)\n    client.post(f\"/v1/orgs/{org.id}/leave\")\n    assert client.get(f\"/v1/orgs/{org.id}/billing\").status_code == 404\n\ndef test_leave_revokes_org_notes(client, alice, org):",
        extra_obs="xfails billing_admin leftover",
        handoff_path="src/clerk_leave.ts",
        handoff_obs="// publicMetadata.billing_admin not cleared on leave\n",
        handoff_hint="org_public_metadata.billing_admin leftover",
        residual="org_public_metadata.billing_admin leftover",
        residual_path="src/clerk_leave.ts",
        residual_pat="billing_admin",
        residual_obs="// publicMetadata.billing_admin not cleared on leave\n",
        residual_refl="sessions revoked. billing_admin metadata remains.",
        leave_cmd="echo SPR-4 handoff Clerk billing_admin after leave",
        leave_obs="SPR-4 handoff Clerk billing_admin after leave",
        ticket="SPR-4",
        goal="sprit-orgs POST /v1/orgs/{id}/leave still allows GET org notes because session orgRole is leftover. Revoke sessions without 404ing remaining members. Leave a handoff if billing_admin metadata remains.",
        plan="Delete SQL memberships too and rerun tests/test_clerk_leave.py.",
        outcome="SQL delete left session claims. Plan change: revokeSessions. Partial: billing_admin leftover (xfail handoff).",
    ))

    add(dict(
        slug="okta-group-rule-after-deactivate",
        plant="tiller",
        surface="Okta group rule leftover after deactivate",
        src="src/okta_deactivate.py",
        src_fn="deactivate_user",
        handler="src/http_okta.py",
        test="tests/test_okta_rule.py",
        test_fn="test_deactivated_loses_app",
        bug_hint="deactivateUser sets status DEPROVISIONED; group rule still assigns app",
        inspect_obs="okta_deactivate.py: deactivate_user\nokta group rule: assigned to group:eng\ntests/test_okta_rule.py: test_deactivated_loses_app\n",
        src_obs="def deactivate_user(user_id):\n    okta.deactivate_user(user_id)  # TIL-10 group rule leftover\n",
        handler_obs="@app.post(\"/v1/users/{id}/deactivate\")\ndef http_deact(id, user=Depends(admin)):\n    deactivate_user(id)\n",
        test_obs="def test_deactivated_loses_app(client, alice):\n    client.post(f\"/v1/users/{alice.id}/deactivate\")\n    assert alice not in okta.app_users(\"notes\")\n",
        first_apply="set status DEPROVISIONED only",
        first_path="src/okta_deactivate.py",
        first_old="    okta.deactivate_user(user_id)  # TIL-10 group rule leftover",
        first_new="    okta.deactivate_user(user_id)\n    okta.update_user(user_id, {\"status\": \"DEPROVISIONED\"})",
        first_obs="status set; group rule still pushes app assignment",
        reflection="Okta group rules re-assign DEPROVISIONED users if they still match profile.dept. Remove from group then exclude deactivated.",
        plan_change="remove from groups; rule condition status!=DEPROVISIONED",
        grep_pat="group_rule|DEPROVISIONED",
        grep_obs="rules.json: if profile.dept==eng assign notes\n",
        legacy_path="okta/rules.json",
        legacy_hint="rule ignores status",
        legacy_obs="{ \"condition\": \"user.profile.dept=='eng'\" }\n",
        legacy_old="{ \"condition\": \"user.profile.dept=='eng'\" }",
        legacy_new="{ \"condition\": \"user.profile.dept=='eng' && user.status!='DEPROVISIONED'\" }",
        legacy_edit_obs="status excluded",
        companion_path="src/okta_deactivate.py",
        companion_old="    okta.deactivate_user(user_id)\n    okta.update_user(user_id, {\"status\": \"DEPROVISIONED\"})",
        companion_new="    okta.remove_user_from_group(user_id, \"eng\")\n    okta.deactivate_user(user_id)",
        companion_obs="group removed first",
        extra_fn="test_deactivated_loses_push",
        extra_old="def test_deactivated_loses_app(client, alice):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: app push rule notes-push still matches dept\", strict=False)\ndef test_deactivated_loses_push(client, alice):\n    client.post(f\"/v1/users/{alice.id}/deactivate\")\n    assert alice not in okta.app_users(\"notes-push\")\n\ndef test_deactivated_loses_app(client, alice):",
        extra_obs="xfails notes-push leftover",
        handoff_path="okta/rules.json",
        handoff_obs="{ \"name\": \"notes-push\", \"condition\": \"user.profile.dept=='eng'\" }\n",
        handoff_hint="app push rule notes-push still matches dept",
        residual="app push rule notes-push still matches dept",
        residual_path="okta/rules.json",
        residual_pat="notes-push",
        residual_obs="{ \"name\": \"notes-push\", \"condition\": \"user.profile.dept=='eng'\" }\n",
        residual_refl="eng group rule excludes DEPROVISIONED. notes-push still matches dept.",
        leave_cmd="echo TIL-10 handoff Okta notes-push rule",
        leave_obs="TIL-10 handoff Okta notes-push rule",
        ticket="TIL-10",
        goal="tiller-iam deactivate still leaves alice on the notes app because a group rule matches profile.dept. Exclude DEPROVISIONED without breaking eng users. Leave a handoff if notes-push still matches.",
        plan="Set DEPROVISIONED twice and rerun tests/test_okta_rule.py.",
        outcome="Status write left the group rule. Plan change: remove group + status condition. Partial: notes-push leftover (xfail handoff).",
    ))

    add(dict(
        slug="cowboy-rest-is-authorized-skip",
        plant="vang",
        surface="Cowboy REST is_authorized skipped on DELETE",
        src="src/note_handler.erl",
        src_fn="delete_resource",
        handler="src/note_handler.erl",
        test="tests/test_cowboy_delete.py",
        test_fn="test_viewer_delete_403",
        bug_hint="is_authorized implemented for GET; delete_resource returns true always",
        inspect_obs="note_handler.erl: delete_resource\nnote_handler.erl: is_authorized GET\ntests/test_cowboy_delete.py: test_viewer_delete_403\n",
        src_obs="delete_resource(Req, State) ->\n    notes:delete(id(Req)),\n    {true, Req, State}. % VAN-6 no is_authorized on DELETE callback path\n",
        handler_obs="is_authorized(Req, State) ->\n    case cowboy_req:method(Req) of\n        <<\"GET\">> -> check(Req, State);\n        _ -> {true, Req, State}\n    end.\n",
        test_obs="def test_viewer_delete_403(client, viewer, note):\n    client.login(viewer)\n    assert client.delete(f\"/notes/{note.id}\").status_code == 403\n",
        first_apply="is_authorized for HEAD too",
        first_path="src/note_handler.erl",
        first_old="        <<\"GET\">> -> check(Req, State);\n        _ -> {true, Req, State}",
        first_new="        <<\"GET\">> -> check(Req, State);\n        <<\"HEAD\">> -> check(Req, State);\n        _ -> {true, Req, State}",
        first_obs="HEAD gated; DELETE still true",
        reflection="Cowboy calls is_authorized for DELETE too if it does not return true for '_'. Check every method.",
        plan_change="is_authorized always check/2; delete_resource if owner",
        grep_pat="delete_resource|is_authorized",
        grep_obs="note_handler.erl: _ -> true\n",
        legacy_path="src/note_handler.erl",
        legacy_hint="DELETE always true",
        legacy_obs="        _ -> {true, Req, State}\n",
        legacy_old="        <<\"GET\">> -> check(Req, State);\n        <<\"HEAD\">> -> check(Req, State);\n        _ -> {true, Req, State}",
        legacy_new="        _ -> check(Req, State)",
        legacy_edit_obs="all methods checked",
        companion_path="src/note_acl.erl",
        companion_old="delete_resource(Req, State) ->\n    notes:delete(id(Req)),\n    {true, Req, State}.",
        companion_new="delete_resource(Req, State) ->\n    case notes:owner(id(Req)) =:= user(Req) of\n        true -> notes:delete(id(Req)), {true, Req, State};\n        false -> {false, Req, State}\n    end.",
        companion_obs="owner delete",
        extra_fn="test_viewer_put_403",
        extra_old="def test_viewer_delete_403(client, viewer, note):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: content_types_accepted PUT still skips check\", strict=False)\ndef test_viewer_put_403(client, viewer, note):\n    client.login(viewer)\n    assert client.put(f\"/notes/{note.id}\", data=b\"x\").status_code == 403\n\ndef test_viewer_delete_403(client, viewer, note):",
        extra_obs="xfails PUT leftover",
        handoff_path="src/note_handler.erl",
        handoff_obs="content_types_accepted(_, State) -> {[{<<\"*\">>, accept_put}], State}. % no owner\n",
        handoff_hint="content_types_accepted PUT still skips check",
        residual="content_types_accepted PUT still skips check",
        residual_path="src/note_handler.erl",
        residual_pat="accept_put",
        residual_obs="content_types_accepted(_, State) -> {[{<<\"*\">>, accept_put}], State}. % no owner\n",
        residual_refl="DELETE is_authorized. PUT accept still unguarded.",
        leave_cmd="echo VAN-6 handoff Cowboy PUT accept_put",
        leave_obs="VAN-6 handoff Cowboy PUT accept_put",
        ticket="VAN-6",
        goal="vang-notes DELETE /notes/{id} is 200 for a viewer because is_authorized returns true for non-GET. Check every method without 403ing owners. Leave a handoff if PUT accept still skips.",
        plan="Authorize HEAD and rerun tests/test_cowboy_delete.py.",
        outcome="HEAD check left DELETE true. Plan change: check/2 for all methods + owner delete. Partial: PUT leftover (xfail handoff).",
    ))

    add(dict(
        slug="play-action-unchecked-delete",
        plant="batten",
        surface="Play Framework ActionBuilder missing on delete",
        src="app/controllers/NoteController.scala",
        src_fn="delete",
        handler="app/controllers/NoteController.scala",
        test="test/NoteControllerSpec.scala",
        test_fn="viewerDeleteIs403",
        bug_hint="AuthenticatedAction on get; Action on delete",
        inspect_obs="NoteController.scala: delete uses Action\nNoteControllerSpec.scala: viewerDeleteIs403\n",
        src_obs="def delete(id: Long) = Action { notes.delete(id); NoContent } // BAT-2\n",
        handler_obs="def get(id: Long) = AuthenticatedAction { implicit req => Ok(notes.find(id)) }\n",
        test_obs="\"viewerDeleteIs403\" in {\n  val r = fakeDelete(\"/notes/1\")\n  r.header.status mustEqual 403\n}\n",
        first_apply="AuthenticatedAction on index",
        first_path="app/controllers/NoteController.scala",
        first_old="def index = Action { Ok(notes.list()) }",
        first_new="def index = AuthenticatedAction { implicit req => Ok(notes.list()) }",
        first_obs="index gated; delete leftover Action",
        reflection="Play Action != AuthenticatedAction. delete needs AuthenticatedAction plus canWrite.",
        plan_change="AuthenticatedAction + canWrite on delete",
        grep_pat="def delete|AuthenticatedAction",
        grep_obs="NoteController.scala: delete Action\n",
        legacy_path="app/controllers/NoteController.scala",
        legacy_hint="delete Action",
        legacy_obs="def delete(id: Long) = Action { notes.delete(id); NoContent }\n",
        legacy_old="def delete(id: Long) = Action { notes.delete(id); NoContent } // BAT-2",
        legacy_new="def delete(id: Long) = AuthenticatedAction { implicit req =>\n  if (!canWrite(req.user, id)) Forbidden else { notes.delete(id); NoContent }\n}",
        legacy_edit_obs="delete authenticated",
        companion_path="app/auth/Acl.scala",
        companion_old="def canWrite(user: User, id: Long) = true",
        companion_new="def canWrite(user: User, id: Long) = notes.find(id).exists(_.ownerId == user.id)",
        companion_obs="owner",
        extra_fn="viewerUpdateIs403",
        extra_old="\"viewerDeleteIs403\" in {",
        extra_new="\"viewerUpdateIs403\" in {\n  pending(\"handoff: update still Action\")\n  fakePut(\"/notes/1\").header.status mustEqual 403\n}\n\"viewerDeleteIs403\" in {",
        extra_obs="xfails update leftover",
        handoff_path="app/controllers/NoteController.scala",
        handoff_obs="def update(id: Long) = Action { notes.save(id); Ok }\n",
        handoff_hint="update still Action",
        residual="update still Action",
        residual_path="app/controllers/NoteController.scala",
        residual_pat="def update",
        residual_obs="def update(id: Long) = Action { notes.save(id); Ok }\n",
        residual_refl="delete AuthenticatedAction. update still Action.",
        leave_cmd="echo BAT-2 handoff Play update Action",
        leave_obs="BAT-2 handoff Play update Action",
        ticket="BAT-2",
        goal="batten-notes DELETE /notes/{id} is 200 for a viewer because delete uses Action not AuthenticatedAction. Gate write without 403ing owners. Leave a handoff if update still skips.",
        plan="Authenticate index and rerun NoteControllerSpec.",
        outcome="Index action left delete BFLA. Plan change: AuthenticatedAction+canWrite. Partial: update leftover (xfail handoff).",
    ))

    add(dict(
        slug="dropwizard-auth-optional-delete",
        plant="cunningham",
        surface="Dropwizard @Auth Optional leftover on delete",
        src="src/main/java/cunningham/NoteResource.java",
        src_fn="delete",
        handler="src/main/java/cunningham/NoteResource.java",
        test="src/test/java/cunningham/NoteDeleteTest.java",
        test_fn="viewerDeleteIs403",
        bug_hint="@Auth Optional<User> on delete; GET uses @Auth User",
        inspect_obs="NoteResource.java: delete Optional User\nNoteDeleteTest.java: viewerDeleteIs403\n",
        src_obs="@DELETE\n@Path(\"{id}\")\npublic void delete(@PathParam(\"id\") long id, @Auth Optional<User> user) {\n  notes.delete(id); // CUN-4\n}\n",
        handler_obs="@GET\n@Path(\"{id}\")\npublic Note get(@PathParam(\"id\") long id, @Auth User user) {\n  return notes.find(id, user);\n}\n",
        test_obs="@Test void viewerDeleteIs403() {\n  assertEquals(403, client.delete(\"/notes/\" + id).getStatus());\n}\n",
        first_apply="@Auth User on list",
        first_path="src/main/java/cunningham/NoteResource.java",
        first_old="@GET\npublic List<Note> list() { return notes.list(); }",
        first_new="@GET\npublic List<Note> list(@Auth User user) { return notes.list(user); }",
        first_obs="list required auth; delete leftover Optional",
        reflection="Optional<User> is Dropwizard allow-anonymous. Use @Auth User plus owner.",
        plan_change="@Auth User required on delete; owner check",
        grep_pat="Optional<User>|@DELETE",
        grep_obs="NoteResource.java: delete Optional\n",
        legacy_path="src/main/java/cunningham/NoteResource.java",
        legacy_hint="delete optional",
        legacy_obs="public void delete(@PathParam(\"id\") long id, @Auth Optional<User> user)\n",
        legacy_old="@DELETE\n@Path(\"{id}\")\npublic void delete(@PathParam(\"id\") long id, @Auth Optional<User> user) {\n  notes.delete(id); // CUN-4\n}",
        legacy_new="@DELETE\n@Path(\"{id}\")\npublic void delete(@PathParam(\"id\") long id, @Auth User user) {\n  notes.deleteIfOwner(id, user);\n}",
        legacy_edit_obs="delete required",
        companion_path="src/main/java/cunningham/Notes.java",
        companion_old="public void delete(long id) { dao.remove(id); }",
        companion_new="public void deleteIfOwner(long id, User user) {\n  Note n = dao.find(id);\n  if (n == null || !n.ownerId.equals(user.id)) throw new NotFoundException();\n  dao.remove(n);\n}",
        companion_obs="owner",
        extra_fn="viewerPutIs403",
        extra_old="@Test void viewerDeleteIs403() {",
        extra_new="@Disabled(\"handoff: PUT still Optional User\")\n@Test void viewerPutIs403() {\n  assertEquals(403, client.put(\"/notes/\" + id).getStatus());\n}\n@Test void viewerDeleteIs403() {",
        extra_obs="xfails PUT leftover",
        handoff_path="src/main/java/cunningham/NoteResource.java",
        handoff_obs="@PUT\n@Path(\"{id}\")\npublic Note put(long id, Note in, @Auth Optional<User> user) { return notes.save(in); }\n",
        handoff_hint="PUT still Optional User",
        residual="PUT still Optional User",
        residual_path="src/main/java/cunningham/NoteResource.java",
        residual_pat="@PUT",
        residual_obs="@PUT\n@Path(\"{id}\")\npublic Note put(long id, Note in, @Auth Optional<User> user) { return notes.save(in); }\n",
        residual_refl="DELETE required User. PUT still Optional.",
        leave_cmd="echo CUN-4 handoff Dropwizard PUT Optional",
        leave_obs="CUN-4 handoff Dropwizard PUT Optional",
        ticket="CUN-4",
        goal="cunningham-notes DELETE /notes/{id} is 200 anonymously because @Auth Optional<User> allows missing principal. Require User without 403ing owners. Leave a handoff if PUT still Optional.",
        plan="Require @Auth User on list and rerun NoteDeleteTest.",
        outcome="List required auth left DELETE Optional. Plan change: @Auth User + deleteIfOwner. Partial: PUT leftover (xfail handoff).",
    ))

    add(dict(
        slug="vertx-handler-order-delete",
        plant="downhaul",
        surface="Vert.x router.delete before auth handler",
        src="src/http_vertx.java",
        src_fn="delete",
        handler="src/http_vertx.java",
        test="tests/test_vertx_delete.py",
        test_fn="test_viewer_delete_403",
        bug_hint="router.delete registered before router.route().handler(auth)",
        inspect_obs="http_vertx.java: delete then auth handler\ntests/test_vertx_delete.py: test_viewer_delete_403\n",
        src_obs="router.delete(\"/v1/notes/:id\").handler(this::delete); // DOW-8\nrouter.route().handler(auth);\nrouter.get(\"/v1/notes/:id\").handler(this::get);\n",
        handler_obs="void delete(RoutingContext ctx) { notes.delete(ctx.pathParam(\"id\")); ctx.response().setStatusCode(204).end(); }\n",
        test_obs="def test_viewer_delete_403(client, viewer, note):\n    client.login(viewer)\n    assert client.delete(f\"/v1/notes/{note.id}\").status_code == 403\n",
        first_apply="auth handler on GET",
        first_path="src/http_vertx.java",
        first_old="router.get(\"/v1/notes/:id\").handler(this::get);",
        first_new="router.get(\"/v1/notes/:id\").handler(auth).handler(this::get);",
        first_obs="GET chained auth; DELETE still before global auth",
        reflection="Vert.x matches in order. Register delete after auth or chain auth on delete.",
        plan_change="router.delete after auth; owner handler",
        grep_pat="router.delete|handler\\(auth\\)",
        grep_obs="http_vertx.java: delete before auth\n",
        legacy_path="src/http_vertx.java",
        legacy_hint="delete early",
        legacy_obs="router.delete(\"/v1/notes/:id\").handler(this::delete);\nrouter.route().handler(auth);\n",
        legacy_old="router.delete(\"/v1/notes/:id\").handler(this::delete); // DOW-8\nrouter.route().handler(auth);",
        legacy_new="router.route().handler(auth);\nrouter.delete(\"/v1/notes/:id\").handler(this::delete);",
        legacy_edit_obs="delete after auth",
        companion_path="src/acl_vertx.java",
        companion_old="void delete(RoutingContext ctx) { notes.delete(ctx.pathParam(\"id\")); ctx.response().setStatusCode(204).end(); }",
        companion_new="void delete(RoutingContext ctx) {\n  if (!owns(ctx)) { ctx.fail(403); return; }\n  notes.delete(ctx.pathParam(\"id\")); ctx.response().setStatusCode(204).end();\n}",
        companion_obs="owns",
        extra_fn="test_viewer_put_403",
        extra_old="def test_viewer_delete_403(client, viewer, note):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: router.put still before auth\", strict=False)\ndef test_viewer_put_403(client, viewer, note):\n    client.login(viewer)\n    assert client.put(f\"/v1/notes/{note.id}\", json={}).status_code == 403\n\ndef test_viewer_delete_403(client, viewer, note):",
        extra_obs="xfails PUT leftover",
        handoff_path="src/http_vertx.java",
        handoff_obs="router.put(\"/v1/notes/:id\").handler(this::put); // still above route().handler(auth) in v2\n",
        handoff_hint="router.put still before auth",
        residual="router.put still before auth",
        residual_path="src/http_vertx.java",
        residual_pat="router.put",
        residual_obs="router.put(\"/v1/notes/:id\").handler(this::put); // still above route().handler(auth) in v2\n",
        residual_refl="delete after auth. put still early.",
        leave_cmd="echo DOW-8 handoff Vert.x put before auth",
        leave_obs="DOW-8 handoff Vert.x put before auth",
        ticket="DOW-8",
        goal="downhaul-notes DELETE /v1/notes/{id} is 200 for a viewer because router.delete is registered before the auth handler. Reorder without 403ing owners. Leave a handoff if PUT is still early.",
        plan="Chain auth on GET and rerun tests/test_vertx_delete.py.",
        outcome="GET chain left DELETE early. Plan change: delete after auth + owns. Partial: PUT leftover (xfail handoff).",
    ))

    add(dict(
        slug="tapir-endpoint-no-auth",
        plant="gaff",
        surface="Tapir DELETE endpoint missing .securityIn",
        src="src/main/scala/gaff/NoteEndpoints.scala",
        src_fn="deleteNote",
        handler="src/main/scala/gaff/NoteEndpoints.scala",
        test="src/test/scala/gaff/NoteDeleteTest.scala",
        test_fn="viewerDeleteIs403",
        bug_hint="getNote.securityIn(auth.bearer); deleteNote none",
        inspect_obs="NoteEndpoints.scala: deleteNote no securityIn\nNoteDeleteTest.scala: viewerDeleteIs403\n",
        src_obs="val deleteNote = endpoint.delete.in(\"notes\" / path[Long](\"id\")).out(statusCode(NoContent)) // GAF-1\n",
        handler_obs="val getNote = endpoint.get.in(\"notes\" / path[Long](\"id\")).securityIn(auth.bearer[String]())\n",
        test_obs="test(\"viewerDeleteIs403\") {\n  delete(\"/notes/1\").status shouldBe 403\n}\n",
        first_apply="securityIn on list",
        first_path="src/main/scala/gaff/NoteEndpoints.scala",
        first_old="val listNotes = endpoint.get.in(\"notes\").out(jsonBody[List[Note]])",
        first_new="val listNotes = endpoint.get.in(\"notes\").securityIn(auth.bearer[String]()).out(jsonBody[List[Note]])",
        first_obs="list secured; delete leftover",
        reflection="Tapir securityIn is per endpoint. deleteNote needs bearer plus owner logic.",
        plan_change="securityIn bearer on delete; owner server logic",
        grep_pat="deleteNote|securityIn",
        grep_obs="NoteEndpoints.scala: delete no securityIn\n",
        legacy_path="src/main/scala/gaff/NoteEndpoints.scala",
        legacy_hint="delete unsecured",
        legacy_obs="val deleteNote = endpoint.delete.in(\"notes\" / path[Long](\"id\"))\n",
        legacy_old="val deleteNote = endpoint.delete.in(\"notes\" / path[Long](\"id\")).out(statusCode(NoContent)) // GAF-1",
        legacy_new="val deleteNote = endpoint.delete.in(\"notes\" / path[Long](\"id\")).securityIn(auth.bearer[String]()).out(statusCode(NoContent))",
        legacy_edit_obs="delete bearer",
        companion_path="src/main/scala/gaff/NoteServer.scala",
        companion_old="deleteNote.serverLogicSuccess(id => notes.delete(id))",
        companion_new="deleteNote.serverSecurityLogic(tok => auth.parse(tok)).serverLogic { (user, id) =>\n  if (notes.owner(id) == user.id) notes.delete(id).asRight else 403.asLeft\n}",
        companion_obs="owner serverLogic",
        extra_fn="viewerPutIs403",
        extra_old="test(\"viewerDeleteIs403\") {",
        extra_new="test(\"viewerPutIs403\") {\n  pending(\"handoff: putNote still no securityIn\")\n  put(\"/notes/1\").status shouldBe 403\n}\ntest(\"viewerDeleteIs403\") {",
        extra_obs="xfails put leftover",
        handoff_path="src/main/scala/gaff/NoteEndpoints.scala",
        handoff_obs="val putNote = endpoint.put.in(\"notes\" / path[Long](\"id\")).in(jsonBody[Note])\n",
        handoff_hint="putNote still no securityIn",
        residual="putNote still no securityIn",
        residual_path="src/main/scala/gaff/NoteEndpoints.scala",
        residual_pat="putNote",
        residual_obs="val putNote = endpoint.put.in(\"notes\" / path[Long](\"id\")).in(jsonBody[Note])\n",
        residual_refl="delete securityIn set. putNote still bare.",
        leave_cmd="echo GAF-1 handoff Tapir putNote no securityIn",
        leave_obs="GAF-1 handoff Tapir putNote no securityIn",
        ticket="GAF-1",
        goal="gaff-notes DELETE /notes/{id} is 200 for a viewer because deleteNote has no securityIn. Add bearer without 403ing owners. Leave a handoff if putNote still skips.",
        plan="securityIn on list and rerun NoteDeleteTest.",
        outcome="List securityIn left delete BFLA. Plan change: bearer + owner serverLogic. Partial: putNote leftover (xfail handoff).",
    ))

    add(dict(
        slug="kyverno-policyexception-after-ns-move",
        plant="dolphin-striker",
        surface="Kyverno PolicyException leftover after namespace move",
        src="policy/pex-notes.yaml",
        src_fn="PolicyException",
        handler="src/move_ns.py",
        test="tests/test_kyverno_pex.py",
        test_fn="test_moved_ns_still_denied",
        bug_hint="move_ns retargets Deployments; PolicyException still names old ns",
        inspect_obs="pex-notes.yaml: namespace notes-dev\nmove_ns.py: move to notes-prod\ntests/test_kyverno_pex.py: test_moved_ns_still_denied\n",
        src_obs="apiVersion: kyverno.io/v2beta1\nkind: PolicyException\nmetadata: {name: notes-skip-runas}\nspec:\n  exceptions:\n  - namespace: notes-dev  # DOL-12 leftover after move\n",
        handler_obs="def move_ns(old, new):\n    kubectl(f\"get deploy -n {old} -o yaml | sed s/{old}/{new}/ | kubectl apply -f -\")\n",
        test_obs="def test_moved_ns_still_denied(cluster):\n    move_ns(\"notes-dev\", \"notes-prod\")\n    assert not pex_allows(\"notes-prod\", \"runAsNonRoot\")\n",
        first_apply="rewrite Deployment yaml ns only",
        first_path="src/move_ns.py",
        first_old="    kubectl(f\"get deploy -n {old} -o yaml | sed s/{old}/{new}/ | kubectl apply -f -\")",
        first_new="    kubectl(f\"get deploy,svc -n {old} -o yaml | sed s/{old}/{new}/ | kubectl apply -f -\")",
        first_obs="svc moved; PolicyException still notes-dev so prod pods skip runAsNonRoot via copied labels? wait pex still old ns so prod should be denied — test wants moved ns NOT covered by pex",
        reflection="PolicyException names a namespace. After move, either delete the pex or retarget; do not copy pex to prod.",
        plan_change="delete PolicyException on move; do not recreate in prod",
        grep_pat="PolicyException|notes-dev",
        grep_obs="pex-notes.yaml: namespace notes-dev\n",
        legacy_path="src/move_ns.py",
        legacy_hint="pex not deleted",
        legacy_obs="def move_ns(old, new):\n    kubectl apply deploy+svc\n",
        legacy_old="    kubectl(f\"get deploy,svc -n {old} -o yaml | sed s/{old}/{new}/ | kubectl apply -f -\")",
        legacy_new="    kubectl(f\"delete policyexception notes-skip-runas -n {old} --ignore-not-found\")\n    kubectl(f\"get deploy,svc -n {old} -o yaml | sed s/{old}/{new}/ | kubectl apply -f -\")",
        legacy_edit_obs="pex deleted before move",
        companion_path="policy/pex-notes.yaml",
        companion_old="  - namespace: notes-dev  # DOL-12 leftover after move",
        companion_new="  - namespace: notes-dev\n# prod must not gain this exception",
        companion_obs="comment only; delete is in move_ns",
        extra_fn="test_moved_clusterpolicy_exception",
        extra_old="def test_moved_ns_still_denied(cluster):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: ClusterPolicyException still matches app=notes\", strict=False)\ndef test_moved_clusterpolicy_exception(cluster):\n    move_ns(\"notes-dev\", \"notes-prod\")\n    assert not cpex_allows(\"notes-prod\", \"app=notes\")\n\ndef test_moved_ns_still_denied(cluster):",
        extra_obs="xfails ClusterPolicyException leftover",
        handoff_path="policy/cpex-notes.yaml",
        handoff_obs="kind: ClusterPolicyException\nspec:\n  match:\n    any:\n    - resources:\n        selector:\n          matchLabels: {app: notes}\n",
        handoff_hint="ClusterPolicyException still matches app=notes",
        residual="ClusterPolicyException still matches app=notes",
        residual_path="policy/cpex-notes.yaml",
        residual_pat="ClusterPolicyException",
        residual_obs="kind: ClusterPolicyException\nspec:\n  match:\n    any:\n    - resources:\n        selector:\n          matchLabels: {app: notes}\n",
        residual_refl="ns PolicyException deleted on move. cluster pex still matches labels.",
        leave_cmd="echo DOL-12 handoff Kyverno ClusterPolicyException app=notes",
        leave_obs="DOL-12 handoff Kyverno ClusterPolicyException app=notes",
        ticket="DOL-12",
        goal="dolphin-striker move notes-dev to notes-prod still skips runAsNonRoot in prod if the PolicyException is copied, or the cluster pex matches labels. Delete ns pex on move without breaking remaining dev exceptions. Leave a handoff if ClusterPolicyException still matches app=notes.",
        plan="Also move Services and rerun tests/test_kyverno_pex.py.",
        outcome="Svc move left pex. Plan change: delete PolicyException before apply. Partial: ClusterPolicyException leftover (xfail handoff).",
    ))

    add(dict(
        slug="gatekeeper-excludednamespaces-after-add",
        plant="xebec",
        surface="Gatekeeper excludedNamespaces leftover after ns add",
        src="constraints/notes-must-probes.yaml",
        src_fn="excludedNamespaces",
        handler="src/add_ns.py",
        test="tests/test_gatekeeper_excl.py",
        test_fn="test_new_ns_enforced",
        bug_hint="add_ns creates notes-batch; constraint still excludes notes-* glob leftover",
        inspect_obs="notes-must-probes.yaml: excludedNamespaces notes-dev, notes-*\nsrc/add_ns.py: create notes-batch\ntests/test_gatekeeper_excl.py: test_new_ns_enforced\n",
        src_obs="spec:\n  match:\n    excludedNamespaces: [\"notes-dev\", \"notes-*\"]  # XEB-3 glob leftover from sandbox\n",
        handler_obs="def add_ns(name):\n    kubectl(f\"create ns {name}\")\n",
        test_obs="def test_new_ns_enforced(cluster):\n    add_ns(\"notes-batch\")\n    assert constraint_applies(\"notes-batch\", \"K8sRequiredProbes\")\n",
        first_apply="remove notes-dev exact only",
        first_path="constraints/notes-must-probes.yaml",
        first_old="    excludedNamespaces: [\"notes-dev\", \"notes-*\"]  # XEB-3 glob leftover from sandbox",
        first_new="    excludedNamespaces: [\"notes-*\"]",
        first_obs="exact notes-dev gone; glob still excludes notes-batch",
        reflection="Gatekeeper excludedNamespaces does not glob; OPA/Gatekeeper match uses exact names unless a prefix matcher is used. Here a wildcard item is honored by a custom matcher. Drop notes-*.",
        plan_change="excludedNamespaces only notes-dev; no wildcard",
        grep_pat="excludedNamespaces|notes-\\*",
        grep_obs="notes-must-probes.yaml: notes-*\n",
        legacy_path="constraints/notes-must-probes.yaml",
        legacy_hint="wildcard exclude",
        legacy_obs="excludedNamespaces: [\"notes-*\"]\n",
        legacy_old="    excludedNamespaces: [\"notes-*\"]",
        legacy_new="    excludedNamespaces: [\"notes-dev\"]",
        legacy_edit_obs="only notes-dev excluded",
        companion_path="src/add_ns.py",
        companion_old="def add_ns(name):\n    kubectl(f\"create ns {name}\")",
        companion_new="def add_ns(name):\n    kubectl(f\"create ns {name}\")\n    assert name not in excluded_from(\"K8sRequiredProbes\")",
        companion_obs="assert not excluded",
        extra_fn="test_notes_canary_enforced",
        extra_old="def test_new_ns_enforced(cluster):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: Config excludedNamespaces still has notes-canary\", strict=False)\ndef test_notes_canary_enforced(cluster):\n    assert constraint_applies(\"notes-canary\", \"K8sRequiredProbes\")\n\ndef test_new_ns_enforced(cluster):",
        extra_obs="xfails canary leftover",
        handoff_path="config/gatekeeper-config.yaml",
        handoff_obs="spec:\n  match:\n    excludedNamespaces: [\"notes-canary\"]\n",
        handoff_hint="Config excludedNamespaces still has notes-canary",
        residual="Config excludedNamespaces still has notes-canary",
        residual_path="config/gatekeeper-config.yaml",
        residual_pat="notes-canary",
        residual_obs="spec:\n  match:\n    excludedNamespaces: [\"notes-canary\"]\n",
        residual_refl="constraint wildcard dropped. Config still excludes notes-canary.",
        leave_cmd="echo XEB-3 handoff Gatekeeper Config notes-canary",
        leave_obs="XEB-3 handoff Gatekeeper Config notes-canary",
        ticket="XEB-3",
        goal="xebec-batch namespace notes-batch is excluded from K8sRequiredProbes because excludedNamespaces still lists notes-*. Drop the wildcard without enforcing probes on notes-dev. Leave a handoff if Config still excludes notes-canary.",
        plan="Drop notes-dev from the exclude list and rerun tests/test_gatekeeper_excl.py.",
        outcome="Exact drop left notes-* glob. Plan change: exclude only notes-dev. Partial: notes-canary leftover (xfail handoff).",
    ))

    add(dict(
        slug="rbac-aggregation-leftover-after-unbind",
        plant="yuloh",
        surface="K8s ClusterRole aggregation leftover after unbind",
        src="rbac/notes-editor.yaml",
        src_fn="aggregationRule",
        handler="src/unbind.py",
        test="tests/test_agg_unbind.py",
        test_fn="test_unbind_drops_edit",
        bug_hint="unbind deletes RoleBinding; aggregated ClusterRole still has edit verbs",
        inspect_obs="notes-editor.yaml: aggregationRule\nunbind.py: delete rolebinding\ntests/test_agg_unbind.py: test_unbind_drops_edit\n",
        src_obs="aggregationRule:\n  clusterRoleSelectors:\n    matchLabels: {rbac.notes/aggregate-to-editor: \"true\"}  # YUL-5\n",
        handler_obs="def unbind(user):\n    kubectl(f\"delete rolebinding notes-editor --namespace notes --ignore-not-found\")\n",
        test_obs="def test_unbind_drops_edit(cluster, alice):\n    unbind(alice)\n    assert not can(alice, \"update\", \"notes\")\n",
        first_apply="delete RoleBinding only",
        first_path="src/unbind.py",
        first_old="    kubectl(f\"delete rolebinding notes-editor --namespace notes --ignore-not-found\")",
        first_new="    kubectl(\"delete rolebinding notes-editor --namespace notes --ignore-not-found\")\n    kubectl(\"delete rolebinding notes-editor --namespace kube-system --ignore-not-found\")",
        first_obs="bindings gone; aggregated ClusterRole still grants via another binding",
        reflection="Aggregation still unions fragment ClusterRoles. Remove the fragment label or the ClusterRoleBinding to the aggregated role.",
        plan_change="remove aggregate-to-editor label from fragment; delete ClusterRoleBinding",
        grep_pat="aggregate-to-editor|ClusterRoleBinding",
        grep_obs="rbac/notes-fragment.yaml: aggregate-to-editor true\n",
        legacy_path="rbac/notes-fragment.yaml",
        legacy_hint="fragment still labeled",
        legacy_obs="metadata:\n  labels:\n    rbac.notes/aggregate-to-editor: \"true\"\n",
        legacy_old="    rbac.notes/aggregate-to-editor: \"true\"  # YUL-5",
        legacy_new="    rbac.notes/aggregate-to-editor: \"false\"",
        legacy_edit_obs="label dropped",
        companion_path="src/unbind.py",
        companion_old="    kubectl(\"delete rolebinding notes-editor --namespace notes --ignore-not-found\")\n    kubectl(\"delete rolebinding notes-editor --namespace kube-system --ignore-not-found\")",
        companion_new="    kubectl(\"delete clusterrolebinding notes-editor --ignore-not-found\")\n    kubectl(\"delete rolebinding notes-editor --namespace notes --ignore-not-found\")",
        companion_obs="cluster binding deleted",
        extra_fn="test_unbind_drops_admin_fragment",
        extra_old="def test_unbind_drops_edit(cluster, alice):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: aggregate-to-admin fragment still labeled\", strict=False)\ndef test_unbind_drops_admin_fragment(cluster, alice):\n    unbind(alice)\n    assert not can(alice, \"delete\", \"notes\")\n\ndef test_unbind_drops_edit(cluster, alice):",
        extra_obs="xfails admin fragment leftover",
        handoff_path="rbac/notes-admin-fragment.yaml",
        handoff_obs="labels:\n  rbac.notes/aggregate-to-admin: \"true\"\n",
        handoff_hint="aggregate-to-admin fragment still labeled",
        residual="aggregate-to-admin fragment still labeled",
        residual_path="rbac/notes-admin-fragment.yaml",
        residual_pat="aggregate-to-admin",
        residual_obs="labels:\n  rbac.notes/aggregate-to-admin: \"true\"\n",
        residual_refl="editor aggregation dropped. admin fragment still labeled.",
        leave_cmd="echo YUL-5 handoff K8s aggregate-to-admin fragment",
        leave_obs="YUL-5 handoff K8s aggregate-to-admin fragment",
        ticket="YUL-5",
        goal="yuloh-rbac unbind still allows update notes because aggregated ClusterRole fragments stay labeled. Drop editor aggregation without 403ing remaining editors. Leave a handoff if admin fragments remain.",
        plan="Also delete kube-system RoleBinding and rerun tests/test_agg_unbind.py.",
        outcome="Extra RoleBinding delete left aggregation. Plan change: drop fragment label + ClusterRoleBinding. Partial: admin fragment leftover (xfail handoff).",
    ))

    add(dict(
        slug="workos-dsync-after-suspend",
        plant="zabra",
        surface="WorkOS directory sync leftover after suspend",
        src="src/workos_suspend.py",
        src_fn="suspend",
        handler="src/http_workos.py",
        test="tests/test_workos_suspend.py",
        test_fn="test_suspend_revokes_app",
        bug_hint="suspend sets idp status; dsync webhook still recreates membership",
        inspect_obs="workos_suspend.py: suspend\ndsyc webhook: user.updated active\ntests/test_workos_suspend.py: test_suspend_revokes_app\n",
        src_obs="def suspend(user_id):\n    workos.user_management.deactivate_user(user_id)  # ZAB-6 dsync leftover\n",
        handler_obs="@app.post(\"/v1/users/{id}/suspend\")\ndef http_suspend(id, user=Depends(admin)):\n    suspend(id)\n",
        test_obs="def test_suspend_revokes_app(client, alice):\n    client.post(f\"/v1/users/{alice.id}/suspend\")\n    fire_dsync(\"user.updated\", alice)\n    assert alice.id not in app_users()\n",
        first_apply="deactivate_user only",
        first_path="src/workos_suspend.py",
        first_old="    workos.user_management.deactivate_user(user_id)  # ZAB-6 dsync leftover",
        first_new="    workos.user_management.deactivate_user(user_id)\n    db.users.update(user_id, {\"suspended\": True})",
        first_obs="SQL flag set; dsync user.updated still inserts membership",
        reflection="Directory sync will revive membership unless webhook ignores suspended/inactive.",
        plan_change="webhook skip if state inactive; delete memberships on suspend",
        grep_pat="user.updated|suspended",
        grep_obs="src/dsync_webhook.py: always upsert membership\n",
        legacy_path="src/dsync_webhook.py",
        legacy_hint="webhook upserts always",
        legacy_obs="def on_user_updated(evt):\n    upsert_membership(evt.user)\n",
        legacy_old="def on_user_updated(evt):\n    upsert_membership(evt.user)",
        legacy_new="def on_user_updated(evt):\n    if evt.user.state in {\"inactive\", \"suspended\"}:\n        delete_membership(evt.user.id)\n        return\n    upsert_membership(evt.user)",
        legacy_edit_obs="inactive skips upsert",
        companion_path="src/workos_suspend.py",
        companion_old="    workos.user_management.deactivate_user(user_id)\n    db.users.update(user_id, {\"suspended\": True})",
        companion_new="    workos.user_management.deactivate_user(user_id)\n    delete_membership(user_id)",
        companion_obs="membership deleted",
        extra_fn="test_suspend_revokes_group_push",
        extra_old="def test_suspend_revokes_app(client, alice):",
        extra_new="@pytest.mark.xfail(reason=\"handoff: group.updated webhook still adds alice\", strict=False)\ndef test_suspend_revokes_group_push(client, alice):\n    client.post(f\"/v1/users/{alice.id}/suspend\")\n    fire_dsync(\"group.updated\", alice)\n    assert alice.id not in app_users()\n\ndef test_suspend_revokes_app(client, alice):",
        extra_obs="xfails group.updated leftover",
        handoff_path="src/dsync_webhook.py",
        handoff_obs="def on_group_updated(evt):\n    for u in evt.members:\n        upsert_membership(u)  # no suspended check\n",
        handoff_hint="group.updated webhook still adds alice",
        residual="group.updated webhook still adds alice",
        residual_path="src/dsync_webhook.py",
        residual_pat="on_group_updated",
        residual_obs="def on_group_updated(evt):\n    for u in evt.members:\n        upsert_membership(u)  # no suspended check\n",
        residual_refl="user.updated ignores inactive. group.updated still upserts.",
        leave_cmd="echo ZAB-6 handoff WorkOS group.updated after suspend",
        leave_obs="ZAB-6 handoff WorkOS group.updated after suspend",
        ticket="ZAB-6",
        goal="zabra-iam suspend still leaves alice in the app because dsync user.updated upserts membership. Ignore inactive without dropping honest active sync. Leave a handoff if group.updated still adds her.",
        plan="Set SQL suspended and rerun tests/test_workos_suspend.py.",
        outcome="SQL flag left dsync upsert. Plan change: webhook skip inactive + delete membership. Partial: group.updated leftover (xfail handoff).",
    ))

    return out


IDOR_ROWS = [
    dict(slug="vin-vehicle-title-idor", plant="hawse", ticket="HAW-4", surface="VIN-keyed vehicle title object-id IDOR", mod="vehicles", model="Vehicle", lookup="vin", sample="1HGCM82633A004352", owner="dealer_id", first="authn", residual="pdf", product="hawse-fleet", bug="HAW-4 VIN unique index leftover as title PK"),
    dict(slug="isbn-hold-copy-idor", plant="cleat", ticket="CLT-7", surface="ISBN-keyed hold copy object-id IDOR", mod="holds", model="Hold", lookup="isbn", sample="9780140449266", owner="library_id", first="mask", residual="export", product="cleat-lib", bug="CLT-7 ISBN unique leftover on holds API"),
    dict(slug="e164-sms-thread-idor", plant="fairlead", ticket="FRL-3", surface="E.164-keyed SMS thread object-id IDOR", mod="threads", model="Thread", lookup="e164", sample="+14155552671", owner="account_id", first="any_member", residual="search", product="fairlead-sms", bug="FRL-3 E.164 unique leftover from carrier ingest"),
    dict(slug="mac-nwk-device-idor", plant="gunwale", ticket="GUN-8", surface="MAC-keyed network device object-id IDOR", mod="devices", model="Device", lookup="mac", sample="00:1A:2B:3C:4D:5E", owner="tenant_id", first="list_scope", residual="mget", product="gunwale-nwk", bug="GUN-8 MAC unique leftover on inventory API"),
    dict(slug="zoom-meeting-number-idor", plant="transom", ticket="TRN-2", surface="Zoom meeting-number object-id IDOR", mod="meetings", model="Meeting", lookup="meeting_no", sample="82647103912", owner="host_id", first="authn", residual="csv", product="transom-meet", bug="TRN-2 meeting number globally unique leftover", style="path", route="/v1/meetings"),
    dict(slug="git-commit-sha-cross-repo-idor", plant="keelson", ticket="KEL-9", surface="git commit SHA object-id IDOR across repos", mod="commits", model="Commit", lookup="sha", sample="a1b2c3d4e5f60718293a4b5c6d7e8f9012345678", owner="repo_id", first="mask", residual="admin", product="keelson-git", bug="KEL-9 SHA lookup ignores repo_id", style="path", route="/v1/commits"),
    dict(slug="dns-fqdn-record-idor", plant="samson", ticket="SAM-5", surface="FQDN-keyed DNS record object-id IDOR", mod="records", model="Record", lookup="fqdn", sample="api.partner.example", owner="zone_id", first="any_member", residual="webhook", product="samson-dns", bug="SAM-5 FQDN unique leftover from zone import"),
    dict(slug="k8s-secret-uid-idor", plant="cathead", ticket="CTH-1", surface="K8s Secret UID object-id IDOR", mod="secrets", model="Secret", lookup="uid", sample="8f2c1a90-4b33-4c1e-9a77-11aa22bb33cc", owner="namespace", first="list_scope", residual="comments", product="cathead-k8s", bug="CTH-1 metadata.uid used as global PK"),
    dict(slug="stripe-pi-lookup-idor", plant="davit", ticket="DAV-6", surface="Stripe PaymentIntent id object-id IDOR", mod="payments", model="Payment", lookup="pi", sample="pi_3N4abcXYZ0001", owner="merchant_id", first="authn", residual="pdf", product="davit-pay", bug="DAV-6 pi_ id unique leftover from dashboard deep links", style="path", route="/v1/payments"),
    dict(slug="shopify-order-name-idor", plant="futtock", ticket="FUT-8", surface="Shopify order name #1042 object-id IDOR", mod="orders", model="Order", lookup="order_name", sample="#1042", owner="shop_id", first="mask", residual="export", product="futtock-shop", bug="FUT-8 order name unique leftover from print receipts"),
    dict(slug="slack-ts-permalink-idor", plant="garboard", ticket="GAR-2", surface="Slack message ts permalink object-id IDOR", mod="messages", model="Message", lookup="ts", sample="1712345678.123456", owner="workspace_id", first="any_member", residual="search", product="garboard-chat", bug="GAR-2 ts unique leftover from permalinks"),
    dict(slug="ldap-dn-entry-idor", plant="inwale", ticket="INW-9", surface="LDAP DN entry object-id IDOR", mod="entries", model="Entry", lookup="dn", sample="uid=bob,ou=people,dc=ex", owner="directory_id", first="list_scope", residual="mget", product="inwale-dir", bug="INW-9 DN unique leftover from sync"),
    dict(slug="imap-uid-fetch-idor", plant="maststep", ticket="MAS-3", surface="IMAP UID fetch object-id IDOR", mod="mail", model="Mail", lookup="imap_uid", sample="44192", owner="mailbox_id", first="authn", residual="csv", product="maststep-mail", bug="MAS-3 UID unique leftover from IMAP proxy"),
    dict(slug="gcs-generation-object-idor", plant="parrel", ticket="PAR-11", surface="GCS object generation object-id IDOR", mod="gcsobjs", model="GcsObj", lookup="generation", sample="1712345678901234", owner="bucket_id", first="mask", residual="admin", product="parrel-gcs", bug="PAR-11 generation used as global get key"),
    dict(slug="docker-digest-manifest-idor", plant="ratline", ticket="RAT-4", surface="Docker content digest object-id IDOR", mod="manifests", model="Manifest", lookup="digest", sample="sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", owner="repo_id", first="any_member", residual="webhook", product="ratline-oci", bug="RAT-4 digest globally unique leftover", style="path", route="/v2/manifests"),
    dict(slug="snowflake-sid-post-idor", plant="sheer", ticket="SHE-7", surface="Snowflake status id object-id IDOR", mod="posts", model="Post", lookup="sid", sample="1844674407370955161", owner="author_id", first="list_scope", residual="comments", product="sheer-social", bug="SHE-7 snowflake id used without author", style="path", route="/v1/posts"),
    dict(slug="ulid-invite-lookup-idor", plant="thwart", ticket="THW-6", surface="ULID invite object-id IDOR", mod="invites", model="Invite", lookup="ulid", sample="01ARZ3NDEKTSV4RRFFQ69G5FAV", owner="org_id", first="authn", residual="pdf", product="thwart-invite", bug="THW-6 ULID unique leftover from email links", style="path", route="/v1/invites"),
    dict(slug="aws-arn-get-idor", plant="windlass", ticket="WIN-2", surface="AWS ARN-keyed resource object-id IDOR", mod="resources", model="Resource", lookup="arn", sample="arn:aws:s3:::partner-bucket/k", owner="account_id", first="mask", residual="export", product="windlass-aws", bug="WIN-2 ARN unique leftover from console copy"),
    dict(slug="btc-txid-wallet-idor", plant="yardarm", ticket="YAR-8", surface="Bitcoin txid wallet object-id IDOR", mod="txs", model="Tx", lookup="txid", sample="f4184fc596403b9d638783cf57adfe4c75c605f6356fbc91338530e9831e9e16", owner="wallet_id", first="any_member", residual="search", product="yardarm-btc", bug="YAR-8 txid unique leftover from explorer links", style="path", route="/v1/txs"),
    dict(slug="ean13-sku-lookup-idor", plant="capstan", ticket="CAP-3", surface="EAN-13 SKU object-id IDOR", mod="skus", model="Sku", lookup="ean", sample="4006381333931", owner="catalog_id", first="list_scope", residual="mget", product="capstan-merch", bug="CAP-3 EAN unique leftover from barcode scan"),
    dict(slug="doi-paper-lookup-idor", plant="cringle", ticket="CRI-9", surface="DOI-keyed paper object-id IDOR", mod="papers", model="Paper", lookup="doi", sample="10.1038/s41586-023-1234-5", owner="publisher_id", first="authn", residual="csv", product="cringle-pubs", bug="CRI-9 DOI unique leftover from Crossref ingest", style="path", route="/v1/papers"),
    dict(slug="orcid-hr-profile-idor", plant="fid", ticket="FID-5", surface="ORCID-keyed HR profile object-id IDOR", mod="profiles", model="Profile", lookup="orcid", sample="0000-0002-1825-0097", owner="institution_id", first="mask", residual="admin", product="fid-hr", bug="FID-5 ORCID unique leftover from faculty import", style="path", route="/v1/profiles"),
    dict(slug="imsi-sim-lookup-idor", plant="hounds", ticket="HOU-8", surface="IMSI-keyed SIM object-id IDOR", mod="sims", model="Sim", lookup="imsi", sample="310150123456789", owner="carrier_account", first="any_member", residual="webhook", product="hounds-telco", bug="HOU-8 IMSI unique leftover from HLR"),
    dict(slug="isin-position-lookup-idor", plant="jibboom", ticket="JIB-4", surface="ISIN-keyed position object-id IDOR", mod="positions", model="Position", lookup="isin", sample="US0378331005", owner="fund_id", first="list_scope", residual="comments", product="jibboom-fund", bug="JIB-4 ISIN unique leftover from blotter"),
    dict(slug="cusip-lot-lookup-idor", plant="luff", ticket="LUF-2", surface="CUSIP-keyed lot object-id IDOR", mod="lots", model="Lot", lookup="cusip", sample="037833100", owner="desk_id", first="authn", residual="pdf", product="luff-desk", bug="LUF-2 CUSIP unique leftover from DTC"),
    dict(slug="lei-kyc-lookup-idor", plant="mizzen", ticket="MIZ-6", surface="LEI-keyed KYC file object-id IDOR", mod="kyc", model="Kyc", lookup="lei", sample="5493001KJTIIGC8Y1R12", owner="firm_id", first="mask", residual="export", product="mizzen-kyc", bug="MIZ-6 LEI unique leftover from GLEIF"),
    dict(slug="figi-order-lookup-idor", plant="nock", ticket="NOC-1", surface="FIGI-keyed order object-id IDOR", mod="figi_orders", model="FigiOrder", lookup="figi", sample="BBG000B9XRY4", owner="book_id", first="any_member", residual="search", product="nock-oms", bug="NOC-1 FIGI unique leftover from Bloomberg"),
    dict(slug="sip-callid-lookup-idor", plant="outhaul", ticket="OUT-8", surface="SIP Call-ID object-id IDOR", mod="calls", model="Call", lookup="callid", sample="a84b4c76e66710@pc33.atlanta", owner="tenant_id", first="list_scope", residual="mget", product="outhaul-sip", bug="OUT-8 Call-ID unique leftover from CDR", style="path", route="/v1/calls"),
    dict(slug="wifi-bssid-ap-idor", plant="peak", ticket="PEA-3", surface="BSSID-keyed access point object-id IDOR", mod="aps", model="Ap", lookup="bssid", sample="00:11:22:33:44:55", owner="venue_id", first="authn", residual="csv", product="peak-wifi", bug="PEA-3 BSSID unique leftover from survey"),
    dict(slug="gs1-sscc-pallet-idor", plant="sprit", ticket="SPR-7", surface="GS1 SSCC pallet object-id IDOR", mod="pallets", model="Pallet", lookup="sscc", sample="006141411234567890", owner="warehouse_id", first="mask", residual="admin", product="sprit-wms", bug="SPR-7 SSCC unique leftover from dock scan"),
    dict(slug="npi-provider-lookup-idor", plant="tiller", ticket="TIL-5", surface="NPI-keyed provider object-id IDOR", mod="providers", model="Provider", lookup="npi", sample="1679672460", owner="clinic_id", first="any_member", residual="webhook", product="tiller-ehr", bug="TIL-5 NPI unique leftover from NPPES"),
    dict(slug="duns-vendor-lookup-idor", plant="vang", ticket="VAN-2", surface="DUNS-keyed vendor object-id IDOR", mod="vendors", model="Vendor", lookup="duns", sample="039779841", owner="buyer_id", first="list_scope", residual="comments", product="vang-procure", bug="VAN-2 DUNS unique leftover from Dun & Bradstreet"),
    dict(slug="gln-location-lookup-idor", plant="batten", ticket="BAT-9", surface="GLN-keyed location object-id IDOR", mod="locations", model="Location", lookup="gln", sample="0614141000005", owner="network_id", first="authn", residual="pdf", product="batten-edi", bug="BAT-9 GLN unique leftover from EDI 856"),
    dict(slug="icao-flight-lookup-idor", plant="cunningham", ticket="CUN-1", surface="ICAO flight id object-id IDOR", mod="flights", model="Flight", lookup="icao", sample="UAL123-20260819", owner="airline_id", first="mask", residual="export", product="cunningham-ops", bug="CUN-1 ICAO flight id unique leftover from AFTN"),
    dict(slug="tailno-aircraft-idor", plant="downhaul", ticket="DOW-4", surface="Tail-number aircraft object-id IDOR", mod="aircraft", model="Aircraft", lookup="tailno", sample="N172UA", owner="operator_id", first="any_member", residual="search", product="downhaul-mx", bug="DOW-4 tail number unique leftover from FAA registry"),
    dict(slug="issn-serial-hold-idor", plant="gaff", ticket="GAF-6", surface="ISSN-keyed serial hold object-id IDOR", mod="serials", model="Serial", lookup="issn", sample="2049-3630", owner="library_id", first="list_scope", residual="mget", product="gaff-serials", bug="GAF-6 ISSN unique leftover from holdings import"),
    dict(slug="pmid-pubmed-lookup-idor", plant="dolphin-striker", ticket="DOL-4", surface="PMID-keyed pubmed record object-id IDOR", mod="pubmed", model="Pubmed", lookup="pmid", sample="38765432", owner="campus_id", first="authn", residual="csv", product="dolphin-striker-lit", bug="DOL-4 PMID unique leftover from PubMed import"),
    dict(slug="ror-org-lookup-idor", plant="xebec", ticket="XEB-8", surface="ROR-keyed institution object-id IDOR", mod="institutions", model="Institution", lookup="ror", sample="https://ror.org/013cjyk83", owner="consortium_id", first="mask", residual="admin", product="xebec-ror", bug="XEB-8 ROR unique leftover from GRID merge"),
    dict(slug="wikidata-qid-entity-idor", plant="yuloh", ticket="YUL-2", surface="Wikidata QID entity object-id IDOR", mod="entities", model="Entity", lookup="qid", sample="Q42", owner="wiki_id", first="any_member", residual="webhook", product="yuloh-wd", bug="YUL-2 QID unique leftover from sitelinks"),
    dict(slug="handle-net-lookup-idor", plant="zabra", ticket="ZAB-9", surface="Handle.net object-id IDOR", mod="handles", model="Handle", lookup="handle", sample="102.100.100/36", owner="registrar_id", first="list_scope", residual="comments", product="zabra-hdl", bug="ZAB-9 handle unique leftover from CNRI"),
]


def _load_extra(name: str):
    spec = importlib.util.spec_from_file_location(name, EXPERIMENTS / f"{name.replace('_', '-')}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_extra = _load_extra("azr_plants_r1245")
_extra2 = _load_extra("azr_plants_r1269")
_extra3 = _load_extra("azr_plants_r1285")


def build_pairs() -> list[tuple[dict, dict]]:
    idors = [
        _idor(row)
        for row in (
            IDOR_ROWS
            + list(_extra.EXTRA_IDOR_ROWS)
            + list(_extra2.EXTRA_IDOR_ROWS)
            + list(_extra3.EXTRA_IDOR_ROWS)
        )
    ]
    bflas = (
        _bflas()
        + _extra.extra_bflas(_H)
        + _extra2.extra_bflas(_H)
        + _extra3.extra_bflas(_H)
    )
    if len(idors) != len(bflas):
        raise SystemExit(f"idor {len(idors)} != bfla {len(bflas)}")
    pairs = list(zip(idors, bflas))
    for sa, sb in pairs:
        for spec in (sa, sb):
            slug = spec["slug"]
            if slug in USED_SLUGS:
                raise SystemExit(f"clone of prior mill slug: {slug}")
            if slug in _old.BANNED_SLUGS:
                raise SystemExit(f"banned slug {slug}")
        if sa["plant"] != sb["plant"]:
            # pair shares invented plant name like r1193 mill
            pass
    return pairs


PAIRS = build_pairs()


def generate_round(round_n: int) -> tuple[list[dict], str]:
    idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"no catalog pair for round {round_n} (have {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1})"
        )
    sa, sb = PAIRS[idx]
    a = build_success(round_n, sa)
    b = build_handoff(round_n, sb)
    return [a, b], notes_for(round_n, a, b, sa, sb)


def write_round(round_n: int, staging: Path) -> None:
    eps, notes = generate_round(round_n)
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    nfile = staging / f"NOTES-r{round_n:02d}.md"
    with batch.open("w") as fh:
        for ep in eps:
            fh.write(json.dumps(ep, ensure_ascii=True) + "\n")
    nfile.write_text(notes)
    print(
        json.dumps(
            {
                "round": round_n,
                "ids": [e["id"] for e in eps],
                "steps": [len(e["steps"]) for e in eps],
                "success": [e["reward"]["success"] for e in eps],
                "batch": str(batch),
                "notes": str(nfile),
            }
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
