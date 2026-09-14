"""Unique leftover leftover leftover authz plants (policy engines / IdP / IAM / RPC).

Not leftover mill cartesian. Not JWT-claim catalog. Not science-object × CMS twins.
Not r1364 geohash-cell-idor / channels-consumer-skip-delete.
"""
from __future__ import annotations

EXTRA_IDOR_ROWS = [
    dict(slug="cedar-policy-set-idor", plant="kedge", ticket="KED-1", surface="Cedar policy-set object-id IDOR", mod="cedars", model="CedarSet", lookup="pidset", sample="ps-a1b2", owner="tenant_id", first="authn", residual="pdf", product="kedge-cedar-aws", bug="KED-1 Cedar policySetId unique across tenants"),
    dict(slug="openfga-store-idor", plant="lanyard", ticket="LAN-2", surface="OpenFGA store object-id IDOR", mod="fgastores", model="FgaStore", lookup="storeid", sample="01HXYZ", owner="org_id", first="mask", residual="export", product="lanyard-openfga-store", bug="LAN-2 OpenFGA store id unique across orgs"),
    dict(slug="casbin-policy-idor", plant="marlin", ticket="MAR-3", surface="Casbin policy row object-id IDOR", mod="casbinps", model="CasbinP", lookup="ptype", sample="p-42", owner="domain_id", first="any_member", residual="search", product="marlin-casbin-p", bug="MAR-3 Casbin ptype id unique across domains"),
    dict(slug="keycloak-uma-idor", plant="nipper", ticket="NIP-4", surface="Keycloak UMA resource object-id IDOR", mod="umas", model="UmaRes", lookup="rsid", sample="uma-991", owner="realm_id", first="list_scope", residual="mget", product="nipper-keycloak-uma", bug="NIP-4 UMA _id unique across realms"),
    dict(slug="auth0-org-member-idor", plant="parrel", ticket="PAR-5", surface="Auth0 org member object-id IDOR", mod="a0mems", model="A0Mem", lookup="orgmem", sample="org_abc|auth0|u1", owner="tenant_id", first="authn", residual="csv", product="parrel-auth0-orgmem", bug="PAR-5 Auth0 org_member id unique across tenants"),
    dict(slug="clerk-org-idor", plant="ratline", ticket="RAT-6", surface="Clerk organization object-id IDOR", mod="clerkorgs", model="ClerkOrg", lookup="orgid", sample="org_2abc", owner="instance_id", first="mask", residual="admin", product="ratline-clerk-org", bug="RAT-6 Clerk org id unique across instances"),
    dict(slug="workos-dir-idor", plant="seizing", ticket="SEI-7", surface="WorkOS directory object-id IDOR", mod="wosdirs", model="WosDir", lookup="dirid", sample="directory_01H", owner="env_id", first="any_member", residual="webhook", product="seizing-workos-dir", bug="SEI-7 WorkOS directory id unique across envs"),
    dict(slug="supabase-rls-row-idor", plant="thimble", ticket="THI-8", surface="Supabase RLS row object-id IDOR", mod="sbrls", model="SbRow", lookup="rowid", sample="uuid-row-7", owner="project_id", first="list_scope", residual="comments", product="thimble-supabase-rls", bug="THI-8 postgrest row id unique when RLS using() omitted"),
    dict(slug="firebase-doc-idor", plant="truck", ticket="TRU-9", surface="Firebase Firestore doc object-id IDOR", mod="fsdocs", model="FsDoc", lookup="docpath", sample="notes/abc", owner="project_id", first="authn", residual="pdf", product="truck-firebase-rules", bug="TRU-9 Firestore path unique when rules get() skips request.auth.uid"),
    dict(slug="aws-iam-role-idor", plant="vang", ticket="VAN-1", surface="AWS IAM role object-id IDOR", mod="iamroles", model="IamRole", lookup="rolearn", sample="arn:aws:iam::111:role/r", owner="account_id", first="mask", residual="export", product="vang-aws-iam-role", bug="VAN-1 IAM role ARN unique across accounts in control plane"),
    dict(slug="gcp-iam-sa-idor", plant="wale", ticket="WAL-2", surface="GCP IAM service-account object-id IDOR", mod="gcpsas", model="GcpSa", lookup="saemail", sample="sa@p.iam.gserviceaccount.com", owner="project_id", first="any_member", residual="search", product="wale-gcp-iam-sa", bug="WAL-2 GCP SA email unique across projects"),
    dict(slug="azure-rbac-assign-idor", plant="xebec", ticket="XEB-3", surface="Azure RBAC assignment object-id IDOR", mod="azrbas", model="AzRbac", lookup="asid", sample="00000000-as", owner="sub_id", first="list_scope", residual="mget", product="xebec-azure-rbac", bug="XEB-3 roleAssignment id unique across subscriptions"),
    dict(slug="k8s-rbac-role-idor", plant="yardarm", ticket="YAR-4", surface="Kubernetes Role object-id IDOR", mod="k8roles", model="K8Role", lookup="rolens", sample="prod/job-runner", owner="cluster_id", first="authn", residual="csv", product="yardarm-k8s-rbac", bug="YAR-4 Role ns/name unique across clusters"),
    dict(slug="gql-field-auth-idor", plant="zulu", ticket="ZUL-5", surface="GraphQL field-auth object-id IDOR", mod="gqlfields", model="GqlNote", lookup="nodeid", sample="Tm90ZTox", owner="tenant_id", first="mask", residual="admin", product="zulu-gql-field-auth", bug="ZUL-5 node(id) unique when @auth on Query.note only"),
    dict(slug="grpc-interceptor-idor", plant="anker", ticket="ANK-6", surface="gRPC interceptor object-id IDOR", mod="grpcrpcs", model="GrpcNote", lookup="noteid", sample="n-88", owner="tenant_id", first="any_member", residual="webhook", product="anker-grpc-interceptor", bug="ANK-6 GetNote id unique when interceptor skips unary Get"),
    dict(slug="trpc-mw-idor", plant="bitt", ticket="BIT-7", surface="tRPC middleware object-id IDOR", mod="trpcs", model="TrpcNote", lookup="trpcid", sample="42", owner="workspace_id", first="list_scope", residual="comments", product="bitt-trpc-mw", bug="BIT-7 tRPC noteById unique when middleware not on query"),
]

BFLA_ROWS = [
    dict(slug="opa-rego-skip-delete", plant="kedge", ticket="KED-1", surface="OPA Rego delete missing allow rule", family="js_route", skip="allow { input.method == \"GET\" }", auth="allow { input.method == \"GET\"; input.user }", leftover="put"),
    dict(slug="spicedb-rel-skip-delete", plant="lanyard", ticket="LAN-2", surface="SpiceDB CheckPermission skip on delete", family="js_route", skip="def delete_note(nid): notes.del(nid)", auth="def get_note(nid, uid): spice.check(uid, 'view', nid)", leftover="patch"),
    dict(slug="oso-polar-skip-delete", plant="marlin", ticket="MAR-3", surface="Oso Polar delete missing allow", family="js_route", skip="allow(actor, \"read\", note) if note.owner = actor;", auth="allow(actor, \"read\", note) if note.owner = actor;", leftover="update"),
    dict(slug="ory-keto-skip-delete", plant="nipper", ticket="NIP-4", surface="ORY Keto check skip on delete", family="js_route", skip="router.delete('/notes/:id', (req,res) => notes.del(req.params.id))", auth="router.get('/notes/:id', keto.check('view'), getNote)", leftover="put"),
    dict(slug="okta-mgmt-skip-delete", plant="parrel", ticket="PAR-5", surface="Okta management delete missing scope", family="js_route", skip="DELETE /api/v1/users/{id}  # no okta.users.manage", auth="GET /api/v1/users/{id}  Authorization: SSWS", leftover="patch"),
    dict(slug="supertokens-skip-delete", plant="ratline", ticket="RAT-6", surface="SuperTokens session skip on delete", family="js_route", skip="app.delete('/notes/:id', (req,res) => notes.del(req.params.id))", auth="app.get('/notes/:id', verifySession(), getNote)", leftover="update"),
    dict(slug="stytch-session-skip-delete", plant="seizing", ticket="SEI-7", surface="Stytch session skip on delete", family="js_route", skip="if method=='DELETE': notes.del(id)", auth="if method=='GET': stytch.sessions.authenticate(token)", leftover="put"),
    dict(slug="hasura-perm-skip-delete", plant="thimble", ticket="THI-8", surface="Hasura delete permission leftover", family="sql", skip="delete_permissions: []", auth="select_permissions: [{role: user, filter: {owner_id: x-hasura-user-id}}]", leftover="patch"),
    dict(slug="appsync-auth-skip-delete", plant="truck", ticket="TRU-9", surface="AppSync delete missing @aws_cognito_user_pools", family="js_route", skip="deleteNote(id: ID!): Boolean", auth="getNote(id: ID!): Note @aws_cognito_user_pools", leftover="update"),
    dict(slug="iam-idc-skip-delete", plant="vang", ticket="VAN-1", surface="IAM Identity Center skip on delete", family="js_route", skip="ssoadmin.DeletePermissionSet unguarded", auth="ssoadmin.DescribePermissionSet + sts GetCallerIdentity", leftover="put"),
    dict(slug="gcp-iap-skip-delete", plant="wale", ticket="WAL-2", surface="GCP IAP skip on delete Cloud Run", family="js_route", skip="DELETE /notes/{id}  # --allow-unauthenticated", auth="GET /notes/{id}  IAP audience check", leftover="patch"),
    dict(slug="aad-app-skip-delete", plant="xebec", ticket="XEB-3", surface="Azure AD app role skip on delete", family="js_route", skip="[Authorize(Roles = \"\")] Delete(id)", auth="[Authorize] Get(id)", leftover="update"),
    dict(slug="kyverno-policy-skip-delete", plant="yardarm", ticket="YAR-4", surface="Kyverno validate skip on DELETE", family="js_route", skip="rules: [{match: {resources: {kinds: [Note], operations: [CREATE]}}}]", auth="admission GET Note requires authn", leftover="put"),
    dict(slug="hasura-col-skip-delete", plant="zulu", ticket="ZUL-5", surface="Hasura column preset skip on delete", family="sql", skip="delete: {filter: {}}", auth="select: {filter: {tenant_id: x-hasura-tenant-id}}", leftover="patch"),
    dict(slug="connectrpc-skip-delete", plant="anker", ticket="ANK-6", surface="Connect-RPC interceptor skip on Delete", family="js_route", skip="DeleteNote unintercepted", auth="GetNote wrapped by auth interceptor", leftover="update"),
    dict(slug="tsrest-skip-delete", plant="bitt", ticket="BIT-7", surface="ts-rest delete missing middleware", family="js_route", skip="deleteNote: { handler: ({params}) => db.del(params.id) }", auth="getNote: { middleware: [auth], handler: get }", leftover="put"),
]


def extra_bflas(H):
    import importlib.util
    from pathlib import Path

    p = Path(__file__).resolve().parent / "azr-plants-r1365.py"
    spec = importlib.util.spec_from_file_location("azr_plants_r1365_expand", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return [H(**mod._expand_bfla(row)) for row in BFLA_ROWS]
