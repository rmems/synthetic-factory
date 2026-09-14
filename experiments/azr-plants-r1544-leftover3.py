"""Unique leftover leftover leftover Cedar/OPA OpenFGA/SpiceDB Casbin/Oso pairs.

Not leftover mill cartesian. Not JWT-claim catalog. Not leftover leftover leftover search plants.
Not clones of r1415/r1445/r1506 cedar-tmpl / opa-partial / openfga-ttu / spicedb-caveat.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

EXTRA_IDOR_ROWS = [
    dict(slug="cedar-when-attr-idor", plant="halyard", ticket="HAL-1", surface="Cedar when-clause attribute object-id IDOR", mod="cedwhens", model="CedWhen", lookup="whenkey", sample="when:dept=eng", owner="policy_store", first="authn", residual="pdf", product="halyard-cedar-when", bug="HAL-1 Cedar when attr unique across policy stores"),
    dict(slug="openfga-listobjects-idor", plant="hawsepipe", ticket="HAW-2", surface="OpenFGA ListObjects object-id IDOR", mod="fgalists", model="FgaList", lookup="objtype", sample="note:77", owner="store_id", first="mask", residual="export", product="hawsepipe-fga-list", bug="HAW-2 ListObjects type unique across stores"),
    dict(slug="casbin-rbac-dom-idor", plant="heartsease", ticket="HEA-3", surface="Casbin RBAC-with-domains object-id IDOR", mod="casrbds", model="CasRbd", lookup="dompol", sample="p, alice, domain1, data1, read", owner="adapter_id", first="any_member", residual="search", product="heartsease-casbin-rbacd", bug="HEA-3 domain policy unique across adapters"),
    dict(slug="kc-resource-srv-idor", plant="heelblock", ticket="HEE-4", surface="Keycloak resource-server object-id IDOR", mod="kcrsvs", model="KcRsv", lookup="rsid", sample="rs-notes", owner="realm_id", first="list_scope", residual="mget", product="heelblock-kc-rs", bug="HEE-4 resource-server id unique across realms"),
    dict(slug="clerk-orgmem-idor", plant="helmsman", ticket="HEL-5", surface="Clerk org membership object-id IDOR", mod="clkmems", model="ClkMem", lookup="memid", sample="orgmem_2abc", owner="instance_id", first="authn", residual="csv", product="helmsman-clerk-mem", bug="HEL-5 org membership unique across instances"),
    dict(slug="fb-rtdb-path-idor", plant="hitchpin", ticket="HIT-6", surface="Firebase RTDB path object-id IDOR", mod="fbrtdbs", model="FbRtdb", lookup="rtdbpath", sample="/notes/n-9", owner="project_id", first="mask", residual="admin", product="hitchpin-fb-rtdb", bug="HIT-6 RTDB path unique across projects"),
    dict(slug="k8s-rolebind-idor", plant="hoistway", ticket="HOI-7", surface="Kubernetes RoleBinding object-id IDOR", mod="k8rbs", model="K8Rb", lookup="rbname", sample="note-editor", owner="namespace", first="any_member", residual="webhook", product="hoistway-k8s-rb", bug="HOI-7 RoleBinding name unique across namespaces"),
    dict(slug="grpc-md-auth-idor", plant="holdbeam", ticket="HOL-8", surface="gRPC metadata auth object-id IDOR", mod="grpcmds", model="GrpcMd", lookup="mdkey", sample="x-note-id:77", owner="service_id", first="list_scope", residual="comments", product="holdbeam-grpc-md", bug="HOL-8 metadata key unique across services"),
    dict(slug="cerbos-resource-idor", plant="hookblock", ticket="HOO-9", surface="Cerbos resource policy object-id IDOR", mod="cerress", model="CerRes", lookup="reskind", sample="note:v1", owner="policy_id", first="authn", residual="pdf", product="hookblock-cerbos-res", bug="HOO-9 resource kind unique across policy ids"),
    dict(slug="topaz-ds-idor", plant="horncleat", ticket="HOR-1", surface="Topaz directory object-id IDOR", mod="topazds", model="TopazDs", lookup="dsobj", sample="user:alice#member", owner="tenant_id", first="mask", residual="export", product="horncleat-topaz-ds", bug="HOR-1 directory object unique across tenants"),
    dict(slug="permit-pdp-idor", plant="horseshoe", ticket="HOS-2", surface="Permit.io PDP object-id IDOR", mod="pmtpds", model="PmtPdp", lookup="pdpkey", sample="note:read", owner="env_id", first="any_member", residual="search", product="horseshoe-permit-pdp", bug="HOS-2 PDP key unique across envs"),
    dict(slug="istio-authz-idor", plant="hounds", ticket="HOU-3", surface="Istio AuthorizationPolicy object-id IDOR", mod="istazs", model="IstAz", lookup="azname", sample="deny-notes-delete", owner="mesh_ns", first="list_scope", residual="mget", product="hounds-istio-az", bug="HOU-3 AuthorizationPolicy unique across mesh ns"),
    dict(slug="shiro-perm-idor", plant="hovea", ticket="HOV-4", surface="Apache Shiro permission object-id IDOR", mod="shirops", model="ShiroP", lookup="permstr", sample="note:delete:77", owner="realm_name", first="authn", residual="csv", product="hovea-shiro-perm", bug="HOV-4 permission string unique across realms"),
    dict(slug="pundit-scope-idor", plant="hove-to", ticket="HOV-5", surface="Pundit policy_scope object-id IDOR", mod="pundits", model="PunditS", lookup="scopekey", sample="NotePolicy::Scope", owner="app_id", first="mask", residual="admin", product="hoveto-pundit-scope", bug="HOV-5 policy_scope unique across apps"),
    dict(slug="guardian-obj-idor", plant="hugger", ticket="HUG-6", surface="django-guardian object perm IDOR", mod="guardos", model="GuardO", lookup="ctypepk", sample="notes.note:42", owner="site_id", first="any_member", residual="webhook", product="hugger-guardian-obj", bug="HUG-6 object perm unique across sites"),
    dict(slug="postgrest-rls-idor", plant="humpback", ticket="HUM-7", surface="PostgREST RLS role object-id IDOR", mod="pgrlss", model="PgRls", lookup="rolname", sample="notes_reader", owner="db_id", first="list_scope", residual="comments", product="humpback-pgrst-rls", bug="HUM-7 role name unique across dbs"),
]

BFLA_ROWS = [
    dict(slug="opa-bundle-skip-delete", plant="halyard", ticket="HAL-1", surface="OPA bundle delete missing allow", family="js_route", skip='allow { input.method == "GET" }', auth='allow { input.method == "GET"; input.user; data.bundle.rev }', leftover="put"),
    dict(slug="spicedb-watch-skip-delete", plant="hawsepipe", ticket="HAW-2", surface="SpiceDB Watch skip on delete", family="js_route", skip="def delete_note(nid): notes.del(nid)", auth="def get_note(nid, uid): spice.check(uid, 'view', nid)", leftover="patch"),
    dict(slug="oso-datafilter-skip-delete", plant="heartsease", ticket="HEA-3", surface="Oso data filtering skip delete", family="js_route", skip="def delete_note(nid): Note.delete(nid)", auth="def list_notes(actor): oso.authorized_query(actor, 'read', Note)", leftover="update"),
    dict(slug="auth0-rbac-skip-delete", plant="heelblock", ticket="HEE-4", surface="Auth0 RBAC skip on delete", family="js_route", skip="scope: []  # deleteNote unscoped", auth="scope: [read:notes] on GET", leftover="put"),
    dict(slug="sb-rpc-skip-delete", plant="helmsman", ticket="HEL-5", surface="Supabase RPC skip delete", family="sql", skip="revoke execute on function notes_del from authenticated;", auth="select on notes using (owner = auth.uid())", leftover="patch"),
    dict(slug="iam-res-skip-delete", plant="hitchpin", ticket="HIT-6", surface="AWS IAM resource skip delete", family="js_route", skip="Action: notes:Delete  Resource: '*'", auth="Action: notes:Get  Resource: arn:notes:${acct}:note/${nid}", leftover="update"),
    dict(slug="gql-resolver-skip-delete", plant="hoistway", ticket="HOI-7", surface="GraphQL resolver skip DeleteNote", family="js_route", skip="DeleteNote: (_, {id}) => notes.del(id)", auth="Note: (_, {id}, ctx) => ctx.authz.load(id)", leftover="put"),
    dict(slug="envoy-extauthz-skip-delete", plant="holdbeam", ticket="HOL-8", surface="Envoy ext_authz skip DELETE", family="js_route", skip="http_filters: [{name: envoy.filters.http.router}]", auth="ext_authz on GET /notes", leftover="patch"),
    dict(slug="cerbos-derived-skip-delete", plant="hookblock", ticket="HOO-9", surface="Cerbos derived-roles skip delete", family="js_route", skip="actions: ['delete']  effect: EFFECT_ALLOW  # no derived", auth="actions: ['view']  derivedRoles: ['owner']", leftover="update"),
    dict(slug="topaz-check-skip-delete", plant="horncleat", ticket="HOR-1", surface="Topaz check skip delete", family="js_route", skip="def delete_note(nid): notes.del(nid)", auth="topaz.check(user, 'can_view', 'note', nid)", leftover="put"),
    dict(slug="opal-pubsub-skip-delete", plant="horseshoe", ticket="HOS-2", surface="OPAL pubsub skip delete policy", family="js_route", skip="topics: [policy:read]", auth="topics: [policy:read]  fetch_all_data_from_provider", leftover="patch"),
    dict(slug="istio-deny-skip-delete", plant="hounds", ticket="HOU-3", surface="Istio deny-all skip DELETE", family="js_route", skip="action: ALLOW  to: [{operation: {methods: ['GET']}}]", auth="action: DENY  to: [{operation: {methods: ['DELETE']}}] missing", leftover="update"),
    dict(slug="shiro-ann-skip-delete", plant="hovea", ticket="HOV-4", surface="Shiro @RequiresPermissions skip delete", family="js_route", skip="@RequiresPermissions('note:read')  # delete unannotated", auth="@RequiresPermissions('note:read') on get", leftover="put"),
    dict(slug="pundit-skip-delete", plant="hove-to", ticket="HOV-5", surface="Pundit skip destroy?", family="js_route", skip="def destroy\n  @note.destroy\nend", auth="def show\n  authorize @note\nend", leftover="patch"),
    dict(slug="guardian-skip-delete", plant="hugger", ticket="HUG-6", surface="django-guardian skip delete perm", family="js_route", skip="def delete(request, pk): Note.objects.get(pk=pk).delete()", auth="@permission_required('notes.view_note')\ndef detail(request, pk):", leftover="update"),
    dict(slug="pgrst-skip-delete", plant="humpback", ticket="HUM-7", surface="PostgREST skip DELETE grant", family="sql", skip="grant delete on notes to anon;", auth="grant select on notes to authenticated;", leftover="put"),
]


def extra_bflas(H):
    p = Path(__file__).resolve().parent / "azr-plants-r1504.py"
    spec = importlib.util.spec_from_file_location("azr_plants_r1504_expand", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return [H(**mod._expand_bfla(row)) for row in BFLA_ROWS]
