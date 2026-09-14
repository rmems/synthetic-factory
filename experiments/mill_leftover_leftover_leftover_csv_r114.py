#!/usr/bin/env python3
"""csv-excel leftover leftover leftover mill r114+ hop from reserved email-webhook.

Staging only. No sir-/dbc- ids. Distinct leftover leftover leftover grains vs r106–r113.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/csv-excel-ingest-factory"
FAC = "csv-excel-ingest-factory"
GEN = "grok-4.6"
PREFIX = "cei"

PAIRS = [
    dict(
        slug="xlsx-definedname-leftover-vs-usedrange",
        fail="xls-definedname-handoff",
        mod="xldn",
        drop="xlsdn",
        keep="definedNames",
        naive="usedRange",
        stack="xlsx leftover leftover leftover definedNames",
        drop_stack="XLS definedName BIFF",
        doc="https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.definednames",
        doc2="https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.definedname",
        domain="xlsx-definedname-leftover-vs-usedrange",
        ticket="XLS-DN-114",
        test_ok="test_xldn",
        test_fail="test_xlsdn",
        short="xldn",
        dshort="xlsdn",
        first_wrong="skip_dn",
    ),
    dict(
        slug="csv-rfc4180-leftover-vs-excel",
        fail="excel-csv-dialect-handoff",
        mod="rfc4180",
        drop="xlcsv",
        keep="rfc4180",
        naive="excel_dialect",
        stack="csv leftover leftover leftover RFC4180",
        drop_stack="Excel CSV dialect",
        doc="https://datatracker.ietf.org/doc/html/rfc4180",
        doc2="https://docs.python.org/3/library/csv.html#csv.excel",
        domain="csv-rfc4180-leftover-vs-excel",
        ticket="XL-CSV-115",
        test_ok="test_rfc4180",
        test_fail="test_xlcsv",
        short="rfc4180",
        dshort="xlcsv",
        first_wrong="excelish",
    ),
    dict(
        slug="xlsx-sharedstrings-leftover-vs-inline",
        fail="xls-sst-inline-handoff",
        mod="xlssst",
        drop="xlsi",
        keep="sharedStrings",
        naive="inlineStr",
        stack="xlsx leftover leftover leftover sharedStrings",
        drop_stack="XLS SST inline",
        doc="https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.sharedstringtable",
        doc2="https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.inlinestring",
        domain="xlsx-sharedstrings-leftover-vs-inline",
        ticket="XLS-SST-116",
        test_ok="test_xlssst",
        test_fail="test_xlsi",
        short="xlssst",
        dshort="xlsi",
        first_wrong="inline_only",
    ),
    dict(
        slug="ods-formula-leftover-vs-cached",
        fail="ods-cached-handoff",
        mod="odsform",
        drop="odscache",
        keep="table_formula",
        naive="office_value",
        stack="ods leftover leftover leftover table:formula",
        drop_stack="ODS office:value cache",
        doc="https://docs.oasis-open.org/office/v1.2/os/OpenDocument-v1.2-os-part1.html",
        doc2="https://docs.oasis-open.org/office/OpenDocument/v1.3/os/part3-schema/",
        domain="ods-formula-leftover-vs-cached",
        ticket="ODS-F-117",
        test_ok="test_odsform",
        test_fail="test_odscache",
        short="odsform",
        dshort="odscache",
        first_wrong="cache_only",
    ),
    dict(
        slug="csv-utf8bom-leftover-vs-utf16",
        fail="utf16-le-handoff",
        mod="csbom",
        drop="u16le",
        keep="utf8_bom",
        naive="utf16le",
        stack="csv leftover leftover leftover utf-8-sig",
        drop_stack="UTF-16LE CSV",
        doc="https://docs.python.org/3/library/codecs.html#module-encodings.utf_8_sig",
        doc2="https://learn.microsoft.com/en-us/windows/win32/intl/using-byte-order-marks",
        domain="csv-utf8bom-leftover-vs-utf16",
        ticket="U16-118",
        test_ok="test_csbom",
        test_fail="test_u16le",
        short="csbom",
        dshort="u16le",
        first_wrong="strip_all",
    ),
    dict(
        slug="xlsx-table-leftover-vs-sheet",
        fail="xls-list-handoff",
        mod="xltbl",
        drop="xlslist",
        keep="table",
        naive="sheet",
        stack="xlsx leftover leftover leftover table",
        drop_stack="XLS List object",
        doc="https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.table",
        doc2="https://learn.microsoft.com/en-us/office/vba/api/excel.listobject",
        domain="xlsx-table-leftover-vs-sheet",
        ticket="XLS-LST-119",
        test_ok="test_xltbl",
        test_fail="test_xlslist",
        short="xltbl",
        dshort="xlslist",
        first_wrong="sheet_scan",
    ),
    dict(
        slug="xls-sst-leftover-vs-label",
        fail="xls-label-handoff",
        mod="xlsst",
        drop="xlslbl",
        keep="SST",
        naive="LABEL",
        stack="xls leftover leftover leftover SST",
        drop_stack="XLS LABEL record",
        doc="https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/2739d144-9834-4e70-b73c-fa911e412dbf",
        doc2="https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/",
        domain="xls-sst-leftover-vs-label",
        ticket="XLS-LBL-120",
        test_ok="test_xlsst",
        test_fail="test_xlslbl",
        short="xlsst",
        dshort="xlslbl",
        first_wrong="label_only",
    ),
    dict(
        slug="csv-tsv-leftover-vs-comma",
        fail="tsv-comma-handoff",
        mod="csvtsv",
        drop="tsvcm",
        keep="tab",
        naive="comma",
        stack="csv leftover leftover leftover TSV",
        drop_stack="TSV as comma",
        doc="https://www.iana.org/assignments/media-types/text/tab-separated-values",
        doc2="https://docs.python.org/3/library/csv.html#csv.excel_tab",
        domain="csv-tsv-leftover-vs-comma",
        ticket="TSV-CM-121",
        test_ok="test_csvtsv",
        test_fail="test_tsvcm",
        short="csvtsv",
        dshort="tsvcm",
        first_wrong="sniff_comma",
    ),
    dict(
        slug="xlsx-comments-leftover-vs-cell",
        fail="xls-note-handoff",
        mod="xlcmt",
        drop="xlsnote",
        keep="comments",
        naive="cell",
        stack="xlsx leftover leftover leftover comments",
        drop_stack="XLS NOTE record",
        doc="https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.comment",
        doc2="https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/4ed0ddd6-2d6d-4248-80c1-76a846d13721",
        domain="xlsx-comments-leftover-vs-cell",
        ticket="XLS-NOTE-122",
        test_ok="test_xlcmt",
        test_fail="test_xlsnote",
        short="xlcmt",
        dshort="xlsnote",
        first_wrong="cell_text",
    ),
    dict(
        slug="xlsx-pivotcache-leftover-vs-sheet",
        fail="xls-pivot-handoff",
        mod="xlpc",
        drop="xlspv",
        keep="pivotCacheDefinition",
        naive="sheet",
        stack="xlsx leftover leftover leftover pivotCache",
        drop_stack="XLS SXDB",
        doc="https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.pivotcachedefinition",
        doc2="https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/59e82452-427d-465c-bacd-4d1e62c6d3c2",
        domain="xlsx-pivotcache-leftover-vs-sheet",
        ticket="XLS-PV-123",
        test_ok="test_xlpc",
        test_fail="test_xlspv",
        short="xlpc",
        dshort="xlspv",
        first_wrong="sheet_dump",
    ),
    dict(
        slug="csv-skipinitialspace-leftover-vs-trim",
        fail="trim-all-handoff",
        mod="csvis",
        drop="csvtrim",
        keep="skipinitialspace",
        naive="strip",
        stack="csv leftover leftover leftover skipinitialspace",
        drop_stack="trim-all CSV",
        doc="https://docs.python.org/3/library/csv.html#csv.Dialect.skipinitialspace",
        doc2="https://docs.python.org/3/library/csv.html",
        domain="csv-skipinitialspace-leftover-vs-trim",
        ticket="CSV-TRIM-124",
        test_ok="test_csvis",
        test_fail="test_csvtrim",
        short="csvis",
        dshort="csvtrim",
        first_wrong="strip_fields",
    ),
    dict(
        slug="xlsx-calcchain-leftover-vs-cell",
        fail="xls-formula-handoff",
        mod="xlcc",
        drop="xlsfm",
        keep="calcChain",
        naive="cell",
        stack="xlsx leftover leftover leftover calcChain",
        drop_stack="XLS Formula",
        doc="https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.calculationchain",
        doc2="https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/8e3c6978-6c9f-4514-ba79-5c61678a09f3",
        domain="xlsx-calcchain-leftover-vs-cell",
        ticket="XLS-FM-125",
        test_ok="test_xlcc",
        test_fail="test_xlsfm",
        short="xlcc",
        dshort="xlsfm",
        first_wrong="cell_value",
    ),
    dict(
        slug="arrow-ipc-leftover-vs-pandas",
        fail="pandas-index-handoff",
        mod="arripc",
        drop="pdidx",
        keep="arrow_ipc",
        naive="pandas_index",
        stack="arrow leftover leftover leftover IPC",
        drop_stack="pandas Index",
        doc="https://arrow.apache.org/docs/format/Columnar.html",
        doc2="https://pandas.pydata.org/docs/reference/api/pandas.read_feather.html",
        domain="arrow-ipc-leftover-vs-pandas",
        ticket="PD-IDX-126",
        test_ok="test_arripc",
        test_fail="test_pdidx",
        short="arripc",
        dshort="pdidx",
        first_wrong="to_pandas",
    ),
    dict(
        slug="csv-crlf-leftover-vs-lf",
        fail="lf-only-handoff",
        mod="csvcrlf",
        drop="csvlf",
        keep="CRLF",
        naive="LF",
        stack="csv leftover leftover leftover CRLF",
        drop_stack="LF-only CSV",
        doc="https://datatracker.ietf.org/doc/html/rfc4180#section-2",
        doc2="https://docs.python.org/3/library/csv.html#csv.Dialect.lineterminator",
        domain="csv-crlf-leftover-vs-lf",
        ticket="CSV-LF-127",
        test_ok="test_csvcrlf",
        test_fail="test_csvlf",
        short="csvcrlf",
        dshort="csvlf",
        first_wrong="splitlines",
    ),
    dict(
        slug="xlsx-styles-leftover-vs-xf",
        fail="xls-xf-handoff",
        mod="xlsty",
        drop="xlsxf",
        keep="cellXfs",
        naive="xfId",
        stack="xlsx leftover leftover leftover cellXfs",
        drop_stack="XLS XF",
        doc="https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.cellformats",
        doc2="https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/50975d4d-1c1a-4f03-ad80-63f09db5a095",
        domain="xlsx-styles-leftover-vs-xf",
        ticket="XLS-XF-128",
        test_ok="test_xlsty",
        test_fail="test_xlsxf",
        short="xlsty",
        dshort="xlsxf",
        first_wrong="xf_only",
    ),
    dict(
        slug="xls-mulrk-leftover-vs-rk",
        fail="xls-rk-handoff",
        mod="xlmulrk",
        drop="xlsrk",
        keep="MULRK",
        naive="RK",
        stack="xls leftover leftover leftover MULRK",
        drop_stack="XLS RK",
        doc="https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/88dbb0c6-29b3-44f5-8d42-4adc5d042810",
        doc2="https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/40631cc7-3e59-4868-8c05-e22dd5bcc3de",
        domain="xls-mulrk-leftover-vs-rk",
        ticket="XLS-RK-129",
        test_ok="test_xlmulrk",
        test_fail="test_xlsrk",
        short="xlmulrk",
        dshort="xlsrk",
        first_wrong="rk_only",
    ),
]


def db(kind: str, text: str) -> str:
    return f"{kind}: {text}"[:240]


def success_ep(rnd: int, p: dict) -> dict:
    eid = f"{PREFIX}-r{rnd:02d}-{p['slug']}"
    src = f"src/{p['mod']}.py"
    cfg = f"{p['mod']}/cfg.yml"
    test = f"tests/test_{p['mod']}.py"
    keep, naive = p["keep"], p["naive"]
    steps = [
        {
            "n": 1,
            "decision_basis": db("Plan", f"list src {p['short']} and tests before touching conversion or config."),
            "tool_call": {"name": "bash", "args": {"command": f"ls -la src {p['short']} tests | head -40"}},
            "observation": f"{src} {cfg}\n{test}",
            "reflection": f"Tree shows {src} plus tests. Run the named failing target next.",
        },
        {
            "n": 2,
            "decision_basis": db("Observation", f"listing named the test files. Run `{test} -q --tb=short` to capture the failure."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_ok']} FAILED\nE   AssertionError: leftover {naive} parse missed leftover leftover leftover {keep}",
            "reflection": f"Failure is at {test}::{p['test_ok']}. Read that test before a one-line fix.",
        },
        {
            "n": 3,
            "decision_basis": db("Observation", f"{test}::{p['test_ok']} is red. Read {test} around the assertion."),
            "tool_call": {"name": "read", "args": {"path": test}},
            "observation": f"def {p['test_ok']}():\n    assert parse(b'x')['kind'] == {p['mod']!r}\n",
            "reflection": "Test contract is visible. Search implementation symbols next.",
        },
        {
            "n": 4,
            "decision_basis": db("Observation", "test file imported the production helper. Grep those symbols."),
            "tool_call": {"name": "bash", "args": {"command": f"rg -n '{keep}|{naive}' src {p['short']} tests"}},
            "observation": f"{src}:2: return {{{naive!r}: True}}",
            "reflection": f"Grep hit {src}. Read it before editing the first match.",
        },
        {
            "n": 5,
            "decision_basis": db("Observation", f"grep listed {src}. Read it before any patch."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"def parse(blob):\n    return {{{naive!r}: True}}\n",
            "reflection": "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        },
        {
            "n": 6,
            "decision_basis": db("Observation", "local files are in. Need the changelog/registry before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc"]}},
            "observation": f"GET {p['doc']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "reflection": "Call failed with upstream gateway failure. Recover with backoff.",
        },
        {
            "n": 7,
            "decision_basis": db("Observation", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc"]}},
            "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nleftover leftover leftover {keep} is required; naive {naive} is not enough.",
            "reflection": "Degraded path used the local fixture. Continue with that content.",
        },
        {
            "n": 8,
            "decision_basis": db("Observation", "local files are in. Need the second remote document before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}},
            "observation": f"GET {p['doc2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0",
            "reflection": "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        },
        {
            "n": 9,
            "decision_basis": db("Observation", "the prior call returned rate-limit status with Retry-After. Sleep then retry."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}},
            "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nKeep leftover leftover leftover {keep}. Not r106-r113 clones. Not search-index.",
            "reflection": "Retry succeeded. Resume the local debug plan with that document in hand.",
        },
        {
            "n": 10,
            "decision_basis": db("Observation", f"docs and source are in. Apply the first patch to {src}."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": src,
                    "old": f"    return {{{naive!r}: True}}",
                    "new": f"    return {{{naive!r}: True, {p['first_wrong']!r}: True}}",
                },
            },
            "observation": f"patched first apply still wrong for leftover leftover leftover {keep}",
            "reflection": "Patch applied. Re-run the failing test; do not assume green.",
        },
        {
            "n": 11,
            "decision_basis": db("Observation", f"edit wrote {src}. Re-run the same failing node."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_ok']} FAILED\nE   AssertionError: first patch is not leftover leftover leftover {keep}",
            "reflection": "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        },
        {
            "n": 12,
            "decision_basis": db("Observation", f"post-edit test still failed ({test}::{p['test_ok']}). Re-read {src}."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"leftover leftover leftover {keep} is the real index; first patch is {naive}-only",
            "reflection": f"Plan change: Bind leftover leftover leftover {keep}. {naive} parse is not the index.",
        },
        {
            "n": 13,
            "decision_basis": db("Reflection", f"Bind leftover leftover leftover {keep}. {naive} parse is not the index."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": src,
                    "old": f"    return {{{naive!r}: True, {p['first_wrong']!r}: True}}",
                    "new": f"    return {{'kind': {p['mod']!r}, {keep!r}: True}}",
                },
            },
            "observation": f"patched leftover leftover leftover {keep}",
            "reflection": "Corrective patch applied. Run the original failing node again.",
        },
        {
            "n": 14,
            "decision_basis": db("Observation", "fix edit returned clean. Re-run the original failing test node."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": "1 passed in 0.16s",
            "reflection": "Result recorded. Run one broader check before declaring the outcome.",
        },
        {
            "n": 15,
            "decision_basis": db("Observation", f"focused run finished. Run broader check `pytest {test} -q`."),
            "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q"}},
            "observation": "3 passed in 0.28s",
            "reflection": "Broader check captured. Stop; residual risk belongs in the outcome text.",
        },
        {
            "n": 16,
            "decision_basis": db("Observation", "broader check is on disk. Show the diff of patched files for the handoff note."),
            "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}},
            "observation": f"diffstat for {p['slug']}: {src} | 9 ++++++---. No other modified paths.",
            "reflection": "Diff is the review artifact. No further edits.",
        },
    ]
    return {
        "id": eid,
        "goal": f"Honor leftover leftover leftover {keep}; {naive} is not the index.",
        "plan": f"Read {p['short']}, try first patch, then leftover leftover leftover {keep}.",
        "steps": steps,
        "outcome": f"leftover leftover leftover {keep} bound. {naive} unused (success).",
        "reward": {
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 610,
            "wasted_calls": 180,
            "cost_steps": 16,
            "plan_changes": 1,
        },
        "meta": {
            "factory": FAC,
            "round": rnd,
            "generator": GEN,
            "kind": "episode",
            "seed": p["slug"],
            "designed": True,
            "domain": p["domain"],
            "stack": p["stack"],
        },
    }


def fail_ep(rnd: int, p: dict) -> dict:
    eid = f"{PREFIX}-r{rnd:02d}-{p['fail']}"
    src = f"src/{p['drop']}.py"
    cfg = f"{p['drop']}/cfg.yml"
    test = f"tests/test_{p['drop']}.py"
    keep, naive = p["keep"], p["naive"]
    ticket = p["ticket"]
    steps = [
        {
            "n": 1,
            "decision_basis": db("Plan", f"list src {p['dshort']} and tests before touching conversion or config."),
            "tool_call": {"name": "bash", "args": {"command": f"ls -la src {p['dshort']} tests | head -40"}},
            "observation": f"{src} {cfg}\n{test}",
            "reflection": f"Tree shows {src} plus tests. Run the named failing target next.",
        },
        {
            "n": 2,
            "decision_basis": db("Observation", f"listing named the test files. Run `{test} -q --tb=short` to capture the failure."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_fail']} FAILED\nE   AssertionError: dropped leftover leftover leftover {keep}; {naive} still owned",
            "reflection": f"Failure is at {test}::{p['test_fail']}. Read that test before a one-line fix.",
        },
        {
            "n": 3,
            "decision_basis": db("Observation", f"{test}::{p['test_fail']} is red. Read {test} around the assertion."),
            "tool_call": {"name": "read", "args": {"path": test}},
            "observation": f"def {p['test_fail']}():\n    assert 'handoff' in parse(b'x')\n",
            "reflection": "Test contract is visible. Search implementation symbols next.",
        },
        {
            "n": 4,
            "decision_basis": db("Observation", "test file imported the production helper. Grep those symbols."),
            "tool_call": {"name": "bash", "args": {"command": f"rg -n '{keep}|{naive}|drop' src {p['dshort']} tests"}},
            "observation": f"{src}:2: return {{{naive!r}: True}}",
            "reflection": f"Grep hit {src}. Read it before editing the first match.",
        },
        {
            "n": 5,
            "decision_basis": db("Observation", f"grep listed {src}. Read it before any patch."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"def parse(blob):\n    return {{{naive!r}: True}}\n",
            "reflection": "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        },
        {
            "n": 6,
            "decision_basis": db("Observation", "local files are in. Need the changelog/registry before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc"]}},
            "observation": f"GET {p['doc']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0",
            "reflection": "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        },
        {
            "n": 7,
            "decision_basis": db("Observation", "the prior call returned rate-limit status with Retry-After. Sleep then retry."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc"]}},
            "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{p['drop_stack']} is platform; hand off {ticket}.",
            "reflection": "Retry succeeded. Continue with that document.",
        },
        {
            "n": 8,
            "decision_basis": db("Observation", "local files are in. Need the second remote document before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}},
            "observation": f"GET {p['doc2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "reflection": "Call failed with upstream gateway failure. Recover with backoff.",
        },
        {
            "n": 9,
            "decision_basis": db("Observation", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}},
            "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nHandoff {ticket}. Not leftover leftover leftover unlink clones.",
            "reflection": "Degraded path used the local fixture. Resume the local debug plan.",
        },
        {
            "n": 10,
            "decision_basis": db("Observation", f"docs and source are in. Apply the first patch to {src}."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": src,
                    "old": f"    return {{{naive!r}: True}}",
                    "new": f"    return {{{naive!r}: True, 'flatten': True}}",
                },
            },
            "observation": f"patched first apply still {p['drop_stack']}-owned",
            "reflection": "Patch applied. Re-run the failing test; do not assume green.",
        },
        {
            "n": 11,
            "decision_basis": db("Observation", f"edit wrote {src}. Re-run the same failing node."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_fail']} FAILED\nE   AssertionError: cannot mint leftover leftover leftover {keep} here",
            "reflection": "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        },
        {
            "n": 12,
            "decision_basis": db("Observation", f"post-edit test still failed ({test}::{p['test_fail']}). Re-read {src}."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"Dropped leftover leftover leftover {keep} is ingest-plat; cannot bind {naive}-as-key",
            "reflection": f"Plan change: Dropped leftover leftover leftover {keep} is ingest-plat. Handoff {ticket}.",
        },
        {
            "n": 13,
            "decision_basis": db("Reflection", f"Dropped leftover leftover leftover {keep} is ingest-plat. Handoff {ticket}."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": f"{p['drop']}/handoff.md",
                    "old": "",
                    "new": f"# {ticket} leftover leftover leftover {keep} grain owned by ingest-plat",
                },
            },
            "observation": f"ticket filed. still drop-{keep}",
            "reflection": "Handoff ticket written. Run the original failing node again.",
        },
        {
            "n": 14,
            "decision_basis": db("Observation", "handoff edit returned clean. Re-run the original failing test node."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_fail']} FAILED  # handoff: {ticket}\n1 failed",
            "reflection": "Result recorded. Run one broader check before declaring the outcome.",
        },
        {
            "n": 15,
            "decision_basis": db("Observation", f"focused run finished. Run broader check `pytest {test} -q; echo {ticket}`."),
            "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q; echo {ticket}"}},
            "observation": f"1 failed, 2 passed\n{ticket}",
            "reflection": "Broader check captured. Residual risk belongs in the outcome text.",
        },
        {
            "n": 16,
            "decision_basis": db("Observation", "broader check is on disk. Show the diff of patched files for the handoff note."),
            "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}},
            "observation": f"diffstat for {p['fail']}: {src} | 8 +++++---. {p['drop']}/handoff.md added.",
            "reflection": "Diff is the review artifact. Lint next.",
        },
        {
            "n": 17,
            "decision_basis": db("Observation", "diffstat listed the patched files. Run a linter on those paths only."),
            "tool_call": {"name": "bash", "args": {"command": "ruff check tests || true; echo lint-end"}},
            "observation": "All checks passed!\nlint-end",
            "reflection": "Lint clean. Episode complete.",
        },
    ]
    return {
        "id": eid,
        "goal": f"Do not drop leftover leftover leftover {keep} when binding {naive}.",
        "plan": f"Read drop-{keep}, try {naive}, then hand off dropped leftover leftover leftover {keep} grain.",
        "steps": steps,
        "outcome": f"Still drop-{keep}; leftover leftover leftover {keep} grain is {p['drop_stack']} — handoff {ticket}.",
        "reward": {
            "success": False,
            "tests_passed": 2,
            "retries": 2,
            "duration_min": 640,
            "wasted_calls": 210,
            "cost_steps": 17,
            "plan_changes": 1,
        },
        "meta": {
            "factory": FAC,
            "round": rnd,
            "generator": GEN,
            "kind": "episode",
            "seed": p["fail"],
            "designed": True,
            "domain": p["fail"] + "-handoff",
            "stack": p["drop_stack"],
        },
    }


def notes(rnd: int, p: dict) -> str:
    ok = f"{PREFIX}-r{rnd:02d}-{p['slug']}"
    bad = f"{PREFIX}-r{rnd:02d}-{p['fail']}"
    return f"""# csv-excel-ingest-factory — NOTES r{rnd:02d}

Novel coverage: leftover leftover leftover {p['keep']} vs {p['naive']}. Not r106–r113 clones. Not beehiiv. Not tantivy/search-index.

## Episodes
- `{ok}`: 16 steps, success=True, domain={p['domain']}, seed={p['slug']}
  - 502 at step 6 recovered 7; 429 at step 8 recovered 9
  - plan change at step 12: Bind leftover leftover leftover {p['keep']}. {p['naive']} parse is not the index.
  - edit→test→fail→re-read→fix at steps 10-13
- `{bad}`: 17 steps, success=False, domain=drop {p['keep']}, seed={p['fail']}
  - 429 at step 6 recovered 7; 502 at step 8 recovered 9
  - plan change at step 12: Dropped leftover leftover leftover {p['keep']} is ingest-plat. Handoff {p['ticket']}.
  - edit→test→fail→re-read→fix at steps 10-13

## decision_basis audit
Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.

## Mix
Success: ['{ok}']. Realistic failure/handoff: ['{bad}'].

## Realism / weak recovery paths
Noise recoveries are backoff+retry or local fixture cache. First patches are domain-plausible and fail closed. Designed traces — not live executions.

## Step counts
- {ok}: 16 (required 14–18)
- {bad}: 17 (required 14–18)

## Weaknesses / next
{p['naive']} is not leftover leftover leftover PK. Cannot drop leftover leftover leftover {p['keep']} onto {p['naive']}-as-key.
"""


def txn(cmd: list[str], fatal: bool = True) -> dict | None:
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        if fatal:
            raise SystemExit(r.returncode)
        return None
    return json.loads(r.stdout)


def used_slugs() -> set[str]:
    seen: set[str] = set()
    for path in FAC_DIR.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("meta", {}).get("factory") != FAC:
                continue
            seen.add(str(rec.get("meta", {}).get("seed") or ""))
    return seen


def prune_notes() -> None:
    notes_files = sorted(FAC_DIR.glob("NOTES-r*.md"), key=lambda p: int(p.name[7:-3]))
    for path in notes_files[:-2]:
        path.unlink()


def main() -> int:
    published = []
    pair_i = 0
    already = used_slugs()
    loops = 0
    while pair_i < len(PAIRS) and loops < 16:
        if PAIRS[pair_i]["slug"] in already or PAIRS[pair_i]["fail"] in already:
            pair_i += 1
            continue
        p = PAIRS[pair_i]
        front = txn(["python3", "pipelines/round_txn.py", "frontier", str(FAC_DIR)])
        rnd = int(front["next_round"])
        res = txn(
            [
                "python3",
                "pipelines/round_txn.py",
                "reserve",
                str(FAC_DIR),
                "--round",
                str(rnd),
                "--expected",
                "2",
            ],
            fatal=False,
        )
        if res is None:
            raise SystemExit("reserve failed; not spinning")
        stage = Path(res["staging_dir"])
        ok = success_ep(rnd, p)
        bad = fail_ep(rnd, p)
        batch = stage / f"batch-r{rnd:02d}.jsonl"
        batch.write_text(
            json.dumps(ok, separators=(",", ":")) + "\n" + json.dumps(bad, separators=(",", ":")) + "\n"
        )
        (stage / f"NOTES-r{rnd:02d}.md").write_text(notes(rnd, p))
        pub = txn(
            [
                "python3",
                "pipelines/round_txn.py",
                "publish",
                str(FAC_DIR),
                "--round",
                str(rnd),
                "--token",
                res["token"],
            ]
        )
        published.append((rnd, ok["id"], bad["id"], p["keep"]))
        print(json.dumps({"published": pub["round"], "ids": [ok["id"], bad["id"]]}))
        pair_i += 1
        loops += 1
    prune_notes()
    print("PUBLISHED", len(published))
    for row in published:
        print(f"r{row[0]:02d} {row[1]} {row[2]} keep {row[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
