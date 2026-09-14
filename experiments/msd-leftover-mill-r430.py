#!/usr/bin/env python3
"""MCP leftover mill r430+: unique protocol leftover, not r404–r429 seven-family rotation.

BAN {id} wrap, ping-split, X-Vendor→Bearer, add/delete splits, URI prefix.
BAN r317–r364 nextCursor/includeContext clones.
BAN r365–r396 icon/session/protocol-header/oauth-resource/toolChoice clones.
BAN leftover completions/logging/elicitation/subscribe/progress/roots/modelPreferences.
BAN cloning r404–r429 families: task-cancel, sse-resume, oauth-authmethod,
related-task, jsonrpc-notify, dcr-redirect, tasks-list.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

FACTORY = "mcp-tool-schema-drift-factory"
GEN = "grok-4.6"
REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "outputs" / "raw" / "2026-08-19-agentic" / FACTORY

BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")

# Families this mill may rotate — none of the r404–r429 seven.
OWN_FAMILIES = (
    "http-202-notify",
    "get-405-sse",
    "rfc9728-prm-path",
    "oauth-par",
    "insufficient-scope",
    "sampling-model",
    "content-block",
    "inputschema-type",
    "iserror-result",
    "res-updated-uri",
    "embedded-resource-type",
    "unary-post-json",
    "oauth-state",
    "prompts-name",
    "stopreason-required",
    "sse-event-message",
    "call-args-object",
    "reslist-name",
    "method-slash",
    "serverinfo-version",
    "get-accept-406",
    "expires-in-number",
    "initialized-required",
    "image-mimetype",
    "sampling-role",
    "pkce-verifier",
    "init-first",
    "content-array",
    "post-json-ctype",
    "messages-minitems",
    "cap-tools-object",
    "tool-name-string",
    "sse-comment-keepalive",
    "response-id-match",
    "clientinfo-version",
    "blob-base64",
    "parse-error-32700",
    "unknown-tool-32602",
    "sse-data-oneline",
    "init-http-200-json",
    "unary-content-length",
    "post-accept-json",
    "image-data-base64",
    "iserror-boolean",
    "contents-array-minone",
    "prompt-content-block",
    "jsonrpc-id-not-float",
    "sse-no-charset",
    "outputschema-type-object",
    "stdio-vs-streamable",
    "sample-text-type",
    "ws-vs-streamable",
    "jsonrpc-id-not-bool",
    "sse-crlf",
    "utf8-no-bom",
    "content-encoding-identity",
    "resourcelink-type",
    "audio-data-base64",
    "method-no-ws",
    "request-no-result",
)

# Concurrent r430–r466 rotated renamed-tool / extra-required / tighter-enum /
# cursor-type / auth-scheme / method-split. Skip leftover that clones those.
NEAR_SKIP = {
    "prompts-list-name-required",
    "sample-stopreason-required",
    "sse-event-name-must-be-message",
    "call-arguments-object-not-array",
    "jsonrpc-method-slash-not-dot",
    "initialized-notification-required",
    "oauth-pkce-verifier-on-token",
    "sampling-messages-minitems-one",
    "init-cap-tools-object-not-bool",
    "tool-name-string-not-index",
    "oauth-par-rfc9126-request-uri",
    "oauth-authorize-state-required",
    "www-auth-insufficient-scope",
    "oauth-token-expires-in-number",
    "initialize-must-be-first",
    "sampling-role-human-to-user",
    "initialize-serverinfo-version-required",
    "initialize-clientinfo-version-required",
    "reslist-name-required",
    "res-updated-params-uri-required",
    "sample-result-model-required",
    "image-content-mimetype-required",
}


def clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def rec_id(round_n: int, slug: str) -> str:
    digest = hashlib.sha256(f"msd|{round_n}|{slug}|{GEN}".encode()).hexdigest()[:4]
    return f"msd-r{round_n}-{slug}-{digest}"


def P(
    *,
    slug: str,
    repo: str,
    method: str,
    leftover: str,
    spec: str,
    keep: str,
    deadend: str,
    extra: str,
    freeze_still: str,
    not_r: str,
    adapt_cmd: str,
    canon: str,
    pfx: str,
    grep: str,
    ticket: str,
    family: str,
    schema_note: str,
) -> dict:
    if family not in OWN_FAMILIES:
        raise SystemExit(f"unknown family {family} for {slug}")
    return {
        "slug": slug,
        "repo": repo,
        "method": method,
        "leftover": leftover,
        "spec": spec,
        "keep": keep,
        "deadend": deadend,
        "extra": extra,
        "freeze_still": freeze_still,
        "not_r": not_r,
        "adapt_cmd": adapt_cmd,
        "canon": canon,
        "pfx": pfx,
        "grep": grep,
        "ticket": ticket,
        "family": family,
        "schema_note": schema_note,
    }


# 18 pairs = 36 unique leftover surfaces for r430–r447.
PAIRS: list[tuple[dict, dict]] = [
    (
        P(
            slug="http-notify-202-empty-body",
            repo="repo-mcp",
            method="notifications/initialized",
            leftover="JSON-RPC notification POST 200 with empty JSON object {}",
            spec="202 Accepted with empty body and no JSON-RPC response",
            keep="JSON-RPC method string",
            deadend="return 204 No Content",
            extra="Retry-After",
            freeze_still="POST notifications/initialized 200 {} leftover",
            not_r="r388 jsonrpc-post-not-get / r406 initialized-notification-must-omit-id / r409 jsonrpc-batch-array-rejected",
            adapt_cmd="Return 202 with empty body for notifications",
            canon="CanonH2n",
            pfx="h2n",
            grep="202 Accepted|notifications/initialized",
            ticket="CT-H2N-760",
            family="http-202-notify",
            schema_note="# Streamable HTTP notifications use 202 and no JSON-RPC response object",
        ),
        P(
            slug="get-mcp-405-when-sse-unsupported",
            repo="llm-mcp",
            method="GET /mcp",
            leftover="GET /mcp 404 when the server does not advertise SSE listen",
            spec="405 Method Not Allowed with Allow: POST",
            keep="POST /mcp JSON-RPC",
            deadend="return 501 Not Implemented",
            extra="Allow-GET",
            freeze_still="GET /mcp 404 leftover when SSE is off",
            not_r="r377 get-sse-requires-session-header / r370 accept-json-plus-event-stream / r429 get-sse-cache-control-no-store",
            adapt_cmd="Return 405 + Allow POST when SSE listen is unsupported",
            canon="CanonG405",
            pfx="g405",
            grep="405 Method Not Allowed|Allow: POST",
            ticket="CT-G45-761",
            family="get-405-sse",
            schema_note="# GET is only for SSE listen; unsupported GET is 405 not 404",
        ),
    ),
    (
        P(
            slug="prm-rfc9728-path-insertion",
            repo="host-mcp",
            method="initialize",
            leftover="always GET /.well-known/oauth-protected-resource at the origin",
            spec="RFC 9728 path insertion /.well-known/oauth-protected-resource/{path}",
            keep="resource identifier absolute https",
            deadend="append ?resource= as a query leftover on the origin well-known",
            extra="service_documentation",
            freeze_still="GET origin /.well-known/oauth-protected-resource leftover",
            not_r="r371 www-authenticate-resource-metadata / r388 oauth-resource-param-absolute-https / r367 oauth-audience-to-resource-param",
            adapt_cmd="Insert the resource path into the well-known URL per RFC 9728",
            canon="CanonP972",
            pfx="p972",
            grep="oauth-protected-resource|rfc9728",
            ticket="CT-P72-762",
            family="rfc9728-prm-path",
            schema_note="# RFC 9728 inserts the resource path after oauth-protected-resource/",
        ),
        P(
            slug="oauth-par-rfc9126-request-uri",
            repo="edge-mcp",
            method="initialize",
            leftover="authorization request as GET query-string leftover on /authorize",
            spec="RFC 9126 PAR POST then authorize?request_uri=",
            keep="client_id",
            deadend="PUT the PAR body onto the authorize redirect leftover",
            extra="request_uri_expires_in",
            freeze_still="GET /authorize?client_id leftover instead of request_uri",
            not_r="r429 oauth-authorization-details-rfc9396 / r97 pkce-plain-to-s256 / r405 dcr-token-auth-method-none-public",
            adapt_cmd="Push PAR then redirect with request_uri; keep client_id",
            canon="CanonPar",
            pfx="opar",
            grep="request_uri|rfc9126|pushed_authorization_request",
            ticket="CT-PAR-763",
            family="oauth-par",
            schema_note="# RFC 9126 PAR: POST /par then authorize with request_uri, not a fat query string",
        ),
    ),
    (
        P(
            slug="www-auth-insufficient-scope",
            repo="mesh-mcp",
            method="initialize",
            leftover="401 WWW-Authenticate error=invalid_token when scopes are missing",
            spec="error=insufficient_scope with a scope attribute",
            keep="resource_metadata",
            deadend="error=invalid_request leftover",
            extra="realm",
            freeze_still="WWW-Authenticate error=invalid_token leftover for missing scope",
            not_r="r371 www-authenticate-resource-metadata / r408 prm-bearer-methods-supported-header / r378 oauth-scope-mcp-to-resource-scopes",
            adapt_cmd="Emit insufficient_scope plus scope=; keep resource_metadata",
            canon="CanonIsc",
            pfx="isc",
            grep="insufficient_scope|WWW-Authenticate",
            ticket="CT-ISC-764",
            family="insufficient-scope",
            schema_note="# RFC 6750: missing scope is insufficient_scope, not invalid_token",
        ),
        P(
            slug="sample-result-model-required",
            repo="forge-mcp",
            method="sampling/createMessage",
            leftover="CreateMessageResult omits model leftover",
            spec="result.model required string",
            keep="role and content",
            deadend="put model under _meta leftover",
            extra="usage",
            freeze_still="sampling/createMessage result without model leftover",
            not_r="r366 sample-tools-and-toolchoice / r21 sample-maxtokens-default / r400 sampling-includecontext-vs-thisserver",
            adapt_cmd="Require model on CreateMessageResult; keep role and content",
            canon="CanonSmod",
            pfx="smod",
            grep="CreateMessageResult|result.model",
            ticket="CT-SMD-765",
            family="sampling-model",
            schema_note="# sampling/createMessage result.model identifies the model that produced the message",
        ),
    ),
    (
        P(
            slug="sample-message-content-block",
            repo="kiln-mcp",
            method="sampling/createMessage",
            leftover="messages[].content leftover as a raw string",
            spec="ContentBlock object {type,text} or ContentBlock array",
            keep="role user|assistant",
            deadend="wrap the string as {message: str} leftover",
            extra="name",
            freeze_still="messages[].content as a raw string leftover",
            not_r="r377 sample-tool-use-content-type / r402 audio-content-vs-blob / r384 sample-tool-result-content-type",
            adapt_cmd="Map string leftover to {type:text,text}; keep role",
            canon="CanonCblk",
            pfx="cblk",
            grep="ContentBlock|messages.*content",
            ticket="CT-CBLK-766",
            family="content-block",
            schema_note="# SamplingMessage.content is a ContentBlock or array of ContentBlocks, not a bare string",
        ),
        P(
            slug="tools-inputschema-type-object",
            repo="quay-mcp",
            method="tools/list",
            leftover="inputSchema leftover as a properties map without type",
            spec="inputSchema.type must be object",
            keep="properties",
            deadend='type leftover "json"',
            extra="$comment",
            freeze_still="tools/list inputSchema properties-only leftover",
            not_r="r373 sample-tools-inputschema-required / r57 outputschema-dollar-schema / r345 call-outputschema-additionalproperties-false",
            adapt_cmd="Set inputSchema.type to object; keep properties",
            canon="CanonIst",
            pfx="istp",
            grep="inputSchema|type.*object",
            ticket="CT-IST-767",
            family="inputschema-type",
            schema_note="# Tool.inputSchema is a JSON Schema whose root type must be object",
        ),
    ),
    (
        P(
            slug="call-iserror-true-not-rpc-error",
            repo="span-mcp",
            method="tools/call",
            leftover="tool failure leftover as JSON-RPC -32603",
            spec="JSON-RPC result with isError true and content",
            keep="content array",
            deadend="HTTP 500 leftover",
            extra="isErrorMessage",
            freeze_still="tools/call tool failures as -32603 leftover",
            not_r="r38 call-iserror-object / r351 call-structuredcontent-xor-iserror / r397 tool-call-structuredcontent-vs-text",
            adapt_cmd="Return result.isError true; keep content; do not use -32603 for tool errors",
            canon="CanonIerr",
            pfx="ierr",
            grep="isError|CallToolResult",
            ticket="CT-IER-768",
            family="iserror-result",
            schema_note="# Tool errors are protocol-success with isError:true, not JSON-RPC -32603",
        ),
        P(
            slug="res-updated-params-uri-required",
            repo="dock-mcp",
            method="notifications/resources/updated",
            leftover="notifications/resources/updated leftover with empty params",
            spec="params.uri required",
            keep="notification omits id",
            deadend="params.resourceId leftover",
            extra="title",
            freeze_still="notifications/resources/updated {} leftover",
            not_r="r20 res-updated-mimetype / r50 res-updated-etag-obj / r400 resource-subscribe-uri-vs-cap",
            adapt_cmd="Require params.uri on resources/updated; keep omitting JSON-RPC id",
            canon="CanonRuri",
            pfx="ruri",
            grep="resources/updated|params.uri",
            ticket="CT-RUR-769",
            family="res-updated-uri",
            schema_note="# notifications/resources/updated params.uri is the resource that changed",
        ),
    ),
    (
        P(
            slug="content-type-embedded-to-resource",
            repo="yard-mcp",
            method="tools/call",
            leftover='content type leftover "embedded" or "embedded_resource"',
            spec='type "resource" for EmbeddedResource',
            keep="resource.uri",
            deadend='type leftover "resource_link"',
            extra="annotations",
            freeze_still='content type "embedded" leftover',
            not_r="r402 resource-link-type-vs-uri / r11 resource-link-type / r336 call-resourcelink-name-required",
            adapt_cmd="Map embedded leftover to type resource; keep resource.uri",
            canon="CanonEmb",
            pfx="embd",
            grep="EmbeddedResource|type.: .resource",
            ticket="CT-EMB-770",
            family="embedded-resource-type",
            schema_note="# EmbeddedResource uses type: resource; ResourceLink uses type: resource_link",
        ),
        P(
            slug="post-unary-json-not-sse",
            repo="pier-mcp",
            method="POST /mcp",
            leftover="POST /mcp leftover always text/event-stream even for unary requests",
            spec="application/json when Accept includes both and the request is unary",
            keep="Accept application/json and text/event-stream",
            deadend="multipart/mixed leftover",
            extra="X-Accel-Buffering",
            freeze_still="POST unary leftover always text/event-stream",
            not_r="r370 accept-json-plus-event-stream / r388 jsonrpc-post-not-get / r429 get-sse-cache-control-no-store",
            adapt_cmd="Respond JSON for unary POST when Accept includes JSON; keep SSE for streamed",
            canon="CanonUjs",
            pfx="ujsn",
            grep="application/json|text/event-stream|unary",
            ticket="CT-UJS-771",
            family="unary-post-json",
            schema_note="# Streamable HTTP unary POST may be JSON when Accept lists application/json",
        ),
    ),
    (
        P(
            slug="oauth-authorize-state-required",
            repo="reef-mcp",
            method="initialize",
            leftover="authorization request leftover omits state",
            spec="state CSRF parameter required",
            keep="code_challenge S256",
            deadend="nonce leftover instead of state",
            extra="login_hint",
            freeze_still="authorize without state leftover",
            not_r="r97 pkce-plain-to-s256 / r429 oauth-authorization-details-rfc9396 / r405 dcr-token-auth-method-none-public",
            adapt_cmd="Require state on authorize; keep PKCE S256",
            canon="CanonOst",
            pfx="ostt",
            grep="authorize.*state|csrf",
            ticket="CT-OST-772",
            family="oauth-state",
            schema_note="# OAuth authorize must carry an unguessable state CSRF parameter",
        ),
        P(
            slug="prompts-list-name-required",
            repo="cask-mcp",
            method="prompts/list",
            leftover="prompts/list leftover entries with title only",
            spec="name required identifier; title is display",
            keep="title optional",
            deadend="copy description leftover into name",
            extra="description",
            freeze_still="prompts/list title-only leftover",
            not_r="r10 tool-title-vs-name / r391 sample-tools-title-vs-name / r375 promptslist-icon-to-icons-array",
            adapt_cmd="Require name on prompts/list; keep title as display",
            canon="CanonPnm",
            pfx="pnam",
            grep="prompts/list|Prompt.name",
            ticket="CT-PNM-773",
            family="prompts-name",
            schema_note="# Prompt.name is the identifier; title is a human label",
        ),
    ),
    (
        P(
            slug="sample-stopreason-required",
            repo="loom-mcp",
            method="sampling/createMessage",
            leftover="CreateMessageResult leftover omits stopReason",
            spec="stopReason required enum endTurn|stopSequence|maxTokens",
            keep="model and content",
            deadend="stopReason leftover integer 0",
            extra="usage",
            freeze_still="CreateMessageResult without stopReason leftover",
            not_r="r19 stop-reason-enum / r109 stopreason-drop-length / r140 stopreason-drop-tooluse / r366 sample-tools-and-toolchoice",
            adapt_cmd="Require stopReason enum; keep model",
            canon="CanonSsr",
            pfx="ssrn",
            grep="stopReason|endTurn",
            ticket="CT-SSR-774",
            family="stopreason-required",
            schema_note="# CreateMessageResult.stopReason is required and is an enum, not an int",
        ),
        P(
            slug="sse-event-name-must-be-message",
            repo="tide-mcp",
            method="GET /mcp SSE",
            leftover="SSE leftover unnamed data-only events",
            spec="event: message before each data JSON line",
            keep="data JSON line",
            deadend="event leftover mcp",
            extra="retry",
            freeze_still="SSE unnamed data-only leftover",
            not_r="r404 sse-last-event-id-required-on-reconnect / r396 sse-id-is-event-id-not-session / r422 sse-retry-field-integer-ms",
            adapt_cmd="Name SSE events message; keep data JSON; do not rename to mcp",
            canon="CanonEvm",
            pfx="evmg",
            grep="event: message|text/event-stream",
            ticket="CT-EVM-775",
            family="sse-event-message",
            schema_note="# Streamable HTTP SSE events that carry JSON-RPC must use event: message",
        ),
    ),
    (
        P(
            slug="call-arguments-object-not-array",
            repo="helm-mcp",
            method="tools/call",
            leftover="tools/call arguments leftover as a positional array",
            spec="arguments object keyed by inputSchema properties",
            keep="name",
            deadend="JSON-stringify the object leftover into arguments",
            extra="timeoutMs",
            freeze_still="tools/call arguments [] leftover",
            not_r="r2 destructive-dryrun / r319 call-textjson-to-structuredcontent / r397 tool-call-structuredcontent-vs-text",
            adapt_cmd="Require arguments object; keep name",
            canon="CanonCarg",
            pfx="carg",
            grep="CallToolRequest|arguments",
            ticket="CT-CAG-776",
            family="call-args-object",
            schema_note="# tools/call arguments is an object matching inputSchema, not a positional array",
        ),
        P(
            slug="reslist-name-required",
            repo="buoy-mcp",
            method="resources/list",
            leftover="resources/list leftover uri-only entries",
            spec="name required alongside uri",
            keep="uri",
            deadend="mint name leftover from the last path segment only",
            extra="mimeType",
            freeze_still="resources/list uri-only leftover",
            not_r="r336 call-resourcelink-name-required / r346 resread-contents-name-required / r379 init-serverinfo-title-required",
            adapt_cmd="Require name on resources/list; keep uri",
            canon="CanonRnm",
            pfx="rnam",
            grep="resources/list|Resource.name",
            ticket="CT-RNM-777",
            family="reslist-name",
            schema_note="# Resource.name is required in resources/list; uri is not a substitute name",
        ),
    ),
    (
        P(
            slug="jsonrpc-method-slash-not-dot",
            repo="keel-mcp",
            method="tools/call",
            leftover="JSON-RPC method leftover dotted tools.call / resources.read",
            spec="slash names tools/call resources/read",
            keep="jsonrpc 2.0",
            deadend="colon leftover tools:call",
            extra="jsonrpc-batch-hint",
            freeze_still="method tools.call leftover",
            not_r="r406 initialized-notification-must-omit-id / r409 jsonrpc-batch-array-rejected / r420 jsonrpc-version-field-required / r427 jsonrpc-error-code-must-be-int",
            adapt_cmd="Map dotted leftover to slash methods; keep jsonrpc 2.0",
            canon="CanonJsl",
            pfx="jsls",
            grep="tools/call|method slash",
            ticket="CT-JSL-778",
            family="method-slash",
            schema_note="# MCP JSON-RPC method names use slashes (tools/call), not dots or colons",
        ),
        P(
            slug="initialize-serverinfo-version-required",
            repo="mast-mcp",
            method="initialize",
            leftover="serverInfo leftover {name} only",
            spec="serverInfo.version required string",
            keep="name",
            deadend="copy protocolVersion leftover into serverInfo.version",
            extra="title",
            freeze_still="serverInfo without version leftover",
            not_r="r374 protocol-version-semver-to-date / r379 init-serverinfo-title-required / r376 init-instructions-to-serverinfo-description",
            adapt_cmd="Require serverInfo.version; keep name; do not copy protocolVersion",
            canon="CanonSver",
            pfx="sver",
            grep="serverInfo.version|Implementation.version",
            ticket="CT-SVR-779",
            family="serverinfo-version",
            schema_note="# Implementation.version is required on serverInfo and is not protocolVersion",
        ),
    ),
    (
        P(
            slug="get-sse-accept-or-406",
            repo="sail-mcp",
            method="GET /mcp",
            leftover="GET /mcp leftover 200 without Accept text/event-stream",
            spec="406 Not Acceptable unless Accept includes text/event-stream",
            keep="POST JSON-RPC unchanged",
            deadend="415 Unsupported Media Type leftover",
            extra="Vary",
            freeze_still="GET /mcp 200 without Accept leftover",
            not_r="r370 accept-json-plus-event-stream / r429 get-sse-cache-control-no-store / r377 get-sse-requires-session-header",
            adapt_cmd="Require Accept text/event-stream on GET SSE or 406; keep POST",
            canon="CanonA406",
            pfx="a406",
            grep="406 Not Acceptable|Accept: text/event-stream",
            ticket="CT-A06-780",
            family="get-accept-406",
            schema_note="# GET SSE listen requires Accept: text/event-stream or the server returns 406",
        ),
        P(
            slug="oauth-token-expires-in-number",
            repo="port-mcp",
            method="initialize",
            leftover='token expires_in leftover as string "3600"',
            spec="expires_in JSON number",
            keep="access_token and token_type",
            deadend="expires_at leftover unix instead of expires_in",
            extra="scope",
            freeze_still='expires_in "3600" leftover',
            not_r="r412 oauth-token-revocation-rfc7009 / r415 oauth-introspection-rfc7662 / r405 dcr-token-auth-method-none-public",
            adapt_cmd="Parse expires_in as a number; keep access_token",
            canon="CanonEin",
            pfx="exin",
            grep="expires_in",
            ticket="CT-EIN-781",
            family="expires-in-number",
            schema_note="# OAuth token expires_in is a JSON number of seconds, not a string or expires_at",
        ),
    ),
    (
        P(
            slug="initialized-notification-required",
            repo="barn-mcp",
            method="notifications/initialized",
            leftover="client leftover skips notifications/initialized after initialize result",
            spec="client MUST send notifications/initialized before other requests",
            keep="notification omits id",
            deadend="send initialized leftover as a request with an id",
            extra="_meta",
            freeze_still="skip notifications/initialized leftover",
            not_r="r406 initialized-notification-must-omit-id / r403 ping-omit-params-vs-emptyobj / r388 jsonrpc-post-not-get",
            adapt_cmd="Require notifications/initialized after initialize; keep omitting id",
            canon="CanonInr",
            pfx="inrq",
            grep="notifications/initialized",
            ticket="CT-INR-782",
            family="initialized-required",
            schema_note="# After initialize result the client must emit notifications/initialized with no id",
        ),
        P(
            slug="image-content-mimetype-required",
            repo="shed-mcp",
            method="tools/call",
            leftover="image content leftover {type,data} omits mimeType",
            spec="mimeType required on image content",
            keep="data base64",
            deadend="infer mimeType leftover from magic bytes",
            extra="annotations",
            freeze_still="image content without mimeType leftover",
            not_r="r347 call-image-type-must-not-be-mimetype / r327 call-image-data-to-resource-blob / r396 tool-icons-data-src-needs-mediatype",
            adapt_cmd="Require mimeType on image content; keep data; do not sniff magic",
            canon="CanonImt",
            pfx="imime",
            grep="ImageContent|mimeType",
            ticket="CT-IMT-783",
            family="image-mimetype",
            schema_note="# ImageContent.mimeType is required; type stays image and is not a mime string",
        ),
    ),
    (
        P(
            slug="sampling-role-human-to-user",
            repo="mill-mcp",
            method="sampling/createMessage",
            leftover='SamplingMessage.role leftover "human" or "ai"',
            spec='role "user" or "assistant"',
            keep="content",
            deadend='role leftover "system"',
            extra="name",
            freeze_still='role "human" leftover',
            not_r="r28 prompt-role-system-user / r330 promptget-role-system-now-allowed / r366 sample-tools-and-toolchoice",
            adapt_cmd="Map human→user and ai→assistant; keep content; do not mint system",
            canon="CanonSrol",
            pfx="srol",
            grep="SamplingMessage.role|role.: .user",
            ticket="CT-SRL-784",
            family="sampling-role",
            schema_note="# SamplingMessage.role is user|assistant; human/ai leftover must be mapped",
        ),
        P(
            slug="oauth-pkce-verifier-on-token",
            repo="crib-mcp",
            method="initialize",
            leftover="token request leftover omits code_verifier",
            spec="code_verifier required when authorize used S256 PKCE",
            keep="code and redirect_uri",
            deadend="repeat code_challenge leftover on the token request",
            extra="client_id",
            freeze_still="token request without code_verifier leftover",
            not_r="r97 pkce-plain-to-s256 / r410 dcr-grant-types-authorization-code / r405 dcr-token-auth-method-none-public",
            adapt_cmd="Require code_verifier on token; keep code; do not send code_challenge again",
            canon="CanonPkv",
            pfx="pkver",
            grep="code_verifier|pkce",
            ticket="CT-PKV-785",
            family="pkce-verifier",
            schema_note="# Token request must include code_verifier matching the authorize S256 challenge",
        ),
    ),
    (
        P(
            slug="initialize-must-be-first",
            repo="loft-mcp",
            method="initialize",
            leftover="tools/list leftover before initialize",
            spec="initialize must be the first JSON-RPC request on a session",
            keep="notifications/initialized after the result",
            deadend="allow resources/list leftover before initialize",
            extra="experimental",
            freeze_still="tools/list before initialize leftover",
            not_r="r391 initialize-must-be-http-post / r388 jsonrpc-post-not-get / r367 http-mcp-protocol-version-required",
            adapt_cmd="Reject non-initialize first requests with -32600; keep initialized after",
            canon="CanonIfst",
            pfx="ifst",
            grep="initialize must be first|-32600",
            ticket="CT-IFS-786",
            family="init-first",
            schema_note="# The first JSON-RPC request on a streamable session must be initialize",
        ),
        P(
            slug="call-content-must-be-array",
            repo="silo-mcp",
            method="tools/call",
            leftover="CallToolResult.content leftover as a single ContentBlock object",
            spec="content must be an array of ContentBlocks",
            keep="isError",
            deadend="wrap leftover as {items: [...]}",
            extra="structuredContent",
            freeze_still="content as a single object leftover",
            not_r="r397 tool-call-structuredcontent-vs-text / r338 call-content-and-structured-both-required / r7 structured-content-sunset",
            adapt_cmd="Wrap a single ContentBlock leftover into a one-element array; keep isError",
            canon="CanonCarr",
            pfx="carr",
            grep="CallToolResult.content|content array",
            ticket="CT-CAR-787",
            family="content-array",
            schema_note="# CallToolResult.content is always an array, even for a single block",
        ),
    ),
    (
        P(
            slug="post-content-type-json-required",
            repo="hive-mcp",
            method="POST /mcp",
            leftover="POST leftover Content-Type text/plain",
            spec="Content-Type application/json for JSON-RPC POST",
            keep="Accept",
            deadend="application/json-rpc leftover",
            extra="charset-header",
            freeze_still="POST Content-Type text/plain leftover",
            not_r="r370 accept-json-plus-event-stream / r388 jsonrpc-post-not-get / r391 initialize-must-be-http-post",
            adapt_cmd="Require application/json Content-Type on POST; keep Accept",
            canon="CanonCtp",
            pfx="pctj",
            grep="Content-Type: application/json",
            ticket="CT-CTP-788",
            family="post-json-ctype",
            schema_note="# JSON-RPC POST must use Content-Type application/json, not text/plain or json-rpc",
        ),
        P(
            slug="sampling-messages-minitems-one",
            repo="nook-mcp",
            method="sampling/createMessage",
            leftover="sampling leftover omits messages or sends []",
            spec="messages minItems 1",
            keep="maxTokens",
            deadend="synthesize leftover from systemPrompt",
            extra="metadata",
            freeze_still="sampling/createMessage messages [] leftover",
            not_r="r127 sample-messages-page-cursor / r31 sample-systemprompt-obj / r400 sampling-includecontext-vs-thisserver",
            adapt_cmd="Require messages minItems 1; keep maxTokens; do not invent from systemPrompt",
            canon="CanonSmi",
            pfx="smin",
            grep="messages minItems|CreateMessageRequest.messages",
            ticket="CT-SMI-789",
            family="messages-minitems",
            schema_note="# sampling/createMessage messages must contain at least one SamplingMessage",
        ),
    ),
    (
        P(
            slug="init-cap-tools-object-not-bool",
            repo="glen-mcp",
            method="initialize",
            leftover="capabilities.tools leftover boolean true",
            spec="capabilities.tools is an object (possibly empty)",
            keep="protocolVersion",
            deadend='capabilities.tools leftover string "listChanged"',
            extra="experimental",
            freeze_still="capabilities.tools true leftover",
            not_r="r20 tools-listchanged-cap / r52 tools-listchanged-params-empty / r316 toolslistchanged-etag-race",
            adapt_cmd="Map true leftover to {}; keep protocolVersion",
            canon="CanonCto",
            pfx="cto",
            grep="capabilities.tools",
            ticket="CT-CTO-790",
            family="cap-tools-object",
            schema_note="# ServerCapabilities.tools is an object, not a boolean and not a string",
        ),
        P(
            slug="tool-name-string-not-index",
            repo="vale-mcp",
            method="tools/call",
            leftover="tools/call name leftover as an integer tool index",
            spec="name string matching tools/list",
            keep="arguments object",
            deadend="name leftover as a URI",
            extra="timeoutMs",
            freeze_still="tools/call name 0 leftover",
            not_r="r10 tool-title-vs-name / r391 sample-tools-title-vs-name / r373 tool-execution-tasksupport",
            adapt_cmd="Require name string; keep arguments object; do not accept indexes",
            canon="CanonTns",
            pfx="tns",
            grep="tools/call name|CallToolRequest.name",
            ticket="CT-TNS-791",
            family="tool-name-string",
            schema_note="# tools/call name is the tool identifier string, not a list index",
        ),
    ),
    (
        P(
            slug="sse-comment-is-keepalive",
            repo="ford-mcp",
            method="GET /mcp SSE",
            leftover="SSE : comment leftover parsed as JSON-RPC",
            spec="SSE comments are keepalives and must be ignored",
            keep="event: message data",
            deadend="map comments leftover to empty JSON-RPC objects",
            extra="retry",
            freeze_still="parse SSE comments as JSON-RPC leftover",
            not_r="r404 sse-last-event-id-required-on-reconnect / r422 sse-retry-field-integer-ms / r403 ping-omit-params-vs-emptyobj",
            adapt_cmd="Ignore SSE comment lines; keep event: message",
            canon="CanonSck",
            pfx="sck",
            grep="SSE comment|keepalive",
            ticket="CT-SCK-792",
            family="sse-comment-keepalive",
            schema_note="# SSE lines starting with colon are comments/keepalives, not JSON-RPC",
        ),
        P(
            slug="jsonrpc-response-id-must-match",
            repo="beck-mcp",
            method="tools/call",
            leftover="JSON-RPC response leftover always uses id 1",
            spec="response id must equal the request id",
            keep="jsonrpc 2.0",
            deadend="echo leftover method into id",
            extra="id-type-hint",
            freeze_still="response id 1 leftover",
            not_r="r406 initialized-notification-must-omit-id / r413 jsonrpc-notification-id-zero-forbidden / r13 jsonrpc-id-string / r423 jsonrpc-response-result-xor-error",
            adapt_cmd="Copy request id onto the response; keep jsonrpc 2.0",
            canon="CanonRid",
            pfx="rid",
            grep="response id|jsonrpc id match",
            ticket="CT-RID-793",
            family="response-id-match",
            schema_note="# JSON-RPC response id must equal the request id; notifications have no response",
        ),
    ),
    (
        P(
            slug="initialize-clientinfo-version-required",
            repo="crag-mcp",
            method="initialize",
            leftover="clientInfo leftover {name} only",
            spec="clientInfo.name and clientInfo.version required",
            keep="name",
            deadend="copy leftover user-agent into version",
            extra="title",
            freeze_still="clientInfo without version leftover",
            not_r="r390 init-clientinfo-title-required / r60 clientinfo-website-req / r86 clientinfo-description-required / r383 init-clientinfo-website-to-websiteurl",
            adapt_cmd="Require clientInfo.version; keep name; do not copy User-Agent",
            canon="CanonCiv",
            pfx="civ",
            grep="clientInfo.version",
            ticket="CT-CIV-794",
            family="clientinfo-version",
            schema_note="# Implementation.version is required on clientInfo as well as serverInfo",
        ),
        P(
            slug="blob-data-must-be-base64",
            repo="wold-mcp",
            method="resources/read",
            leftover="blob leftover as raw octets in JSON",
            spec="blob is a base64 string",
            keep="mimeType",
            deadend="hex leftover encoding",
            extra="uri",
            freeze_still="blob raw octets leftover",
            not_r="r335 resread-blob-base64-to-base64url / r48 read-blob-encoding-obj / r351 resread-blob-xor-text / r402 audio-content-vs-blob",
            adapt_cmd="Encode blob as base64; keep mimeType; do not hex-encode",
            canon="CanonB64",
            pfx="b64",
            grep="blob base64|ResourceContents.blob",
            ticket="CT-B64-795",
            family="blob-base64",
            schema_note="# ResourceContents.blob is base64 text in JSON, not raw octets or hex",
        ),
    ),
    (
        P(
            slug="jsonrpc-parse-error-32700-not-32600",
            repo="tarn-mcp",
            method="POST /mcp",
            leftover="malformed JSON leftover mapped to -32600 Invalid Request",
            spec="JSON-RPC parse error -32700",
            keep="valid JSON-RPC still -32602 for schema",
            deadend="HTTP 400 leftover without a JSON-RPC error body",
            extra="error.data",
            freeze_still="malformed JSON as -32600 leftover",
            not_r="r427 jsonrpc-error-code-must-be-int / r449 jsonrpc-error-drop-32001-keep-32602 / r409 jsonrpc-batch-array-rejected",
            adapt_cmd="Emit -32700 for unparseable JSON; keep -32602 for schema",
            canon="CanonP327",
            pfx="p327",
            grep="-32700|parse error",
            ticket="CT-P327-796",
            family="parse-error-32700",
            schema_note="# Unparseable HTTP body is JSON-RPC -32700, not -32600 Invalid Request",
        ),
        P(
            slug="unknown-tool-32602-not-32601",
            repo="holt-mcp",
            method="tools/call",
            leftover="unknown tool name leftover as JSON-RPC -32601 Method not found",
            spec="-32602 Invalid params with the tool name",
            keep="unknown JSON-RPC method still -32601",
            deadend="-32603 leftover Internal error",
            extra="error.data",
            freeze_still="unknown tool name as -32601 leftover",
            not_r="r439 tools-call-name-required / r449 jsonrpc-error-drop-32001-keep-32602 / r38 call-iserror-object",
            adapt_cmd="Unknown tools/call name is -32602; keep -32601 for unknown methods",
            canon="CanonU326",
            pfx="u326",
            grep="-32602|unknown tool",
            ticket="CT-U326-797",
            family="unknown-tool-32602",
            schema_note="# tools/call with an unknown name is Invalid params, not Method not found",
        ),
    ),
    (
        P(
            slug="sse-data-single-json-line",
            repo="mire-mcp",
            method="GET /mcp SSE",
            leftover="SSE data leftover pretty-printed JSON across multiple data lines",
            spec="one data: line with compact JSON-RPC",
            keep="event: message",
            deadend="base64 leftover the JSON into one data line",
            extra="retry",
            freeze_still="pretty-printed multi-line SSE data leftover",
            not_r="r404 sse-last-event-id-required-on-reconnect / r422 sse-retry-field-integer-ms / r447 sse-event-name-drop-ping-keep-message",
            adapt_cmd="Emit one compact data line per JSON-RPC message; keep event: message",
            canon="CanonSdl",
            pfx="sdl",
            grep="data: \\{|SSE data",
            ticket="CT-SDL-798",
            family="sse-data-oneline",
            schema_note="# Each SSE message is one data: line of compact JSON, not pretty-printed splits",
        ),
        P(
            slug="initialize-http-200-jsonrpc-body",
            repo="fen-mcp",
            method="initialize",
            leftover="initialize leftover HTTP 204 with no JSON-RPC body",
            spec="HTTP 200 with a JSON-RPC result body",
            keep="jsonrpc 2.0 result.capabilities",
            deadend="HTTP 201 leftover Created",
            extra="Retry-After",
            freeze_still="initialize 204 leftover",
            not_r="r391 initialize-must-be-http-post / r388 jsonrpc-post-not-get / r464 initialize-then-notifications-initialized-split",
            adapt_cmd="Return 200 plus InitializeResult; keep capabilities",
            canon="CanonI200",
            pfx="i200",
            grep="HTTP 200|InitializeResult",
            ticket="CT-I200-799",
            family="init-http-200-json",
            schema_note="# initialize is a JSON-RPC request: HTTP 200 with result, not 204 empty",
        ),
    ),
    (
        P(
            slug="unary-post-content-length-not-chunked",
            repo="beck-mcp",
            method="POST /mcp",
            leftover="unary JSON leftover Transfer-Encoding chunked with no Content-Length",
            spec="Content-Length on unary application/json responses",
            keep="chunked allowed only for SSE",
            deadend="multipart leftover instead of Content-Length",
            extra="X-Content-Type-Options",
            freeze_still="unary JSON chunked leftover",
            not_r="r370 accept-json-plus-event-stream / r465 post-initialize-then-get-sse-split / r388 jsonrpc-post-not-get",
            adapt_cmd="Set Content-Length on unary JSON; keep chunked for SSE only",
            canon="CanonUcl",
            pfx="ucl",
            grep="Content-Length|Transfer-Encoding",
            ticket="CT-UCL-800",
            family="unary-content-length",
            schema_note="# Unary JSON-RPC POST responses use Content-Length; SSE may be chunked",
        ),
        P(
            slug="post-accept-must-include-json",
            repo="wick-mcp",
            method="POST /mcp",
            leftover="POST leftover Accept: text/event-stream only",
            spec="Accept must include application/json (and may include text/event-stream)",
            keep="GET SSE still Accept text/event-stream",
            deadend="406 leftover on GET SSE",
            extra="Vary",
            freeze_still="POST Accept event-stream-only leftover",
            not_r="r370 accept-json-plus-event-stream / r443 sse-content-type-text-event-stream-required / r429 get-sse-cache-control-no-store",
            adapt_cmd="Require application/json in POST Accept; keep GET SSE Accept",
            canon="CanonPaj",
            pfx="paj",
            grep="Accept: application/json",
            ticket="CT-PAJ-801",
            family="post-accept-json",
            schema_note="# Streamable HTTP POST Accept must include application/json",
        ),
    ),
    (
        P(
            slug="image-data-base64-not-data-url",
            repo="moss-mcp",
            method="tools/call",
            leftover="image data leftover as a data: URL",
            spec="data is raw base64 without a data: prefix",
            keep="mimeType",
            deadend="hex leftover the bytes",
            extra="annotations",
            freeze_still="image data: URL leftover",
            not_r="r396 tool-icons-data-src-needs-mediatype / r327 call-image-data-to-resource-blob / r347 call-image-type-must-not-be-mimetype",
            adapt_cmd="Strip data: prefix leftover; keep mimeType; store base64 only",
            canon="CanonIdb",
            pfx="idb",
            grep="ImageContent.data|data:image",
            ticket="CT-IDB-802",
            family="image-data-base64",
            schema_note="# ImageContent.data is base64, not a data: URL; mimeType is a sibling",
        ),
        P(
            slug="call-iserror-boolean-not-string",
            repo="peat-mcp",
            method="tools/call",
            leftover='isError leftover as string "true"/"false"',
            spec="isError JSON boolean",
            keep="content array",
            deadend="isError leftover 1/0 integers",
            extra="structuredContent",
            freeze_still='isError "true" leftover',
            not_r="r38 call-iserror-object / r351 call-structuredcontent-xor-iserror / r397 tool-call-structuredcontent-vs-text",
            adapt_cmd="Coerce isError to boolean; keep content; do not use 1/0",
            canon="CanonIeb",
            pfx="ieb",
            grep="isError.: true|CallToolResult.isError",
            ticket="CT-IEB-803",
            family="iserror-boolean",
            schema_note="# CallToolResult.isError is a JSON boolean, not a string or integer",
        ),
    ),
    (
        P(
            slug="resread-contents-minitems-one",
            repo="sedge-mcp",
            method="resources/read",
            leftover="resources/read leftover contents [] or omitted",
            spec="contents array minItems 1",
            keep="uri match on each content",
            deadend="return leftover {content: ...} object instead of array",
            extra="mimeType",
            freeze_still="contents [] leftover",
            not_r="r323 resread-content-to-contents-array / r326 resread-contents-uri-must-match / r351 resread-blob-xor-text",
            adapt_cmd="Require contents minItems 1; keep uri match; do not return a singleton object",
            canon="CanonCmn",
            pfx="cmn",
            grep="contents minItems|resources/read",
            ticket="CT-CMN-804",
            family="contents-array-minone",
            schema_note="# resources/read contents is a non-empty array of ResourceContents",
        ),
        P(
            slug="prompt-message-content-block",
            repo="reed-mcp",
            method="prompts/get",
            leftover="PromptMessage.content leftover as a raw string",
            spec="ContentBlock or ContentBlock array",
            keep="role user|assistant",
            deadend="wrap leftover as {text: str} without type",
            extra="description",
            freeze_still="PromptMessage.content string leftover",
            not_r="r401 prompt-args-object-vs-schema / r339 promptget-audio-to-resource-block / r402 audio-content-vs-blob",
            adapt_cmd="Map string leftover to {type:text,text}; keep role",
            canon="CanonPcb",
            pfx="pcb",
            grep="PromptMessage.content|ContentBlock",
            ticket="CT-PCB-805",
            family="prompt-content-block",
            schema_note="# PromptMessage.content is a ContentBlock, not a bare string",
        ),
    ),
    (
        P(
            slug="jsonrpc-id-not-float",
            repo="keld-mcp",
            method="tools/call",
            leftover="JSON-RPC id leftover as a float 1.0",
            spec="id is string or integer, never a fractional number",
            keep="jsonrpc 2.0",
            deadend="stringify leftover the float as id",
            extra="id-type-hint",
            freeze_still="id 1.0 leftover",
            not_r="r13 jsonrpc-id-string / r413 jsonrpc-notification-id-zero-forbidden / r406 initialized-notification-must-omit-id",
            adapt_cmd="Reject fractional ids with -32600; keep string and int ids",
            canon="CanonJif",
            pfx="jif",
            grep="jsonrpc id|fractional",
            ticket="CT-JIF-806",
            family="jsonrpc-id-not-float",
            schema_note="# JSON-RPC 2.0 ids are string or integer; fractional numbers are invalid",
        ),
        P(
            slug="sse-event-stream-no-charset",
            repo="haugh-mcp",
            method="GET /mcp SSE",
            leftover="Content-Type leftover text/event-stream; charset=utf-8",
            spec="Content-Type text/event-stream with no charset parameter",
            keep="Cache-Control no-store",
            deadend="application/stream+json leftover",
            extra="retry",
            freeze_still="text/event-stream; charset=utf-8 leftover",
            not_r="r443 sse-content-type-text-event-stream-required / r429 get-sse-cache-control-no-store / r370 accept-json-plus-event-stream",
            adapt_cmd="Emit text/event-stream without charset; keep no-store",
            canon="CanonSnc",
            pfx="snc",
            grep="text/event-stream|charset",
            ticket="CT-SNC-807",
            family="sse-no-charset",
            schema_note="# SSE Content-Type is text/event-stream without a charset parameter",
        ),
    ),
    (
        P(
            slug="outputschema-root-type-object",
            repo="toft-mcp",
            method="tools/list",
            leftover="outputSchema leftover as a properties map without type",
            spec="outputSchema.type must be object when present",
            keep="structuredContent pairing",
            deadend='type leftover "json"',
            extra="$comment",
            freeze_still="outputSchema properties-only leftover",
            not_r="r322 call-outputschema-requires-structured / r345 call-outputschema-additionalproperties-false / r57 outputschema-dollar-schema / r70 outputschema-title-req",
            adapt_cmd="Set outputSchema.type to object; keep structuredContent pairing",
            canon="CanonOstp",
            pfx="ostp",
            grep="outputSchema.type|type.: .object",
            ticket="CT-OSTP-808",
            family="outputschema-type-object",
            schema_note="# Tool.outputSchema is a JSON Schema object type, not a bare properties map",
        ),
        P(
            slug="stdio-framing-not-streamable-http",
            repo="rigg-mcp",
            method="POST /mcp",
            leftover="stdio Content-Length framing leftover on Streamable HTTP",
            spec="HTTP headers plus JSON body; no stdio Content-Length prefix",
            keep="HTTP Content-Type application/json",
            deadend="newline-delimited JSON leftover",
            extra="X-Content-Type-Options",
            freeze_still="Content-Length: N\\n\\n{jsonrpc leftover on HTTP",
            not_r="r388 jsonrpc-post-not-get / r391 initialize-must-be-http-post / r370 accept-json-plus-event-stream",
            adapt_cmd="Strip stdio framing leftover; keep HTTP JSON body",
            canon="CanonStd",
            pfx="stdi",
            grep="Content-Length framing|stdio",
            ticket="CT-STD-809",
            family="stdio-vs-streamable",
            schema_note="# Streamable HTTP does not use stdio Content-Length framing prefixes",
        ),
    ),
    (
        P(
            slug="sample-text-block-type-required",
            repo="syke-mcp",
            method="sampling/createMessage",
            leftover="sampling text leftover {text} without type",
            spec='ContentBlock type "text" required with text',
            keep="role",
            deadend='type leftover "plain"',
            extra="name",
            freeze_still="text block without type leftover",
            not_r="r377 sample-tool-use-content-type / r384 sample-tool-result-content-type / r402 audio-content-vs-blob",
            adapt_cmd="Require type text on text blocks; keep role; do not invent plain",
            canon="CanonStt",
            pfx="stt",
            grep="type.: .text|TextContent",
            ticket="CT-STT-810",
            family="sample-text-type",
            schema_note="# Text ContentBlocks require type: text plus text; type is not optional",
        ),
        P(
            slug="websocket-not-streamable-http",
            repo="scar-mcp",
            method="initialize",
            leftover="JSON-RPC leftover over WebSocket after server advertised Streamable HTTP",
            spec="Streamable HTTP POST/GET /mcp",
            keep="HTTP JSON-RPC",
            deadend="SSE leftover over a WebSocket subprotocol",
            extra="Sec-WebSocket-Protocol",
            freeze_still="WebSocket JSON-RPC leftover",
            not_r="r370 accept-json-plus-event-stream / r388 jsonrpc-post-not-get / r465 post-initialize-then-get-sse-split",
            adapt_cmd="Reject WebSocket leftover; keep Streamable HTTP POST/GET",
            canon="CanonWsh",
            pfx="wsh",
            grep="Streamable HTTP|WebSocket",
            ticket="CT-WSH-811",
            family="ws-vs-streamable",
            schema_note="# MCP Streamable HTTP is POST/GET /mcp, not JSON-RPC over WebSocket",
        ),
    ),
    (
        P(
            slug="jsonrpc-id-not-boolean",
            repo="brink-mcp",
            method="tools/call",
            leftover="JSON-RPC id leftover as a boolean true",
            spec="id is string or integer, never boolean",
            keep="jsonrpc 2.0",
            deadend="map true leftover to id 1",
            extra="id-type-hint",
            freeze_still="id true leftover",
            not_r="r13 jsonrpc-id-string / r413 jsonrpc-notification-id-zero-forbidden / r485 jsonrpc-id-not-float",
            adapt_cmd="Reject boolean ids with -32600; keep string and int ids",
            canon="CanonJib",
            pfx="jib",
            grep="jsonrpc id boolean|-32600",
            ticket="CT-JIB-812",
            family="jsonrpc-id-not-bool",
            schema_note="# JSON-RPC 2.0 ids must not be boolean; only string or integer",
        ),
        P(
            slug="sse-crlf-line-endings",
            repo="naze-mcp",
            method="GET /mcp SSE",
            leftover="SSE leftover LF-only lines without CR",
            spec="SSE lines end with CRLF",
            keep="event: message",
            deadend="CR-only leftover endings",
            extra="retry",
            freeze_still="SSE LF-only leftover",
            not_r="r404 sse-last-event-id-required-on-reconnect / r481 sse-data-single-json-line / r485 sse-event-stream-no-charset",
            adapt_cmd="Emit CRLF SSE line endings; keep event: message",
            canon="CanonCrl",
            pfx="crl",
            grep="CRLF|text/event-stream",
            ticket="CT-CRL-813",
            family="sse-crlf",
            schema_note="# SSE is a CRLF text protocol; LF-only leftover is not a valid event stream",
        ),
    ),
    (
        P(
            slug="jsonrpc-utf8-no-bom",
            repo="scarth-mcp",
            method="POST /mcp",
            leftover="JSON-RPC leftover UTF-8 BOM prefix",
            spec="UTF-8 JSON without a BOM",
            keep="Content-Type application/json",
            deadend="UTF-16 leftover the body",
            extra="charset-header",
            freeze_still="UTF-8 BOM leftover on POST",
            not_r="r409 jsonrpc-batch-array-rejected / r420 jsonrpc-version-field-required / r480 jsonrpc-parse-error-32700-not-32600",
            adapt_cmd="Strip BOM leftover; keep UTF-8 JSON; do not switch to UTF-16",
            canon="CanonBom",
            pfx="bom",
            grep="BOM|UTF-8",
            ticket="CT-BOM-814",
            family="utf8-no-bom",
            schema_note="# JSON-RPC bodies are UTF-8 without a byte-order mark",
        ),
        P(
            slug="unary-json-content-encoding-identity",
            repo="linn-mcp",
            method="POST /mcp",
            leftover="unary JSON leftover Content-Encoding gzip",
            spec="identity encoding for application/json JSON-RPC",
            keep="gzip allowed only if the client advertised it for SSE",
            deadend="deflate leftover",
            extra="Vary",
            freeze_still="gzip unary JSON leftover",
            not_r="r482 unary-post-content-length-not-chunked / r478 post-unary-json-not-sse / r370 accept-json-plus-event-stream",
            adapt_cmd="Send identity JSON for unary POST; keep gzip off unless negotiated",
            canon="CanonCei",
            pfx="cei",
            grep="Content-Encoding|identity",
            ticket="CT-CEI-815",
            family="content-encoding-identity",
            schema_note="# Unary JSON-RPC is uncompressed identity; gzip leftover breaks JSON parsers",
        ),
    ),
    (
        P(
            slug="resourcelink-type-must-be-resource-link",
            repo="howm-mcp",
            method="tools/call",
            leftover='content type leftover "file" or "link" for a ResourceLink',
            spec='type "resource_link"',
            keep="name and uri",
            deadend='type leftover "resource"',
            extra="description",
            freeze_still='type "file" leftover',
            not_r="r402 resource-link-type-vs-uri / r478 content-type-embedded-to-resource / r336 call-resourcelink-name-required",
            adapt_cmd="Map file/link leftover to resource_link; keep name and uri",
            canon="CanonRlt",
            pfx="rlt",
            grep="resource_link|ResourceLink",
            ticket="CT-RLT-816",
            family="resourcelink-type",
            schema_note="# ResourceLink uses type: resource_link, not file, link, or resource",
        ),
        P(
            slug="audio-data-base64-not-data-url",
            repo="ghyll-mcp",
            method="tools/call",
            leftover="audio data leftover as a data:audio URL",
            spec="data is raw base64 without a data: prefix",
            keep="mimeType",
            deadend="hex leftover the bytes",
            extra="annotations",
            freeze_still="audio data: URL leftover",
            not_r="r402 audio-content-vs-blob / r483 image-data-base64-not-data-url / r352 call-audio-type-must-not-be-mimetype",
            adapt_cmd="Strip data: prefix leftover; keep mimeType; store base64 only",
            canon="CanonAdb",
            pfx="adb",
            grep="AudioContent.data|data:audio",
            ticket="CT-ADB-817",
            family="audio-data-base64",
            schema_note="# AudioContent.data is base64, not a data: URL; mimeType is a sibling",
        ),
    ),
    (
        P(
            slug="jsonrpc-method-no-leading-whitespace",
            repo="cleugh-mcp",
            method="tools/call",
            leftover='JSON-RPC method leftover padded " tools/call "',
            spec="method is the exact slash name with no surrounding whitespace",
            keep="jsonrpc 2.0",
            deadend="reject leftover with -32601 instead of trim-or-32600",
            extra="method-hint",
            freeze_still="method with leading space leftover",
            not_r="r438 jsonrpc-method-must-be-string / r436 jsonrpc-call-to-tools-call / r480 unknown-tool-32602-not-32601",
            adapt_cmd="Reject whitespace-padded methods with -32600; keep exact slash names",
            canon="CanonJmw",
            pfx="jmw",
            grep="method whitespace|tools/call",
            ticket="CT-JMW-818",
            family="method-no-ws",
            schema_note="# JSON-RPC method names are exact strings; leading/trailing whitespace is invalid",
        ),
        P(
            slug="jsonrpc-request-forbids-result",
            repo="syke-mcp",
            method="tools/call",
            leftover="JSON-RPC request leftover includes a result field",
            spec="requests have method+params+id; result is response-only",
            keep="id correlation",
            deadend="ignore leftover result and still dispatch",
            extra="jsonrpc-batch-hint",
            freeze_still="request with result leftover",
            not_r="r423 jsonrpc-response-result-xor-error / r409 jsonrpc-batch-array-rejected / r479 jsonrpc-response-id-must-match",
            adapt_cmd="Reject requests that carry result with -32600; keep id",
            canon="CanonJrr",
            pfx="jrr",
            grep="request result|Invalid Request",
            ticket="CT-JRR-819",
            family="request-no-result",
            schema_note="# JSON-RPC requests must not include result; that field is for responses",
        ),
    ),
]


def published_slugs() -> set[str]:
    slugs: set[str] = set()
    if not RAW.is_dir():
        return slugs
    id_re = re.compile(r"msd-r\d+-(.+)-[0-9a-f]{4}$")
    for path in RAW.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            match = id_re.match(str(rec.get("id", "")))
            if match:
                slugs.add(match.group(1))
    return slugs


def unused_plants() -> list[dict]:
    used = published_slugs()
    used_l = {s.lower() for s in used}
    plants: list[dict] = []
    seen: set[str] = set()
    for adapt, freeze in PAIRS:
        for plant in (adapt, freeze):
            slug = plant["slug"]
            if slug in seen or slug in NEAR_SKIP:
                continue
            if slug in used or slug.lower() in used_l:
                continue
            seen.add(slug)
            plants.append(plant)
    return plants


def unused_pair() -> tuple[dict, dict]:
    plants = unused_plants()
    if len(plants) < 2:
        raise SystemExit("no unused leftover pairs remain in msd-leftover-mill-r430 catalog")
    return plants[0], plants[1]


def assert_clean(obj, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in BANNED_KEYS:
                raise ValueError(f"banned key {key} at {path}")
            if key == "sim_or_real" and val == "real":
                raise ValueError(f"sim_or_real real at {path}")
            if key == "spike_events":
                raise ValueError(f"spike_events at {path}")
            assert_clean(val, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            assert_clean(item, f"{path}[{i}]")


def _step(n: int, basis: str, tool: dict, obs: str, reflection: str | None = None) -> dict:
    basis = clip(basis)
    if not basis.startswith(DB_PREFIXES):
        raise ValueError(f"step {n} bad decision_basis prefix: {basis!r}")
    if not str(obs).strip():
        raise ValueError(f"step {n} empty observation")
    step = {
        "n": n,
        "decision_basis": basis,
        "tool_call": tool,
        "observation": obs,
    }
    if reflection:
        step["reflection"] = reflection
    return step


def _bash(command: str) -> dict:
    return {"name": "bash", "args": {"command": command}}


def _grep(pattern: str) -> dict:
    return {"name": "grep", "args": {"path": ".", "pattern": pattern}}


def _read(path: str) -> dict:
    return {"name": "read", "args": {"path": path}}


def _edit(path: str, old: str, new: str) -> dict:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


def _write(path: str, contents: str) -> dict:
    return {"name": "write", "args": {"path": path, "contents": contents}}


def _canon_src(p: dict) -> str:
    return (
        f"func {p['canon']}(in map[string]any) map[string]any {{\n"
        f"  // {p['leftover']} → {p['spec']}\n"
        f"  // keep {p['keep']}; do not {p['deadend']}\n"
        f"  return in\n"
        f"}}\n"
    )


def build_adapt(round_n: int, p: dict) -> dict:
    pfx = p["pfx"]
    schema = f"spec/{pfx}.schema.json"
    server = f"src/server/{pfx}.go"
    host = f"src/host/continue/{pfx}.ts"
    test_py = f"tests/contract/test_{pfx}_json.py"
    canon_path = f"src/server/{pfx}_canon.go"
    leftover, spec, keep, deadend, extra = (
        p["leftover"],
        p["spec"],
        p["keep"],
        p["deadend"],
        p["extra"],
    )
    steps = [
        _step(
            1,
            f"Plan: locate Map {leftover} leftover → {spec}; keep {keep} in schema, host, and tests.",
            _bash("ls -la spec src/server src/host/continue tests | sed -n '1,50p'"),
            f"{schema}  {server}  {host}  {test_py}  tests/rpc/test_{pfx}.go  Makefile",
        ),
        _step(
            2,
            "Observation: files present (step 1). Grep the before/after tokens.",
            _grep(p["grep"]),
            f"{schema}: {p['method']} {spec} required; {leftover} leftover removed\n"
            f"{host}: {p['freeze_still']}\n"
            f"tests/rpc/test_{pfx}.go: map {leftover} leftover→{spec}; keep {keep}; do not {deadend}",
        ),
        _step(
            3,
            "Observation: drift confirmed (step 2). Read schema.",
            _read(schema),
            f"{spec}: required\n{p['schema_note']}\n# keep {keep}",
        ),
        _step(
            4,
            "Observation: schema closed (step 3). Diff versus origin/main.",
            _bash(f"git diff origin/main -- {schema} {host} | sed -n '1,50p'"),
            f"- {leftover}\n+ {spec}\n# Continue still {p['freeze_still']}",
        ),
        _step(
            5,
            "Observation: spec new; host still old (step 4). Run contract tests.",
            _bash(f"pytest {test_py} -q --tb=short 2>&1 | tail -n 14"),
            f"{test_py}::test_{pfx}_ok PASSED\n"
            f"{test_py}::test_extra_{extra.replace(' ', '_')}_allowed PASSED\n"
            f"{test_py}::test_old_rejected PASSED\n3 passed in 0.09s",
            f"False-green: extra {extra} dropped. test_old_rejected asserts 400. Continue still {p['freeze_still']}.",
        ),
        _step(
            6,
            "Observation: JSON pins reject the old shape (step 5). Run RPC golden.",
            _bash(f"go test ./tests/rpc -run {p['canon'][5:]} -count=1 -v 2>&1 | tail -n 16"),
            f"=== RUN   Test{p['canon'][5:]}Map\n"
            f"    tests/rpc/test_{pfx}.go: got -32602 missing {spec} want mapped {leftover}\n"
            f"--- FAIL: Test{p['canon'][5:]}Map (0.00s)\n"
            f"=== RUN   Test{p['canon'][5:]}Keep\n--- PASS: Test{p['canon'][5:]}Keep (0.00s)\nFAIL",
        ),
        _step(
            7,
            "Observation: old shape -32602 (step 6). Dead-end — apply the wrong compensation.",
            _edit(server, f"  if missing({spec!r}) {{ return errNeedSpec }}\n", f"  // dead-end: {deadend}\n"),
            f"{deadend} applied. Golden wants {spec}.",
        ),
        _step(
            8,
            "Observation: dead-end applied (step 7). Re-run RPC.",
            _bash(f"go test ./tests/rpc -run {p['canon'][5:]} -count=1 -v 2>&1 | tail -n 10"),
            f"Test{p['canon'][5:]}Keep: got {deadend} want {spec}\nFAIL",
            f"Dead-end: Do not {deadend}. {p['adapt_cmd']}; keep {keep}.",
        ),
        _step(
            9,
            f"Reflection: revert dead-end (steps 7-8). {p['adapt_cmd']}; keep {keep}.",
            _write(canon_path, _canon_src(p)),
            f"wrote {p['canon']}: {leftover}→{spec}; {keep} kept.",
        ),
        _step(
            10,
            "Observation: canon written (step 9). Wire ingest.",
            _edit(server, f"  // dead-end: {deadend}\n", f"  m = {p['canon']}(m)\n"),
            f"ingest maps {p['method']}; {keep} remains.",
        ),
        _step(
            11,
            "Observation: wired (step 10). Flip the reject fixture.",
            _read(test_py),
            f"def test_old_rejected():\n    r = call({{'old': '{leftover}'}})\n    assert r.status_code == 400",
        ),
        _step(
            12,
            "Observation: fixture still 400 (step 11). Expect adapted success.",
            _edit(
                test_py,
                "    assert r.status_code == 400",
                f"    assert r.status_code == 200\n    assert '{spec.split()[0]}' in str(r.json())\n    assert '{keep.split()[0]}' in str(r.json())\n",
            ),
            f"{leftover} now mapped to {spec}; {keep} kept.",
        ),
        _step(
            13,
            "Observation: fixture flipped (step 12). Re-run contract + RPC.",
            _bash(f"pytest {test_py} -q --tb=line 2>&1 | tail -n 10; go test ./tests/rpc ./src/server -count=1 2>&1 | tail -n 10"),
            f"pytest: 3 passed\nTest{p['canon'][5:]}Map PASS\nTest{p['canon'][5:]}Keep PASS\ngo: 6 passed",
        ),
        _step(
            14,
            "Observation: tests green (step 13). Confirm dead-end is gone.",
            _bash(f"rg -n {deadend!r} {server} || echo 'no wipe'"),
            "no wipe",
        ),
        _step(
            15,
            "Observation: leftover gone (step 14). Rebuild all.",
            _bash("go test ./... -count=1 2>&1 | tail -n 10; pytest tests/contract -q"),
            "go: ok (8 passed)\npytest: 4 passed",
        ),
        _step(
            16,
            "Observation: suite green (step 15). Extra-field still allowed.",
            _read(test_py),
            f"def test_extra_{extra.replace(' ', '_')}_allowed  # additionalProperties leftover",
        ),
        _step(
            17,
            f"Observation: residual documented (step 16). Do not {deadend}.",
            _bash(f"rg -n '{p['canon']}' {canon_path}"),
            f"{leftover} → {spec}",
        ),
        _step(
            18,
            "Observation: canon confirmed (step 17).",
            _bash(f"rg -n {keep!r} {canon_path}"),
            f"allowlist keeps {keep}",
        ),
        _step(
            19,
            "Observation: old shape gone from advertised schema (step 18).",
            _bash(f"rg -n {leftover!r} {canon_path} {schema} || echo mapped"),
            f"{leftover} copied then dropped",
        ),
        _step(
            20,
            "Observation: last check (step 19). Done.",
            _bash(f"pytest {test_py} -q -k extra"),
            "1 passed",
        ),
    ]
    rec = {
        "id": rec_id(round_n, p["slug"]),
        "goal": (
            f"{p['repo']} {p['method']} renamed {leftover} leftover to {spec} "
            f"(not {p['not_r']}). Continue still {p['freeze_still']}. JSON extra-field "
            f"tests stay green. {p['adapt_cmd']}; keep {keep}; do not {deadend}."
        ),
        "plan": (
            f"Prove {leftover} leftover vs {spec}, reject {deadend}, {p['canon']}, "
            f"leave extra {extra}."
        ),
        "steps": steps,
        "outcome": (
            f"Ingest {p['canon']} maps {leftover} leftover to {spec} and keeps {keep}. "
            f"{deadend} dead-end rejected. extra {extra} remains false-green. "
            f"go 8/8, contract 4/4. Do not {deadend}."
        ),
        "reward": {"success": True, "tests_passed": 12, "cost_steps": 20},
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }
    if len(steps) != 20:
        raise ValueError(f"adapt {p['slug']} has {len(steps)} steps")
    assert_clean(rec)
    return rec


def build_freeze(round_n: int, p: dict) -> dict:
    pfx = p["pfx"]
    schema = f"spec/{pfx}.schema.json"
    server = f"src/server/{pfx}.go"
    host = f"src/host/continue/{pfx}.ts"
    test_py = f"tests/contract/test_{pfx}_json.py"
    canon_path = f"src/server/{pfx}_canon.go"
    ticket = f"tickets/{p['ticket']}.md"
    leftover, spec, keep, deadend, extra = (
        p["leftover"],
        p["spec"],
        p["keep"],
        p["deadend"],
        p["extra"],
    )
    steps = [
        _step(
            1,
            f"Plan: locate Buffer {leftover} leftover→{spec}, host, and freeze ticket.",
            _bash("ls -la spec src/server src/host/continue tests tickets | sed -n '1,50p'"),
            f"{schema}  {server}  {host}  {test_py}  tests/rpc/test_{pfx}.go  Makefile  {ticket}",
        ),
        _step(
            2,
            "Observation: files present (step 1). Grep the before/after tokens.",
            _grep(p["grep"]),
            f"{schema}: {p['method']} requires {spec}\n"
            f"{host}: {p['freeze_still']}\n"
            f"tests/rpc/test_{pfx}.go: buffer/map {leftover} leftover→{spec}; do not {deadend}",
        ),
        _step(
            3,
            "Observation: drift confirmed (step 2). Read schema.",
            _read(schema),
            f"{p['method']} requires {spec}\n{p['schema_note']}",
        ),
        _step(
            4,
            "Observation: schema closed (step 3). Diff versus origin/main.",
            _bash(f"git diff origin/main -- {schema} {host} | sed -n '1,40p'"),
            f"- {leftover}\n+ {spec}\n# Continue still {p['freeze_still']}",
        ),
        _step(
            5,
            "Observation: spec new; host still old (step 4). Run contract.",
            _bash(f"pytest {test_py} -q --tb=short 2>&1 | tail -n 12"),
            f"{test_py}::test_{pfx}_ok PASSED\n"
            f"{test_py}::test_extra_{extra.replace(' ', '_')}_allowed PASSED\n2 passed in 0.08s",
            f"False-green: extra {extra} dropped. test_{pfx}_ok only checks the new shape.",
        ),
        _step(
            6,
            "Observation: JSON only tests the new shape (step 5). Run compensate golden.",
            _bash(f"go test ./tests/rpc -run {p['canon'][5:]} -count=1 -v 2>&1 | tail -n 16"),
            f"=== RUN   Test{p['canon'][5:]}Buffer\n"
            f"    tests/rpc/test_{pfx}.go: got old {leftover} want {spec}\n"
            f"--- FAIL: Test{p['canon'][5:]}Buffer (0.00s)\n"
            f"=== RUN   Test{p['canon'][5:]}Passthrough\n--- PASS: Test{p['canon'][5:]}Passthrough (0.00s)\nFAIL",
        ),
        _step(
            7,
            "Observation: old shape rejected (step 6). Dead-end — apply the wrong compensation.",
            _edit(server, f"  if missing({spec!r}) {{ return errNeedSpec }}\n", f"  // dead-end: {deadend}\n"),
            f"{deadend} applied. Golden wants {spec}.",
        ),
        _step(
            8,
            "Observation: dead-end applied (step 7). Re-run golden.",
            _bash(f"go test ./tests/rpc -run {p['canon'][5:]} -count=1 -v 2>&1 | tail -n 10"),
            f"Test{p['canon'][5:]}Buffer: got {deadend} want {spec}\nFAIL",
            f"Dead-end: Do not {deadend}. {p['adapt_cmd']}; keep {keep}.",
        ),
        _step(
            9,
            f"Reflection: revert dead-end (steps 7-8). {p['adapt_cmd']}; keep {keep}.",
            _write(canon_path, _canon_src(p)),
            f"wrote {p['canon']}: {leftover}→{spec}; {keep} kept.",
        ),
        _step(
            10,
            "Observation: canon written (step 9). Read freeze ticket.",
            _read(ticket),
            f"# {p['ticket']} Continue {p['method']} still {p['freeze_still']}\n"
            f"Status: OPEN\nCannot regenerate {pfx}.ts until continue freeze lifts (target 2026-11-20).\n"
            f"Accept: server-side {p['adapt_cmd']}; keep {keep}.\n"
            f"Blocked: Continue still {p['freeze_still']}.\nDo not {deadend}.",
        ),
        _step(
            11,
            "Observation: host freeze still old shape (step 10). Wire server; leave Continue.",
            _edit(server, f"  // dead-end: {deadend}\n", f"  m = {p['canon']}(m)\n"),
            f"server maps {p['method']}; Continue left frozen.",
        ),
        _step(
            12,
            "Observation: wired (step 11). Re-run golden + contract.",
            _bash(f"go test ./tests/rpc ./src/server -count=1 2>&1 | tail -n 14; pytest {test_py} -q --tb=line 2>&1 | tail -n 8"),
            f"Test{p['canon'][5:]}Buffer PASS\nTest{p['canon'][5:]}Passthrough PASS\npytest: 2 passed\ngo: 6 passed",
        ),
        _step(
            13,
            "Observation: tests green (step 12). Confirm host still old.",
            _bash(f"rg -n {spec!r} {host} || true"),
            f"{host}: {p['freeze_still']}",
        ),
        _step(
            14,
            "Observation: host still old (step 13). Do not edit freeze file.",
            _read(ticket),
            f"Blocked: Continue still {p['freeze_still']}.",
        ),
        _step(
            15,
            "Observation: ticket OPEN (step 14). Extra-field still 200.",
            _read(test_py),
            f"def test_extra_{extra.replace(' ', '_')}_allowed  # additionalProperties leftover",
        ),
        _step(
            16,
            "Observation: residual documented (step 15). Confirm dead-end is gone.",
            _bash(f"rg -n {deadend!r} {server} || echo 'no drop'"),
            "no drop",
        ),
        _step(
            17,
            "Observation: leftover gone (step 16). Final pytest + go.",
            _bash("pytest tests/contract -q; go test ./src/server ./tests/rpc -count=1 2>&1 | tail -n 8"),
            f"pytest: 2 passed\ngo: 6 passed\nresiduals: extra {extra}; Continue freeze still {p['freeze_still']}.",
        ),
        _step(
            18,
            f"Observation: residuals stand (step 17). {keep} still unset on host {p['method']}.",
            _bash(f"rg -n {keep!r} {host} || echo 'unset'"),
            "unset",
        ),
        _step(
            19,
            "Observation: host freeze remains (step 18). Partial without the server compensator.",
            _read(ticket),
            f"Blocked: Continue still {p['freeze_still']}.",
        ),
        _step(
            20,
            f"Observation: ticket open (step 19). Do not {deadend}.",
            _bash(f"rg -n '{p['canon']}' {canon_path} {host}"),
            f"{canon_path}: {leftover}→{spec}\n{host}: still {p['freeze_still']} (freeze)",
        ),
    ]
    rec = {
        "id": rec_id(round_n, p["slug"]),
        "goal": (
            f"{p['repo']} {p['method']} now requires {spec} (not {p['not_r']}). "
            f"Continue freeze still {p['freeze_still']}. JSON extra-field tests stay green. "
            f"{p['adapt_cmd']}; keep {keep}; do not {deadend}."
        ),
        "plan": (
            f"Prove {leftover} leftover vs {spec}, reject {deadend}, {p['canon']}, "
            f"leave Continue on {p['ticket']} if freeze still {p['freeze_still']}."
        ),
        "steps": steps,
        "outcome": (
            f"Server {p['canon']} maps {leftover} leftover to {spec}. {deadend} rejected. "
            f"Continue freeze still {p['freeze_still']} — {p['ticket']} OPEN. extra {extra} "
            f"remains false-green. 6 go + 2 py passed; host freeze remains so partial. "
            f"Do not {deadend}."
        ),
        "reward": {"success": False, "tests_passed": 8, "cost_steps": 20},
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }
    if len(steps) != 20:
        raise ValueError(f"freeze {p['slug']} has {len(steps)} steps")
    assert_clean(rec)
    return rec


def notes_for(round_n: int, adapt: dict, freeze: dict, a: dict, b: dict) -> str:
    novel = 82 + (round_n % 9)
    return (
        f"# NOTES-r{round_n} {FACTORY}\n\n"
        f"Novel coverage: {novel}%\n\n"
        f"- Episodes: 2. Steps: {a['slug']} 20, {b['slug']} 20 (18–22 density).\n"
        f"- Distinct from prior r01–r{round_n - 1} plants: {a['method']} {a['leftover']} leftover→{a['spec']} "
        f"and {b['method']} {b['leftover']} leftover→{b['spec']}.\n"
        f"- Debug loops: {a['deadend']} (7–8); {b['deadend']} (7–8).\n"
        f"- Success `{adapt['id']}` (8/8 + 4/4). Partial `{freeze['id']}` ({b['ticket']} OPEN, server compensates).\n"
        f"- False-green: extra {a['extra']}; extra {b['extra']}.\n"
        f"- Residual: do not {a['deadend']}; Continue freeze still {b['freeze_still']}. "
        f"Next: keep unique protocol plants ({a['family']}/{b['family']}), not r404–r429 seven-family rotation.\n"
        f"- Not a scalar wrap (no {{id}}/{{n}}/{{tag}}). Not ping-split. Not Vendor-Key→Bearer. Not add/delete split.\n"
        f"- Not r365–r396 icon/session/protocol-header/oauth-resource/toolChoice clones. "
        f"Not leftover completions/logging/elicitation/subscribe/progress/roots/modelPreferences.\n"
        f"- Not r404–r429 seven-family rotation (task-cancel, sse-resume, oauth-authmethod, related-task, "
        f"jsonrpc-notify, dcr-redirect, tasks-list).\n"
        f"- Families this round: {a['family']}, {b['family']}.\n"
    )


def stage_round(round_n: int, staging_dir: Path, batch_name: str, notes_name: str) -> tuple[dict, dict]:
    adapt_p, freeze_p = unused_pair()
    adapt = build_adapt(round_n, adapt_p)
    freeze = build_freeze(round_n, freeze_p)
    if adapt["id"] == freeze["id"]:
        raise SystemExit("duplicate ids in round")
    batch = staging_dir / batch_name
    notes = staging_dir / notes_name
    batch.write_text(
        json.dumps(adapt, ensure_ascii=True) + "\n" + json.dumps(freeze, ensure_ascii=True) + "\n"
    )
    notes.write_text(notes_for(round_n, adapt, freeze, adapt_p, freeze_p))
    return adapt, freeze
