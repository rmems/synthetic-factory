"""Unique leftover leftover leftover policy-engine / IdP / IAM / RPC pairs.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1505 vesselNNNN-sys.
Not clones of r1415 cedar-policy-set / opa-rego / openfga-store / spicedb-rel.
Not clones of r1445 casbin-policy / oso-polar / keycloak-uma.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

EXTRA_IDOR_ROWS = [
    dict(slug="cedar-tmpl-link-idor", plant="aftpeak", ticket="AFT-1", surface="Cedar template-linked policy object-id IDOR", mod="cedtmpls", model="CedTmpl", lookup="tmplink", sample="tl-cedar-9", owner="tenant_id", first="authn", residual="pdf", product="aftpeak-cedar-tmpl", bug="AFT-1 Cedar templateLinkId unique across tenants"),
    dict(slug="openfga-ttu-idor", plant="backstay", ticket="BAC-2", surface="OpenFGA tuple-to-userset object-id IDOR", mod="fgattus", model="FgaTtu", lookup="ttukey", sample="doc:42#parent", owner="store_id", first="mask", residual="export", product="backstay-openfga-ttu", bug="BAC-2 OpenFGA TTU key unique across stores"),
    dict(slug="casbin-g2-idor", plant="bobstay", ticket="BOB-3", surface="Casbin g2 grouping object-id IDOR", mod="casg2s", model="CasG2", lookup="g2row", sample="g2-dom-7", owner="domain_id", first="any_member", residual="search", product="bobstay-casbin-g2", bug="BOB-3 Casbin g2 row unique across domains"),
    dict(slug="keycloak-cscope-idor", plant="breast", ticket="BRE-4", surface="Keycloak client-scope object-id IDOR", mod="kcsps", model="KcScope", lookup="csid", sample="cs-profile", owner="realm_id", first="list_scope", residual="mget", product="breast-kc-cscope", bug="BRE-4 client-scope id unique across realms"),
    dict(slug="auth0-fga-tuple-idor", plant="bullseye", ticket="BUL-5", surface="Auth0 FGA tuple object-id IDOR", mod="a0fgas", model="A0Fga", lookup="tuplekey", sample="note:9#owner@user:u", owner="tenant_id", first="authn", residual="csv", product="bullseye-auth0-fga", bug="BUL-5 Auth0 FGA tuple unique across tenants"),
    dict(slug="clerk-orgrole-idor", plant="catharpin", ticket="CAT-6", surface="Clerk org role object-id IDOR", mod="clkroles", model="ClkRole", lookup="rolekey", sample="org:admin", owner="instance_id", first="mask", residual="admin", product="catharpin-clerk-role", bug="CAT-6 Clerk org role unique across instances"),
    dict(slug="sb-rls-policy-idor", plant="clewline", ticket="CLE-7", surface="Supabase RLS policy oid object-id IDOR", mod="sbrlps", model="SbRlp", lookup="poloid", sample="16422", owner="project_id", first="any_member", residual="webhook", product="clewline-sb-rlspol", bug="CLE-7 pg_policy oid unique across projects"),
    dict(slug="iam-policy-ver-idor", plant="cringle", ticket="CRI-8", surface="AWS IAM policy version object-id IDOR", mod="iamvers", model="IamVer", lookup="polver", sample="arn:aws:iam::1:policy/p:v3", owner="account_id", first="list_scope", residual="comments", product="cringle-iam-ver", bug="CRI-8 IAM policy version unique across accounts"),
    dict(slug="k8s-clusterrole-idor", plant="crosstree", ticket="CRO-9", surface="Kubernetes ClusterRole object-id IDOR", mod="k8crs", model="K8Cr", lookup="crname", sample="job-admin", owner="cluster_id", first="authn", residual="pdf", product="crosstree-k8s-cr", bug="CRO-9 ClusterRole name unique across clusters"),
    dict(slug="gql-dir-auth-idor", plant="deadeye", ticket="DEA-1", surface="GraphQL @auth directive object-id IDOR", mod="gqldirs", model="GqlDir", lookup="fieldid", sample="Mutation.deleteNote", owner="schema_id", first="mask", residual="export", product="deadeye-gql-dir", bug="DEA-1 field unique when @auth on Query only"),
    dict(slug="cedar-entityuid-idor", plant="dolphin", ticket="DOL-2", surface="Cedar EntityUid object-id IDOR", mod="cedent", model="CedEnt", lookup="euid", sample='Note::"n-77"', owner="policy_store", first="any_member", residual="search", product="dolphin-cedar-euid", bug="DOL-2 Cedar EntityUid unique across policy stores"),
    dict(slug="openfga-cond-idor", plant="fairlead", ticket="FAI-3", surface="OpenFGA condition object-id IDOR", mod="fgaconds", model="FgaCond", lookup="condname", sample="in_office_hours", owner="store_id", first="list_scope", residual="mget", product="fairlead-fga-cond", bug="FAI-3 condition name unique across stores"),
    dict(slug="casbin-dom-rbac-idor", plant="fid", ticket="FID-4", surface="Casbin domain RBAC object-id IDOR", mod="casdoms", model="CasDom", lookup="domkey", sample="dom:acme:p", owner="adapter_id", first="authn", residual="csv", product="fid-casbin-dom", bug="FID-4 domain policy unique across adapters"),
    dict(slug="kc-authz-scope-idor", plant="fishplate", ticket="FIS-5", surface="Keycloak authz scope object-id IDOR", mod="kcazs", model="KcAzs", lookup="azsid", sample="scope:note:delete", owner="realm_id", first="mask", residual="admin", product="fishplate-kc-azs", bug="FIS-5 authz scope unique across realms"),
    dict(slug="clerk-sat-idor", plant="footrope", ticket="FOO-6", surface="Clerk session token object-id IDOR", mod="clksats", model="ClkSat", lookup="sid", sample="sess_2xyz", owner="instance_id", first="any_member", residual="webhook", product="footrope-clerk-sat", bug="FOO-6 Clerk session id unique across instances"),
    dict(slug="fb-custom-claim-idor", plant="gammon", ticket="GAM-7", surface="Firebase custom-claim uid object-id IDOR", mod="fbclaims", model="FbClaim", lookup="uid", sample="uid-aa11", owner="project_id", first="list_scope", residual="comments", product="gammon-fb-claim", bug="GAM-7 custom-claim uid unique across projects"),
]

BFLA_ROWS = [
    dict(slug="opa-partial-skip-delete", plant="aftpeak", ticket="AFT-1", surface="OPA partial-eval delete missing allow", family="js_route", skip='allow { input.method == "GET" }', auth='allow { input.method == "GET"; input.user }', leftover="put"),
    dict(slug="spicedb-caveat-skip-delete", plant="backstay", ticket="BAC-2", surface="SpiceDB caveat skip on delete", family="js_route", skip="def delete_note(nid): notes.del(nid)", auth="def get_note(nid, uid): spice.check(uid, 'view', nid, caveat='ip')", leftover="patch"),
    dict(slug="oso-filter-skip-delete", plant="bobstay", ticket="BOB-3", surface="Oso authorized_resources skip delete", family="js_route", skip="def delete_note(nid): Note.delete(nid)", auth="def list_notes(actor): oso.authorized_resources(actor, 'read', Note)", leftover="update"),
    dict(slug="oathkeeper-skip-delete", plant="breast", ticket="BRE-4", surface="ORY Oathkeeper delete missing authorizer", family="js_route", skip="id: notes-delete\nmatch: {url: /notes/<id>, methods: [DELETE]}\nauthorizer: allow", auth="id: notes-get\nmatch: {methods: [GET]}\nauthorizer: keto", leftover="put"),
    dict(slug="okta-iga-skip-delete", plant="bullseye", ticket="BUL-5", surface="Okta IGA skip on delete entitlement", family="js_route", skip="DELETE /iga/entitlements/{id}  # no okta.iga.manage", auth="GET /iga/entitlements/{id}  SSWS + scope", leftover="patch"),
    dict(slug="stytch-rbac-skip-delete", plant="catharpin", ticket="CAT-6", surface="Stytch RBAC skip on delete", family="js_route", skip="if method=='DELETE': notes.del(id)", auth="if method=='GET': stytch.rbac.authorize(session, 'note.read')", leftover="update"),
    dict(slug="fb-storage-skip-delete", plant="clewline", ticket="CLE-7", surface="Firebase Storage rules skip delete", family="js_route", skip="match /notes/{id} { allow delete: if true; }", auth="match /notes/{id} { allow get: if request.auth.uid == resource.data.owner; }", leftover="put"),
    dict(slug="gcp-iam-cond-skip-delete", plant="cringle", ticket="CRI-8", surface="GCP IAM condition skip on delete", family="js_route", skip="roles/notes.deleter  # no condition", auth='roles/notes.viewer  condition: resource.name.startsWith("projects/"+proj)', leftover="patch"),
    dict(slug="cilium-cnp-skip-delete", plant="crosstree", ticket="CRO-9", surface="CiliumNetworkPolicy skip DELETE", family="js_route", skip="egress: [{toPorts: [{ports: [{port: '80'}]}]}]  # no DELETE deny", auth="ingress: [{fromEndpoints: [{matchLabels: {auth: 'required'}}]}]", leftover="update"),
    dict(slug="grpc-authz-skip-delete", plant="deadeye", ticket="DEA-1", surface="gRPC authz interceptor skip Delete", family="js_route", skip="rpc DeleteNote(Id) returns (Empty) {}  # no interceptor", auth="rpc GetNote(Id) returns (Note) { option (authz.required) = true; }", leftover="put"),
    dict(slug="opa-httpsend-skip-delete", plant="dolphin", ticket="DOL-2", surface="OPA http.send allow skip delete", family="js_route", skip='allow { input.action == "read" }', auth='allow { http.send({"url": data.idp}).body.sub == input.user }', leftover="patch"),
    dict(slug="spicedb-lookup-skip-delete", plant="fairlead", ticket="FAI-3", surface="SpiceDB LookupResources skip delete", family="js_route", skip="def delete_note(nid): notes.del(nid)", auth="def list_notes(uid): spice.lookup('note', 'view', uid)", leftover="update"),
    dict(slug="oso-block-skip-delete", plant="fid", ticket="FID-4", surface="Oso resource block skip delete", family="js_route", skip='resource Note { permissions = ["read"]; }', auth='resource Note { permissions = ["read"]; "read" if owner; }', leftover="put"),
    dict(slug="auth0-apiperm-skip-delete", plant="fishplate", ticket="FIS-5", surface="Auth0 API permission skip delete", family="js_route", skip="scope: []  # deleteNote unscoped", auth="scope: [read:notes] on GET", leftover="patch"),
    dict(slug="sb-vault-skip-delete", plant="footrope", ticket="FOO-6", surface="Supabase vault secret skip delete", family="sql", skip="revoke delete on vault.secrets from authenticated;", auth="select on vault.secrets using (owner = auth.uid())", leftover="update"),
    dict(slug="aws-sso-permset-skip-delete", plant="gammon", ticket="GAM-7", surface="IAM Identity Center permset skip delete", family="js_route", skip="ssoadmin.DeletePermissionSet unguarded", auth="ssoadmin.DescribePermissionSet + GetCallerIdentity", leftover="put"),
]


def extra_bflas(H):
    p = Path(__file__).resolve().parent / "azr-plants-r1504.py"
    spec = importlib.util.spec_from_file_location("azr_plants_r1504_expand", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return [H(**mod._expand_bfla(row)) for row in BFLA_ROWS]
