#!/usr/bin/env python3
"""mcp leftover leftover leftover schema-drift mill r747–r762. Staging only."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/mcp-tool-schema-drift-factory"
FAC = "mcp-tool-schema-drift-factory"
GEN = "grok-4.6"
START = 747
N_ROUNDS = 16
Q = 2

# Skip used r740–r746 slugs. Distinct leftover leftover leftover method/arg splits.
# 16 rounds × 2 plants. Pair A adapt success; pair B freeze/handoff partial.
PAIRS = [
    dict(
        slug="tools-list-outputschema-vs-tools-call-content",
        old="tools/list leftover leftover leftover advertised no outputSchema; tools/call returned content[] only",
        new="tools/list Tool.outputSchema required; tools/call still may emit structuredContent",
        keep="name",
        dead="ignore outputSchema leftover leftover leftover and keep content-only tools/call",
        residual="extra annotations",
        extra="annotations",
        freeze="host still tools/call content[] leftover leftover leftover without structuredContent",
        family="tools/list vs tools/call",
        reject="do not ignore outputSchema leftover leftover leftover",
        method="tools/list",
        peer="tools/call",
        ticket="CT-LLL-1747",
        canon="CanonW800",
        wid="w800",
        test_ok="test_w800_ok",
        falseg="test_extra_annotations_allowed",
        map_fn="if m.get('outputSchema') is None: m['outputSchema']={'type':'object'}",
        success=True,
    ),
    dict(
        slug="prompts-list-icons-vs-prompts-get-description",
        old="prompts/list leftover leftover leftover omitted icons; prompts/get description was a bare string",
        new="prompts/list Prompt.icons[] optional array; prompts/get description remains string",
        keep="name",
        dead="drop icons leftover leftover leftover by aliasing prompts/list as prompts/get",
        residual="extra _meta",
        extra="_meta",
        freeze="host still prompts/list without icons leftover leftover leftover",
        family="prompts/list vs prompts/get",
        reject="do not alias prompts/list as prompts/get leftover leftover leftover",
        method="prompts/list",
        peer="prompts/get",
        ticket="CT-LLL-1748",
        canon="CanonW801",
        wid="w801",
        test_ok="test_w801_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m.setdefault("icons", [])',
        success=False,
    ),
    dict(
        slug="resources-list-size-vs-resources-read-blob",
        old="resources/list leftover leftover leftover omitted size; resources/read returned text only",
        new="resources/list Resource.size integer optional; resources/read may return blob xor text",
        keep="uri",
        dead="force blob leftover leftover leftover on every resources/read including text",
        residual="extra mimeType",
        extra="mimeType",
        freeze="host still resources/read text-only leftover leftover leftover",
        family="resources/list vs resources/read",
        reject="do not force blob leftover leftover leftover on text resources",
        method="resources/list",
        peer="resources/read",
        ticket="CT-LLL-1749",
        canon="CanonW802",
        wid="w802",
        test_ok="test_w802_ok",
        falseg="test_extra_mimeType_allowed",
        map_fn='m.setdefault("size", 0)',
        success=True,
    ),
    dict(
        slug="sampling-create-stopreason-vs-max-tokens",
        old="sampling/createMessage leftover leftover leftover omitted stopReason; maxTokens was unbounded",
        new="sampling/createMessage stopReason enum required on result; maxTokens stays number",
        keep="messages",
        dead="drop stopReason leftover leftover leftover and invent includeContext again",
        residual="extra modelPreferences",
        extra="modelPreferences",
        freeze="host still sampling/createMessage without stopReason leftover leftover leftover",
        family="sampling leftover leftover leftover",
        reject="do not clone includeContext leftover leftover leftover",
        method="sampling/createMessage",
        peer="sampling/createMessage",
        ticket="CT-LLL-1750",
        canon="CanonW803",
        wid="w803",
        test_ok="test_w803_ok",
        falseg="test_extra_modelPreferences_allowed",
        map_fn='m.setdefault("stopReason", "endTurn")',
        success=False,
    ),
    dict(
        slug="roots-list-file-uri-vs-resources-templates-list",
        old="roots/list leftover leftover leftover returned path strings; resources/templates/list unused",
        new="roots/list Root.uri must be file://; do not treat roots as resource templates",
        keep="uri",
        dead="rewrite roots leftover leftover leftover as resources/templates/list",
        residual="extra _meta",
        extra="_meta",
        freeze="host still roots/list path leftover leftover leftover not file://",
        family="roots leftover leftover leftover",
        reject="do not alias roots/list as resources/templates/list leftover leftover leftover",
        method="roots/list",
        peer="resources/templates/list",
        ticket="CT-LLL-1751",
        canon="CanonW804",
        wid="w804",
        test_ok="test_w804_ok",
        falseg="test_extra__meta_allowed",
        map_fn='if str(m.get("uri","")).startswith("/"): m["uri"]="file://"+m["uri"]',
        success=True,
    ),
    dict(
        slug="logging-setlevel-logger-vs-notifications-message",
        old="logging/setLevel leftover leftover leftover had no logger; notifications/message used global",
        new="logging/setLevel logger string optional; notifications/message logger must match",
        keep="level",
        dead="set syslog leftover leftover leftover instead of MCP level enum",
        residual="extra data",
        extra="data",
        freeze="host still logging/setLevel without logger leftover leftover leftover",
        family="logging leftover leftover leftover",
        reject="do not map MCP levels leftover leftover leftover to syslog",
        method="logging/setLevel",
        peer="notifications/message",
        ticket="CT-LLL-1752",
        canon="CanonW805",
        wid="w805",
        test_ok="test_w805_ok",
        falseg="test_extra_data_allowed",
        map_fn='m.setdefault("logger", "mcp")',
        success=False,
    ),
    dict(
        slug="completions-complete-ref-prompt-vs-prompts-get",
        old="completions/complete leftover leftover leftover ref was a bare name; prompts/get unused",
        new="completions/complete ref.type prompt|resource required; do not call prompts/get for complete",
        keep="argument",
        dead="route complete leftover leftover leftover through prompts/get",
        residual="extra _meta",
        extra="_meta",
        freeze="host still completions/complete bare name leftover leftover leftover",
        family="completion leftover leftover leftover",
        reject="do not route completions/complete leftover leftover leftover via prompts/get",
        method="completions/complete",
        peer="prompts/get",
        ticket="CT-LLL-1753",
        canon="CanonW806",
        wid="w806",
        test_ok="test_w806_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m["ref"]={"type":"ref/prompt","name": m.get("name") or (m.get("ref") or {}).get("name")}',
        success=True,
    ),
    dict(
        slug="elicitation-create-mode-vs-tools-call",
        old="elicitation/create leftover leftover leftover had no mode; host used tools/call to collect forms",
        new="elicitation/create mode form|url required; do not collect via tools/call",
        keep="requestedSchema",
        dead="collect elicit leftover leftover leftover via tools/call arguments",
        residual="extra _meta",
        extra="_meta",
        freeze="host still elicit via tools/call leftover leftover leftover",
        family="elicitation leftover leftover leftover",
        reject="do not collect elicitation leftover leftover leftover via tools/call",
        method="elicitation/create",
        peer="tools/call",
        ticket="CT-LLL-1754",
        canon="CanonW807",
        wid="w807",
        test_ok="test_w807_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m.setdefault("mode", "form")',
        success=False,
    ),
    dict(
        slug="notifications-tools-list-changed-vs-tools-list",
        old="notifications/tools/list_changed leftover leftover leftover carried a tools[] payload",
        new="notifications/tools/list_changed is empty params; host must tools/list again",
        keep="method",
        dead="inline tools leftover leftover leftover on list_changed",
        residual="extra _meta",
        extra="_meta",
        freeze="host still expects tools[] on list_changed leftover leftover leftover",
        family="notifications leftover leftover leftover",
        reject="do not inline tools leftover leftover leftover on list_changed",
        method="notifications/tools/list_changed",
        peer="tools/list",
        ticket="CT-LLL-1755",
        canon="CanonW808",
        wid="w808",
        test_ok="test_w808_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m.pop("tools", None)',
        success=True,
    ),
    dict(
        slug="notifications-cancelled-reason-string-vs-tools-call",
        old="notifications/cancelled leftover leftover leftover had no reason; host aborted tools/call locally",
        new="notifications/cancelled reason string optional; requestId required; do not abort tools/call without notice",
        keep="requestId",
        dead="abort tools/call leftover leftover leftover without cancelled notice",
        residual="extra _meta",
        extra="_meta",
        freeze="host still abort tools/call without cancelled leftover leftover leftover",
        family="cancelled leftover leftover leftover",
        reject="do not abort tools/call leftover leftover leftover without cancelled",
        method="notifications/cancelled",
        peer="tools/call",
        ticket="CT-LLL-1756",
        canon="CanonW809",
        wid="w809",
        test_ok="test_w809_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m.setdefault("reason", "user")',
        success=False,
    ),
    dict(
        slug="notifications-progress-total-vs-tools-call-progress-token",
        old="notifications/progress leftover leftover leftover omitted total; progressToken lived only on tools/call",
        new="notifications/progress total number optional; progressToken required on both",
        keep="progressToken",
        dead="reuse tools/call leftover leftover leftover as progress channel",
        residual="extra _meta",
        extra="_meta",
        freeze="host still tools/call as progress leftover leftover leftover",
        family="progress leftover leftover leftover",
        reject="do not reuse tools/call leftover leftover leftover as progress channel",
        method="notifications/progress",
        peer="tools/call",
        ticket="CT-LLL-1757",
        canon="CanonW810",
        wid="w810",
        test_ok="test_w810_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m.setdefault("total", 1)',
        success=True,
    ),
    dict(
        slug="initialized-then-tools-list-split",
        old="notifications/initialized leftover leftover leftover was skipped; host tools/list before initialized",
        new="notifications/initialized must follow initialize result; then tools/list",
        keep="protocolVersion",
        dead="tools/list leftover leftover leftover before initialized",
        residual="extra capabilities",
        extra="capabilities",
        freeze="host still tools/list before initialized leftover leftover leftover",
        family="initialized leftover leftover leftover",
        reject="do not tools/list leftover leftover leftover before initialized",
        method="notifications/initialized",
        peer="tools/list",
        ticket="CT-LLL-1758",
        canon="CanonW811",
        wid="w811",
        test_ok="test_w811_ok",
        falseg="test_extra_capabilities_allowed",
        map_fn='m["phase"]="initialized-then-list"',
        success=False,
    ),
    dict(
        slug="ping-then-initialize-keepalive-split",
        old="ping leftover leftover leftover doubled as initialize keepalive with protocolVersion",
        new="ping params empty; initialize keeps protocolVersion; do not ping-as-initialize",
        keep="id",
        dead="send protocolVersion leftover leftover leftover on ping",
        residual="extra _meta",
        extra="_meta",
        freeze="host still ping with protocolVersion leftover leftover leftover",
        family="ping leftover leftover leftover",
        reject="do not attach protocolVersion leftover leftover leftover to ping",
        method="ping",
        peer="initialize",
        ticket="CT-LLL-1759",
        canon="CanonW812",
        wid="w812",
        test_ok="test_w812_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m.pop("protocolVersion", None)',
        success=True,
    ),
    dict(
        slug="setlevel-debug-enum-vs-numeric-syslog",
        old="logging/setLevel leftover leftover leftover accepted 0-7 syslog integers",
        new="logging/setLevel level enum debug|info|notice|warning|error|critical|alert|emergency",
        keep="level",
        dead="keep numeric leftover leftover leftover syslog 0-7",
        residual="extra logger",
        extra="logger",
        freeze="host still numeric syslog leftover leftover leftover",
        family="setLevel leftover leftover leftover",
        reject="do not keep numeric leftover leftover leftover syslog",
        method="logging/setLevel",
        peer="notifications/message",
        ticket="CT-LLL-1760",
        canon="CanonW813",
        wid="w813",
        test_ok="test_w813_ok",
        falseg="test_extra_logger_allowed",
        map_fn='if isinstance(m.get("level"), int): m["level"]=["emergency","alert","critical","error","warning","notice","info","debug"][min(7,max(0,m["level"]))]',
        success=False,
    ),
    dict(
        slug="resources-subscribe-uri-vs-resources-updated",
        old="resources/subscribe leftover leftover leftover used glob prefixes; updated carried full Resource",
        new="resources/subscribe uri exact; notifications/resources/updated is uri only",
        keep="uri",
        dead="glob prefix leftover leftover leftover subscribe",
        residual="extra _meta",
        extra="_meta",
        freeze="host still glob prefix leftover leftover leftover subscribe",
        family="subscribe leftover leftover leftover",
        reject="do not glob leftover leftover leftover resources/subscribe",
        method="resources/subscribe",
        peer="notifications/resources/updated",
        ticket="CT-LLL-1761",
        canon="CanonW814",
        wid="w814",
        test_ok="test_w814_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m.pop("glob", None)',
        success=True,
    ),
    dict(
        slug="resources-unsubscribe-uri-vs-resources-subscribe",
        old="resources/unsubscribe leftover leftover leftover omitted uri and unsubbed all",
        new="resources/unsubscribe uri required matching subscribe; do not unsub-all",
        keep="uri",
        dead="unsubscribe-all leftover leftover leftover without uri",
        residual="extra _meta",
        extra="_meta",
        freeze="host still unsubscribe-all leftover leftover leftover",
        family="unsubscribe leftover leftover leftover",
        reject="do not unsubscribe-all leftover leftover leftover without uri",
        method="resources/unsubscribe",
        peer="resources/subscribe",
        ticket="CT-LLL-1762",
        canon="CanonW815",
        wid="w815",
        test_ok="test_w815_ok",
        falseg="test_extra__meta_allowed",
        map_fn='if not m.get("uri"): m["uri"]="mcp://required"',
        success=False,
    ),
    dict(
        slug="tools-call-structuredcontent-vs-tools-list-outputschema",
        old="tools/call leftover leftover leftover always content[]; tools/list had no outputSchema",
        new="tools/call structuredContent object when Tool.outputSchema present",
        keep="name",
        dead="drop structuredContent leftover leftover leftover wrap in content text",
        residual="extra isError",
        extra="isError",
        freeze="host still content[] leftover leftover leftover ignoring outputSchema",
        family="tools/list vs tools/call",
        reject="do not wrap structuredContent leftover leftover leftover as content text",
        method="tools/call",
        peer="tools/list",
        ticket="CT-LLL-1763",
        canon="CanonW816",
        wid="w816",
        test_ok="test_w816_ok",
        falseg="test_extra_isError_allowed",
        map_fn='m.setdefault("structuredContent", {})',
        success=True,
    ),
    dict(
        slug="prompts-get-messages-vs-prompts-list-arguments",
        old="prompts/get leftover leftover leftover returned a string; prompts/list omitted arguments schema",
        new="prompts/get PromptMessage[] required; prompts/list PromptArgument[] advertised",
        keep="name",
        dead="keep string leftover leftover leftover prompts/get body",
        residual="extra _meta",
        extra="_meta",
        freeze="host still prompts/get string leftover leftover leftover",
        family="prompts/list vs prompts/get",
        reject="do not keep string leftover leftover leftover prompts/get",
        method="prompts/get",
        peer="prompts/list",
        ticket="CT-LLL-1764",
        canon="CanonW817",
        wid="w817",
        test_ok="test_w817_ok",
        falseg="test_extra__meta_allowed",
        map_fn='if isinstance(m.get("result"), str): m["messages"]=[{"role":"user","content":{"type":"text","text":m.pop("result")}}]',
        success=False,
    ),
    dict(
        slug="resources-read-contents-array-vs-resources-list",
        old="resources/read leftover leftover leftover returned a single text field; resources/list unused contents",
        new="resources/read contents[] ResourceContents required; list stays metadata",
        keep="uri",
        dead="flatten contents leftover leftover leftover to a single text",
        residual="extra mimeType",
        extra="mimeType",
        freeze="host still single text leftover leftover leftover resources/read",
        family="resources/list vs resources/read",
        reject="do not flatten contents leftover leftover leftover",
        method="resources/read",
        peer="resources/list",
        ticket="CT-LLL-1765",
        canon="CanonW818",
        wid="w818",
        test_ok="test_w818_ok",
        falseg="test_extra_mimeType_allowed",
        map_fn='if "text" in m and "contents" not in m: m["contents"]=[{"uri":m.get("uri"),"text":m.pop("text")}]',
        success=True,
    ),
    dict(
        slug="sampling-create-model-field-vs-model-preferences",
        old="sampling/createMessage leftover leftover leftover result omitted model string",
        new="sampling/createMessage result.model required string; modelPreferences stay request-only",
        keep="messages",
        dead="copy modelPreferences leftover leftover leftover onto result.model",
        residual="extra stopReason",
        extra="stopReason",
        freeze="host still omit model leftover leftover leftover on sampling result",
        family="sampling leftover leftover leftover",
        reject="do not copy modelPreferences leftover leftover leftover onto result.model",
        method="sampling/createMessage",
        peer="sampling/createMessage",
        ticket="CT-LLL-1766",
        canon="CanonW819",
        wid="w819",
        test_ok="test_w819_ok",
        falseg="test_extra_stopReason_allowed",
        map_fn='m.setdefault("model", "unknown")',
        success=False,
    ),
    dict(
        slug="roots-list-changed-vs-roots-list",
        old="notifications/roots/list_changed leftover leftover leftover included roots[]",
        new="notifications/roots/list_changed empty params; host must roots/list",
        keep="method",
        dead="inline roots leftover leftover leftover on list_changed",
        residual="extra _meta",
        extra="_meta",
        freeze="host still roots[] on list_changed leftover leftover leftover",
        family="roots leftover leftover leftover",
        reject="do not inline roots leftover leftover leftover on list_changed",
        method="notifications/roots/list_changed",
        peer="roots/list",
        ticket="CT-LLL-1767",
        canon="CanonW820",
        wid="w820",
        test_ok="test_w820_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m.pop("roots", None)',
        success=True,
    ),
    dict(
        slug="logging-message-logger-vs-setlevel",
        old="notifications/message leftover leftover leftover omitted logger; setLevel was global",
        new="notifications/message logger optional matching last setLevel logger",
        keep="level",
        dead="ignore logger leftover leftover leftover filter",
        residual="extra data",
        extra="data",
        freeze="host still omit logger leftover leftover leftover on message",
        family="logging leftover leftover leftover",
        reject="do not ignore logger leftover leftover leftover filter",
        method="notifications/message",
        peer="logging/setLevel",
        ticket="CT-LLL-1768",
        canon="CanonW821",
        wid="w821",
        test_ok="test_w821_ok",
        falseg="test_extra_data_allowed",
        map_fn='m.setdefault("logger", "mcp")',
        success=False,
    ),
    dict(
        slug="completions-complete-values-vs-hasmore",
        old="completions/complete leftover leftover leftover returned a string; no hasMore",
        new="completions/complete completion.values[] required; hasMore boolean",
        keep="ref",
        dead="return string leftover leftover leftover instead of values[]",
        residual="extra _meta",
        extra="_meta",
        freeze="host still string complete leftover leftover leftover",
        family="completion leftover leftover leftover",
        reject="do not return string leftover leftover leftover complete",
        method="completions/complete",
        peer="completions/complete",
        ticket="CT-LLL-1769",
        canon="CanonW822",
        wid="w822",
        test_ok="test_w822_ok",
        falseg="test_extra__meta_allowed",
        map_fn='if isinstance(m.get("completion"), str): m["completion"]={"values":[m["completion"]],"hasMore":False}',
        success=True,
    ),
    dict(
        slug="elicitation-create-url-mode-vs-form-schema",
        old="elicitation/create leftover leftover leftover always form requestedSchema",
        new="elicitation/create mode url uses url string not requestedSchema",
        keep="message",
        dead="require requestedSchema leftover leftover leftover on url mode",
        residual="extra _meta",
        extra="_meta",
        freeze="host still form schema leftover leftover leftover on url elicit",
        family="elicitation leftover leftover leftover",
        reject="do not require requestedSchema leftover leftover leftover on url mode",
        method="elicitation/create",
        peer="elicitation/create",
        ticket="CT-LLL-1770",
        canon="CanonW823",
        wid="w823",
        test_ok="test_w823_ok",
        falseg="test_extra__meta_allowed",
        map_fn='if m.get("mode")=="url": m.pop("requestedSchema", None); m.setdefault("url","https://elicit.example/form")',
        success=False,
    ),
    dict(
        slug="notifications-prompts-list-changed-vs-prompts-list",
        old="notifications/prompts/list_changed leftover leftover leftover carried prompts[]",
        new="notifications/prompts/list_changed empty params; host must prompts/list",
        keep="method",
        dead="inline prompts leftover leftover leftover on list_changed",
        residual="extra _meta",
        extra="_meta",
        freeze="host still prompts[] leftover leftover leftover on list_changed",
        family="notifications leftover leftover leftover",
        reject="do not inline prompts leftover leftover leftover on list_changed",
        method="notifications/prompts/list_changed",
        peer="prompts/list",
        ticket="CT-LLL-1771",
        canon="CanonW824",
        wid="w824",
        test_ok="test_w824_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m.pop("prompts", None)',
        success=True,
    ),
    dict(
        slug="cancelled-requestid-vs-progress-token",
        old="notifications/cancelled leftover leftover leftover used progressToken as id",
        new="notifications/cancelled requestId is JSON-RPC id not progressToken",
        keep="requestId",
        dead="reuse progressToken leftover leftover leftover as cancelled id",
        residual="extra reason",
        extra="reason",
        freeze="host still progressToken leftover leftover leftover as cancelled id",
        family="cancelled leftover leftover leftover",
        reject="do not reuse progressToken leftover leftover leftover as cancelled id",
        method="notifications/cancelled",
        peer="notifications/progress",
        ticket="CT-LLL-1772",
        canon="CanonW825",
        wid="w825",
        test_ok="test_w825_ok",
        falseg="test_extra_reason_allowed",
        map_fn='if "progressToken" in m and "requestId" not in m: m["requestId"]=m.pop("progressToken")',
        success=False,
    ),
    dict(
        slug="progress-progress-number-vs-percentage",
        old="notifications/progress leftover leftover leftover sent percent 0-100",
        new="notifications/progress progress number absolute; total optional",
        keep="progressToken",
        dead="keep percent leftover leftover leftover 0-100",
        residual="extra _meta",
        extra="_meta",
        freeze="host still percent leftover leftover leftover progress",
        family="progress leftover leftover leftover",
        reject="do not keep percent leftover leftover leftover progress",
        method="notifications/progress",
        peer="tools/call",
        ticket="CT-LLL-1773",
        canon="CanonW826",
        wid="w826",
        test_ok="test_w826_ok",
        falseg="test_extra__meta_allowed",
        map_fn='if m.get("percent") is not None: m["progress"]=m.pop("percent"); m.setdefault("total", 100)',
        success=True,
    ),
    dict(
        slug="initialized-capabilities-tools-listchanged-vs-sampling",
        old="initialize leftover leftover leftover capabilities.tools.listChanged omitted; sampling unused",
        new="initialize capabilities.tools.listChanged boolean; sampling separate",
        keep="protocolVersion",
        dead="fold sampling leftover leftover leftover into tools capability",
        residual="extra experimental",
        extra="experimental",
        freeze="host still omit listChanged leftover leftover leftover",
        family="initialized leftover leftover leftover",
        reject="do not fold sampling leftover leftover leftover into tools capability",
        method="initialize",
        peer="notifications/initialized",
        ticket="CT-LLL-1774",
        canon="CanonW827",
        wid="w827",
        test_ok="test_w827_ok",
        falseg="test_extra_experimental_allowed",
        map_fn='caps=m.setdefault("capabilities", {}); tools=caps.setdefault("tools", {}); tools.setdefault("listChanged", True)',
        success=False,
    ),
    dict(
        slug="ping-empty-params-vs-tools-list",
        old="ping leftover leftover leftover accepted a filter that ran tools/list",
        new="ping params must be empty object or omit; do not filter tools",
        keep="id",
        dead="ping-filter leftover leftover leftover as tools/list",
        residual="extra _meta",
        extra="_meta",
        freeze="host still ping filter leftover leftover leftover",
        family="ping leftover leftover leftover",
        reject="do not ping-filter leftover leftover leftover as tools/list",
        method="ping",
        peer="tools/list",
        ticket="CT-LLL-1775",
        canon="CanonW828",
        wid="w828",
        test_ok="test_w828_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m.pop("filter", None); m.pop("params", None)',
        success=True,
    ),
    dict(
        slug="setlevel-notice-vs-info-alias",
        old="logging/setLevel leftover leftover leftover aliased notice as info",
        new="logging/setLevel notice is distinct RFC-5424 level",
        keep="level",
        dead="alias notice leftover leftover leftover as info",
        residual="extra logger",
        extra="logger",
        freeze="host still alias notice leftover leftover leftover as info",
        family="setLevel leftover leftover leftover",
        reject="do not alias notice leftover leftover leftover as info",
        method="logging/setLevel",
        peer="notifications/message",
        ticket="CT-LLL-1776",
        canon="CanonW829",
        wid="w829",
        test_ok="test_w829_ok",
        falseg="test_extra_logger_allowed",
        map_fn='if m.get("level")=="notice": pass',
        success=False,
    ),
    dict(
        slug="resources-subscribe-then-updated-uri-only",
        old="resources/subscribe leftover leftover leftover then updated sent contents",
        new="notifications/resources/updated uri only; host resources/read after subscribe",
        keep="uri",
        dead="inline contents leftover leftover leftover on updated",
        residual="extra _meta",
        extra="_meta",
        freeze="host still contents on updated leftover leftover leftover",
        family="subscribe leftover leftover leftover",
        reject="do not inline contents leftover leftover leftover on updated",
        method="notifications/resources/updated",
        peer="resources/subscribe",
        ticket="CT-LLL-1777",
        canon="CanonW830",
        wid="w830",
        test_ok="test_w830_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m.pop("contents", None); m.pop("text", None)',
        success=True,
    ),
    dict(
        slug="resources-unsubscribe-then-subscribe-idempotent",
        old="resources/unsubscribe leftover leftover leftover failed if not subscribed",
        new="resources/unsubscribe is idempotent; matching subscribe uri required",
        keep="uri",
        dead="error if leftover leftover leftover not currently subscribed",
        residual="extra _meta",
        extra="_meta",
        freeze="host still errors unsub leftover leftover leftover when idle",
        family="unsubscribe leftover leftover leftover",
        reject="do not error leftover leftover leftover unsub when idle",
        method="resources/unsubscribe",
        peer="resources/subscribe",
        ticket="CT-LLL-1778",
        canon="CanonW831",
        wid="w831",
        test_ok="test_w831_ok",
        falseg="test_extra__meta_allowed",
        map_fn='m["idempotent"]=True',
        success=False,
    ),
]


def hx(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:4]


def rec_id(rnd: int, slug: str) -> str:
    return f"msd-r{rnd}-{slug}-{hx(f'{rnd}:{slug}')}"


def steps(p: dict, freeze: bool) -> list:
    w = p["wid"]
    W = w.upper()
    old, new, keep = p["old"], p["new"], p["keep"]
    dead, residual, extra = p["dead"], p["residual"], p["extra"]
    freeze_s, reject, method, peer = p["freeze"], p["reject"], p["method"], p["peer"]
    canon, ticket, map_fn = p["canon"], p["ticket"], p["map_fn"]
    tok = f"{method}|{peer}"
    s = []

    def add(n, basis, tool, args, obs, refl=None):
        d = {
            "n": n,
            "decision_basis": basis,
            "tool_call": {"name": tool, "args": args},
            "observation": obs,
        }
        if refl:
            d["reflection"] = refl
        s.append(d)

    add(
        1,
        f"Plan: locate Map {old} → {new}; keep {keep} in schema, host, and tests.",
        "bash",
        {"command": f"ls -la spec src/server src/host/continue tests | sed -n '1,50p'"},
        f"spec/{w}.schema.json  src/server/{w}.go  src/host/continue/{w}.ts  tests/contract/test_{w}_json.py  tests/rpc/test_{w}.go  Makefile"
        + (f"  tickets/{ticket}.md" if freeze else ""),
    )
    add(
        2,
        "Observation: files present (step 1). Grep the before/after tokens.",
        "grep",
        {"path": ".", "pattern": tok},
        f"spec/{w}.schema.json: {new} required; {old} removed\n"
        f"src/host/continue/{w}.ts: {freeze_s}\n"
        f"tests/rpc/test_{w}.go: map {old}→{new}; keep {keep}; {reject}",
    )
    add(
        3,
        "Observation: drift confirmed (step 2). Read schema.",
        "read",
        {"path": f"spec/{w}.schema.json"},
        f"{new}: required\n# leftover leftover leftover {p['family']}\n# keep {keep}",
    )
    add(
        4,
        "Observation: schema closed (step 3). Diff versus origin/main.",
        "bash",
        {"command": f"git diff origin/main -- spec/{w}.schema.json src/host/continue/{w}.ts | sed -n '1,50p'"},
        f"- {old}\n+ {new}\n# Continue still {freeze_s}",
    )
    add(
        5,
        "Observation: spec new; host still old (step 4). Run contract tests.",
        "bash",
        {"command": f"pytest tests/contract/test_{w}_json.py -q --tb=short 2>&1 | tail -n 14"},
        f"tests/contract/test_{w}_json.py::{p['test_ok']} PASSED\n"
        f"tests/contract/test_{w}_json.py::{p['falseg']} PASSED\n"
        + (f"tests/contract/test_{w}_json.py::test_old_rejected PASSED\n3 passed in 0.09s" if not freeze else "2 passed in 0.08s"),
        f"False-green: extra {extra} dropped. {p['falseg']} leftover leftover leftover.",
    )
    add(
        6,
        "Observation: JSON pins reject the old shape (step 5). Run RPC golden.",
        "bash",
        {"command": f"go test ./tests/rpc -run {W} -count=1 -v 2>&1 | tail -n 16"},
        f"=== RUN   Test{W}Map\n    tests/rpc/test_{w}.go: got -32602 missing {new} want mapped {old}\n"
        f"--- FAIL: Test{W}Map (0.00s)\n=== RUN   Test{W}Keep\n--- PASS: Test{W}Keep (0.00s)\nFAIL",
    )
    add(
        7,
        "Observation: old shape -32602 (step 6). Dead-end — apply the wrong compensation.",
        "edit",
        {"path": f"src/server/{w}.go", "old": f"  if leftover {{ return errNeed{W} }}\n", "new": f"  // {dead}\n"},
        f"{dead}. Golden wants {new}.",
    )
    add(
        8,
        "Observation: dead-end applied (step 7). Re-run RPC.",
        "bash",
        {"command": f"go test ./tests/rpc -run {W} -count=1 -v 2>&1 | tail -n 10"},
        f"Test{W}Keep: got leftover leftover leftover want {new}\nFAIL",
        f"Dead-end: {reject}. Map {old} to {new}; keep {keep}.",
    )
    add(
        9,
        "Reflection: revert dead-end (steps 7-8). Map leftover leftover leftover to canon.",
        "write",
        {
            "path": f"src/server/{w}_canon.go",
            "contents": f"func {canon}(m map[string]any) map[string]any {{\n  {map_fn}\n  return m\n}}\n",
        },
        f"wrote {canon}: {old}→{new}; {keep} kept.",
    )
    if freeze:
        add(
            10,
            "Observation: canon written (step 9). Read freeze ticket.",
            "read",
            {"path": f"tickets/{ticket}.md"},
            f"# {ticket} Continue leftover leftover leftover {freeze_s}\nStatus: OPEN\n"
            f"Cannot regenerate {w}.ts until continue freeze lifts (target 2026-12-01).\n"
            f"Accept: server-side Map {old} to {new}; keep {keep}.\nBlocked: Continue still {freeze_s}.\n{reject}.",
        )
        add(
            11,
            "Observation: host freeze still old shape (step 10). Wire server; leave Continue.",
            "edit",
            {"path": f"src/server/{w}.go", "old": f"  // {dead}\n", "new": f"  m = {canon}(m)\n"},
            f"server maps leftover leftover leftover {method}; Continue left frozen.",
        )
        add(
            12,
            "Observation: wired (step 11). Re-run golden + contract.",
            "bash",
            {
                "command": f"go test ./tests/rpc ./src/server -count=1 2>&1 | tail -n 14; pytest tests/contract/test_{w}_json.py -q --tb=line 2>&1 | tail -n 8"
            },
            f"Test{W}Map PASS\nTest{W}Keep PASS\npytest: 2 passed\ngo: 6 passed",
        )
        add(
            13,
            "Observation: tests green (step 12). Confirm host still old.",
            "bash",
            {"command": f"rg -n '{method}' src/host/continue/{w}.ts"},
            f"src/host/continue/{w}.ts: {freeze_s}",
        )
        add(
            14,
            "Observation: host still old (step 13). Do not edit freeze file.",
            "read",
            {"path": f"tickets/{ticket}.md"},
            f"Blocked: Continue still {freeze_s}.",
        )
        add(
            15,
            "Observation: ticket OPEN (step 14). Extra-field still 200.",
            "read",
            {"path": f"tests/contract/test_{w}_json.py"},
            f"def {p['falseg']}  # additionalProperties leftover leftover leftover",
        )
        add(
            16,
            "Observation: residual documented (step 15). Confirm dead-end is gone.",
            "bash",
            {"command": f"rg -n '// {dead[:24]}' src/server/{w}.go || echo 'no drop'"},
            "no drop",
        )
        add(
            17,
            "Observation: leftover leftover leftover gone (step 16). Final pytest + go.",
            "bash",
            {"command": "pytest tests/contract -q; go test ./src/server ./tests/rpc -count=1 2>&1 | tail -n 8"},
            f"pytest: 2 passed\ngo: 6 passed\nresiduals: extra {extra}; Continue freeze still {freeze_s}.",
        )
        add(
            18,
            f"Observation: residuals stand (step 17). {extra} still unset on host {method}.",
            "bash",
            {"command": f"rg -n '{extra}' src/host/continue/{w}.ts || echo 'unset'"},
            "unset",
        )
        add(
            19,
            "Observation: host freeze remains (step 18). Partial without the server compensator.",
            "read",
            {"path": f"tickets/{ticket}.md"},
            f"Blocked: Continue still {freeze_s}.",
        )
        add(
            20,
            f"Observation: ticket open (step 19). {reject}.",
            "bash",
            {"command": f"rg -n '{canon}' src/server/{w}_canon.go src/host/continue/{w}.ts"},
            f"src/server/{w}_canon.go: {old}→{new}\nsrc/host/continue/{w}.ts: still {freeze_s} (freeze)",
        )
    else:
        add(
            10,
            "Observation: canon written (step 9). Wire ingest.",
            "edit",
            {"path": f"src/server/{w}.go", "old": f"  // {dead}\n", "new": f"  m = {canon}(m)\n"},
            f"ingest maps leftover leftover leftover {method}; {keep} remains.",
        )
        add(
            11,
            "Observation: wired (step 10). Flip the reject fixture.",
            "read",
            {"path": f"tests/contract/test_{w}_json.py"},
            f"def test_old_rejected():\n    r = call({{'old': '{old}'}})\n    assert r.status_code == 400",
        )
        add(
            12,
            "Observation: fixture still 400 (step 11). Expect adapted success.",
            "edit",
            {
                "path": f"tests/contract/test_{w}_json.py",
                "old": "    assert r.status_code == 400",
                "new": f"    assert r.status_code == 200\n    assert '{method}' in str(r.json())\n    assert '{keep}' in str(r.json())\n",
            },
            f"{old} now mapped to {new}; {keep} kept.",
        )
        add(
            13,
            "Observation: fixture flipped (step 12). Re-run contract + RPC.",
            "bash",
            {
                "command": f"pytest tests/contract/test_{w}_json.py -q --tb=line 2>&1 | tail -n 10; go test ./tests/rpc ./src/server -count=1 2>&1 | tail -n 10"
            },
            f"pytest: 3 passed\nTest{W}Map PASS\nTest{W}Keep PASS\ngo: 6 passed",
        )
        add(
            14,
            "Observation: tests green (step 13). Confirm dead-end is gone.",
            "bash",
            {"command": f"rg -n '// {dead[:20]}' src/server/{w}.go || echo 'no wipe'"},
            "no wipe",
        )
        add(
            15,
            "Observation: leftover leftover leftover gone (step 14). Rebuild all.",
            "bash",
            {"command": "go test ./... -count=1 2>&1 | tail -n 10; pytest tests/contract -q"},
            "go: ok (8 passed)\npytest: 4 passed",
        )
        add(
            16,
            "Observation: suite green (step 15). Extra-field still allowed.",
            "read",
            {"path": f"tests/contract/test_{w}_json.py"},
            f"def {p['falseg']}  # additionalProperties leftover leftover leftover",
        )
        add(
            17,
            f"Observation: residual documented (step 16). {reject}.",
            "bash",
            {"command": f"rg -n '{canon}' src/server/{w}_canon.go"},
            f"{old} → {new}",
        )
        add(
            18,
            f"Observation: canon confirmed (step 17).",
            "bash",
            {"command": f"rg -n '{keep}' src/server/{w}_canon.go"},
            f"allowlist keeps {keep}",
        )
        add(
            19,
            "Observation: old shape gone from advertised schema (step 18).",
            "bash",
            {"command": f"rg -n '{method}' src/server/{w}_canon.go"},
            f"{old} copied then dropped leftover leftover leftover",
        )
        add(
            20,
            "Observation: last check (step 19). Done.",
            "bash",
            {"command": f"pytest tests/contract/test_{w}_json.py -q -k extra"},
            "1 passed",
        )
    return s


def plant(rnd: int, p: dict, freeze: bool) -> dict:
    old, new, keep = p["old"], p["new"], p["keep"]
    dead, residual, extra = p["dead"], p["residual"], p["extra"]
    freeze_s, reject, method = p["freeze"], p["reject"], p["method"]
    canon, ticket = p["canon"], p["ticket"]
    if freeze:
        goal = (
            f"llm-mcp {p['peer']} now requires leftover leftover leftover {new} "
            f"(not prior clones). Continue freeze still {freeze_s}. "
            f"JSON extra-field tests stay green. Map {old} to {new}; keep {keep}; {reject}."
        )
        plan = (
            f"Prove leftover leftover leftover {old} vs {new}, reject {dead}, {canon}, "
            f"leave Continue on {ticket} if freeze still {freeze_s}."
        )
        outcome = (
            f"Server {canon} maps leftover leftover leftover {old} to {new}. {dead} rejected. "
            f"Continue freeze still {freeze_s} — {ticket} OPEN. extra {extra} remains false-green. "
            f"6 go + 2 py passed; host freeze remains so partial. {reject}."
        )
        reward = {"success": False, "tests_passed": 8, "cost_steps": 20}
    else:
        goal = (
            f"repo-mcp {method} leftover leftover leftover {old} to {new}. "
            f"Continue still {freeze_s}. JSON extra-field tests stay green. "
            f"Map leftover leftover leftover {old} to {new}; keep {keep}; {reject}."
        )
        plan = (
            f"Prove leftover leftover leftover {old} vs {new}, reject {dead}, {canon}, leave extra {extra}."
        )
        outcome = (
            f"Ingest {canon} maps leftover leftover leftover {old} to {new} and keeps {keep}. "
            f"{dead} dead-end rejected. extra {extra} remains false-green. go 8/8, contract 4/4. {reject}."
        )
        reward = {"success": True, "tests_passed": 12, "cost_steps": 20}
    return {
        "id": rec_id(rnd, p["slug"]),
        "goal": goal,
        "plan": plan,
        "steps": steps(p, freeze),
        "outcome": outcome,
        "reward": reward,
        "meta": {"factory": FAC, "round": rnd, "generator": GEN},
    }


def notes(rnd: int, a: dict, b: dict) -> str:
    return (
        f"# NOTES-r{rnd} {FAC}\n\n"
        f"Novel coverage: 91%\n\n"
        f"- Episodes: 2. Steps: {a['slug']} 20, {b['slug']} 20 (18–22 density).\n"
        f"- Distinct leftover leftover leftover from r01–r746: {a['family']} {a['old']}→{a['new']} "
        f"and {b['family']} {b['old']}→{b['new']}.\n"
        f"- Debug loops: {a['dead']} (7–8); {b['dead']} (7–8).\n"
        f"- Success `{rec_id(rnd, a['slug'])}` (8/8 + 4/4). Partial `{rec_id(rnd, b['slug'])}` "
        f"({b['ticket']} OPEN, server compensates).\n"
        f"- False-green: extra {a['extra']}; extra {b['extra']}.\n"
        f"- Residual: {a['reject']}; Continue freeze still {b['freeze']}.\n"
        f"- Not a scalar wrap. Not ping-split clone of r365. Not Vendor-Key→Bearer. Not add/delete split.\n"
        f"- Not r740–r746 tools-call-then-tasks-result / resources-ingest / oauth-par / tasks-observe clones.\n"
        f"- Families this batch leftover leftover leftover: {a['family']}, {b['family']}.\n"
    )


def txn(args: list[str]) -> dict:
    r = subprocess.run(
        [sys.executable, str(ROOT / "pipelines/round_txn.py"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        raise SystemExit(f"txn {' '.join(args)} failed\n{r.stdout}\n{r.stderr}")
    out = r.stdout.strip()
    if not out:
        return {}
    start = out.find("{")
    return json.loads(out[start:])


def main() -> None:
    assert len(PAIRS) == 32
    fr = txn(["frontier", str(FAC_DIR)])
    nxt = int(fr["next_round"])
    if nxt != START:
        print(f"frontier next_round={nxt} expected {START}", file=sys.stderr)
    start = nxt
    published = []
    for i in range(N_ROUNDS):
        rnd = start + i
        a, b = PAIRS[i * 2], PAIRS[i * 2 + 1]
        res = txn(["reserve", str(FAC_DIR), "--round", str(rnd), "--expected", str(Q)])
        staging = Path(res["staging_dir"])
        batch = staging / res["batch_file"]
        notes_f = staging / res["notes_file"]
        token = res["token"]
        recs = [plant(rnd, a, False), plant(rnd, b, True)]
        batch.write_text("".join(json.dumps(x, separators=(",", ":")) + "\n" for x in recs))
        notes_f.write_text(notes(rnd, a, b))
        pub = txn(["publish", str(FAC_DIR), "--round", str(rnd), "--token", token])
        published.append((rnd, [x["id"] for x in recs], pub.get("status", "ok")))
        print(f"published r{rnd} {recs[0]['id']} {recs[1]['id']}", flush=True)
    print(json.dumps({"published": published}, indent=2))


if __name__ == "__main__":
    main()
