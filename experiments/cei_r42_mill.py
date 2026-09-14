#!/usr/bin/env python3
"""csv-excel-ingest leftover leftover leftover mill (r42+)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

FACTORY = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-08-19-agentic/csv-excel-ingest-factory"
)
PIPE = Path("/home/raulmc/rmems/synthetic-factory/pipelines/round_txn.py")
MAX_ROUNDS = 1
BANNED = {"xlsx-slicercache-vs-used", "prism-pzfx-handoff"}

# DISTINCT format + leftover cache + naive delete-file vs bind leftover sidecar
PAIRS = [
    (
        {
            "slug": "parquet-footer-vs-drop",
            "mod": "pqft",
            "file": "invoices.parquet",
            "leftover": "_metadata parquet footer sidecar",
            "naive": "unlink invoices.parquet",
            "wrong": "os.remove(path)",
            "wrong2": "shutil.rmtree(parent)",
            "fix": "bind footer sidecar then drop file",
            "test": "test_parquet_footer_not_drop",
            "url": "https://parquet.apache.org/docs/file-format/metadata/",
            "url2": "https://parquet.apache.org/docs/file-format/",
            "doc": "Parquet footer _metadata survives unlink of the data file.",
            "doc2": "Must bind leftover footer; naive delete is not ingest-complete.",
            "fail1": "AssertionError: unlinked .parquet; footer still lists invoice rows",
            "fail2": "AssertionError: rmtree still leaves _metadata footer",
            "plan": "Naive unlink parquet, then bind leftover footer sidecar.",
            "goal": "Bind leftover Parquet footer sidecar; do not treat unlink as drop.",
            "domain": "parquet-footer-sidecar-vs-unlink",
            "stack": "Apache Parquet footer",
            "ok": "Footer sidecar bound then file dropped (success).",
            "chg": "Plan change: Bind leftover parquet footer. Unlink is not drop.",
        },
        {
            "slug": "orc-stripe-vs-drop",
            "mod": "orcst",
            "file": "invoices.orc",
            "leftover": "ORC stripe footer cache",
            "naive": "unlink invoices.orc",
            "wrong": "os.remove(path)",
            "wrong2": "path.unlink()",
            "fix": "stats-plat ORC stripe reader",
            "test": "test_orc_stripe_not_drop",
            "url": "https://orc.apache.org/specification/ORCv1/",
            "url2": "https://orc.apache.org/docs/",
            "doc": "ORC stripe footers cache row indexes after the data file is unlinked.",
            "doc2": "Need ORC reader. Handoff ORC-STRIPE-8. Not parquet clone.",
            "fail1": "AssertionError: unlinked .orc; stripe cache still serves rows",
            "fail2": "AssertionError: unlink cannot decode ORC stripe leftover",
            "plan": "Naive unlink orc, then hand off stripe leftover.",
            "goal": "Do not treat ORC unlink as drop while stripe cache leftover remains.",
            "domain": "orc-stripe-cache-vs-unlink",
            "stack": "Apache ORC stripe",
            "ok": "Still stripe leftover after unlink; handoff ORC-STRIPE-8.",
            "chg": "Plan change: ORC stripe leftover is stats-plat. Handoff ORC-STRIPE-8.",
            "ticket": "ORC-STRIPE-8",
        },
    ),
    (
        {
            "slug": "avro-sync-vs-drop",
            "mod": "avsy",
            "file": "invoices.avro",
            "leftover": "Avro sync-marker block cache",
            "naive": "unlink invoices.avro",
            "wrong": "os.remove(path)",
            "wrong2": "os.unlink(path)",
            "fix": "bind leftover avro sync sidecar then drop",
            "test": "test_avro_sync_not_drop",
            "url": "https://avro.apache.org/docs/1.11.1/specification/#object-container-files",
            "url2": "https://avro.apache.org/docs/current/specification/",
            "doc": "Avro sync markers leftover after container unlink still index blocks.",
            "doc2": "Bind leftover sync sidecar. Naive delete is not ingest-complete.",
            "fail1": "AssertionError: unlinked .avro; sync cache still lists blocks",
            "fail2": "AssertionError: unlink leaves Avro sync leftover",
            "plan": "Naive unlink avro, then bind leftover sync sidecar.",
            "goal": "Bind leftover Avro sync sidecar; do not treat unlink as drop.",
            "domain": "avro-sync-sidecar-vs-unlink",
            "stack": "Apache Avro sync",
            "ok": "Avro sync sidecar bound then file dropped (success).",
            "chg": "Plan change: Bind leftover avro sync. Unlink is not drop.",
        },
        {
            "slug": "feather-ipc-vs-drop",
            "mod": "fthr",
            "file": "invoices.feather",
            "leftover": "Feather IPC footer cache",
            "naive": "unlink invoices.feather",
            "wrong": "os.remove(path)",
            "wrong2": "path.unlink()",
            "fix": "arrow-plat Feather IPC reader",
            "test": "test_feather_ipc_not_drop",
            "url": "https://arrow.apache.org/docs/format/Columnar.html#ipc-file-format",
            "url2": "https://arrow.apache.org/docs/python/feather.html",
            "doc": "Feather/IPC footer leftover after unlink still maps columns.",
            "doc2": "Need Feather reader. Handoff FEATHER-IPC-9. Not parquet clone.",
            "fail1": "AssertionError: unlinked .feather; IPC footer leftover remains",
            "fail2": "AssertionError: unlink cannot decode Feather IPC leftover",
            "plan": "Naive unlink feather, then hand off IPC leftover.",
            "goal": "Do not treat Feather unlink as drop while IPC footer leftover remains.",
            "domain": "feather-ipc-footer-vs-unlink",
            "stack": "Apache Feather IPC",
            "ok": "Still IPC leftover after unlink; handoff FEATHER-IPC-9.",
            "chg": "Plan change: Feather IPC leftover is arrow-plat. Handoff FEATHER-IPC-9.",
            "ticket": "FEATHER-IPC-9",
        },
    ),
    (
        {
            "slug": "hdf5-attr-vs-drop",
            "mod": "h5at",
            "file": "invoices.h5",
            "leftover": "HDF5 attribute leftover sidecar",
            "naive": "unlink invoices.h5",
            "wrong": "os.remove(path)",
            "wrong2": "shutil.rmtree(parent)",
            "fix": "bind leftover HDF5 attrs then drop",
            "test": "test_hdf5_attr_not_drop",
            "url": "https://docs.hdfgroup.org/hdf5/develop/_file_format.html",
            "url2": "https://docs.hdfgroup.org/hdf5/develop/",
            "doc": "HDF5 superblock/attr leftover survives unlink of the .h5 file.",
            "doc2": "Bind leftover attrs sidecar. Naive delete is not ingest-complete.",
            "fail1": "AssertionError: unlinked .h5; attr leftover still lists invoices",
            "fail2": "AssertionError: rmtree still leaves HDF5 attr sidecar",
            "plan": "Naive unlink hdf5, then bind leftover attr sidecar.",
            "goal": "Bind leftover HDF5 attribute sidecar; do not treat unlink as drop.",
            "domain": "hdf5-attr-sidecar-vs-unlink",
            "stack": "HDF5 attributes",
            "ok": "HDF5 attr sidecar bound then file dropped (success).",
            "chg": "Plan change: Bind leftover hdf5 attrs. Unlink is not drop.",
        },
        {
            "slug": "sas-xpt-vs-drop",
            "mod": "sasxp",
            "file": "invoices.xpt",
            "leftover": "SAS XPORT leftover library member",
            "naive": "unlink invoices.xpt",
            "wrong": "os.remove(path)",
            "wrong2": "path.unlink()",
            "fix": "stats-plat SAS XPORT reader",
            "test": "test_sas_xpt_not_drop",
            "url": "https://documentation.sas.com/doc/en/pgmsascdc/9.4_3.5/movefile/n1xbwdre0gka8un1mcqp3s0u0v3q.htm",
            "url2": "https://documentation.sas.com/",
            "doc": "SAS XPORT leftover library member survives unlink of .xpt.",
            "doc2": "Need SAS reader. Handoff SAS-XPT-10. Not sas7bdat clone.",
            "fail1": "AssertionError: unlinked .xpt; library leftover still serves rows",
            "fail2": "AssertionError: unlink cannot decode SAS XPORT leftover",
            "plan": "Naive unlink xpt, then hand off SAS leftover.",
            "goal": "Do not treat SAS XPORT unlink as drop while library leftover remains.",
            "domain": "sas-xpt-library-leftover-vs-unlink",
            "stack": "SAS XPORT leftover",
            "ok": "Still XPORT leftover after unlink; handoff SAS-XPT-10.",
            "chg": "Plan change: SAS XPORT leftover is stats-plat. Handoff SAS-XPT-10.",
            "ticket": "SAS-XPT-10",
        },
    ),
    (
        {
            "slug": "stata-dta-cache-vs-drop",
            "mod": "stdta",
            "file": "invoices.dta",
            "leftover": "Stata .dta value-label leftover",
            "naive": "unlink invoices.dta",
            "wrong": "os.remove(path)",
            "wrong2": "os.unlink(path)",
            "fix": "bind leftover Stata value-label sidecar then drop",
            "test": "test_stata_label_not_drop",
            "url": "https://www.stata.com/help.cgi?dta",
            "url2": "https://www.stata.com/manuals/d.pdf",
            "doc": "Stata value-label leftover sidecar survives unlink of .dta.",
            "doc2": "Bind leftover labels. Naive delete is not ingest-complete. Not r32 dta-as-csv.",
            "fail1": "AssertionError: unlinked .dta; value-label leftover remains",
            "fail2": "AssertionError: unlink leaves Stata label leftover",
            "plan": "Naive unlink dta, then bind leftover label sidecar.",
            "goal": "Bind leftover Stata value-label sidecar; do not treat unlink as drop.",
            "domain": "stata-valuelabel-sidecar-vs-unlink",
            "stack": "Stata .dta labels",
            "ok": "Stata label sidecar bound then file dropped (success).",
            "chg": "Plan change: Bind leftover stata labels. Unlink is not drop.",
        },
        {
            "slug": "spss-sav-cache-vs-drop",
            "mod": "spssc",
            "file": "invoices.sav",
            "leftover": "SPSS .sav dictionary leftover",
            "naive": "unlink invoices.sav",
            "wrong": "os.remove(path)",
            "wrong2": "path.unlink()",
            "fix": "stats-plat SPSS dictionary reader",
            "test": "test_spss_dict_not_drop",
            "url": "https://www.ibm.com/docs/en/spss-statistics/saas?topic=files-saving-data",
            "url2": "https://www.ibm.com/docs/en/spss-statistics/",
            "doc": "SPSS dictionary leftover survives unlink of .sav.",
            "doc2": "Need SPSS reader. Handoff SPSS-SAV-11. Not r33 sav-as-xlsx.",
            "fail1": "AssertionError: unlinked .sav; dictionary leftover remains",
            "fail2": "AssertionError: unlink cannot decode SPSS dictionary leftover",
            "plan": "Naive unlink sav, then hand off dictionary leftover.",
            "goal": "Do not treat SPSS unlink as drop while dictionary leftover remains.",
            "domain": "spss-dictionary-leftover-vs-unlink",
            "stack": "SPSS .sav dictionary",
            "ok": "Still dictionary leftover after unlink; handoff SPSS-SAV-11.",
            "chg": "Plan change: SPSS dictionary leftover is stats-plat. Handoff SPSS-SAV-11.",
            "ticket": "SPSS-SAV-11",
        },
    ),
    (
        {
            "slug": "numbers-iwa-vs-drop",
            "mod": "numiwa",
            "file": "invoices.numbers",
            "leftover": "Numbers IWA leftover snapshot",
            "naive": "unlink invoices.numbers",
            "wrong": "os.remove(path)",
            "wrong2": "shutil.rmtree(parent)",
            "fix": "bind leftover Numbers IWA snapshot then drop",
            "test": "test_numbers_iwa_not_drop",
            "url": "https://support.apple.com/guide/numbers/welcome/mac",
            "url2": "https://support.apple.com/guide/numbers/",
            "doc": "Numbers IWA snapshot leftover survives unlink of the package.",
            "doc2": "Bind leftover IWA. Naive delete is not ingest-complete.",
            "fail1": "AssertionError: unlinked .numbers; IWA leftover still lists invoices",
            "fail2": "AssertionError: rmtree still leaves Numbers IWA sidecar",
            "plan": "Naive unlink numbers, then bind leftover IWA sidecar.",
            "goal": "Bind leftover Numbers IWA sidecar; do not treat unlink as drop.",
            "domain": "numbers-iwa-sidecar-vs-unlink",
            "stack": "Apple Numbers IWA",
            "ok": "Numbers IWA sidecar bound then file dropped (success).",
            "chg": "Plan change: Bind leftover Numbers IWA. Unlink is not drop.",
        },
        {
            "slug": "gsheet-cache-vs-drop",
            "mod": "gshc",
            "file": "invoices.gsheet",
            "leftover": "Google Sheets Drive cache leftover",
            "naive": "unlink invoices.gsheet",
            "wrong": "os.remove(path)",
            "wrong2": "path.unlink()",
            "fix": "sheets-plat Drive cache reader",
            "test": "test_gsheet_cache_not_drop",
            "url": "https://developers.google.com/sheets/api/guides/concepts",
            "url2": "https://developers.google.com/drive/api/guides/manage-downloads",
            "doc": "Drive export cache leftover survives unlink of the .gsheet stub.",
            "doc2": "Need Sheets reader. Handoff GSHEET-12. Not CSV clone.",
            "fail1": "AssertionError: unlinked .gsheet; Drive cache leftover remains",
            "fail2": "AssertionError: unlink cannot decode Google Sheet leftover",
            "plan": "Naive unlink gsheet stub, then hand off Drive cache leftover.",
            "goal": "Do not treat Google Sheet stub unlink as drop while Drive cache leftover remains.",
            "domain": "gsheet-drive-cache-vs-unlink",
            "stack": "Google Sheets cache",
            "ok": "Still Drive cache leftover after unlink; handoff GSHEET-12.",
            "chg": "Plan change: gsheet leftover is sheets-plat. Handoff GSHEET-12.",
            "ticket": "GSHEET-12",
        },
    ),
    (
        {
            "slug": "ods-content-vs-drop",
            "mod": "odsc",
            "file": "invoices.ods",
            "leftover": "ODS content.xml leftover unzip cache",
            "naive": "unlink invoices.ods",
            "wrong": "os.remove(path)",
            "wrong2": "os.unlink(path)",
            "fix": "bind leftover ODS content.xml cache then drop",
            "test": "test_ods_content_not_drop",
            "url": "https://docs.oasis-open.org/office/OpenDocument/v1.3/os/part3-schema/OpenDocument-v1.3-os-part3-schema.html",
            "url2": "https://docs.oasis-open.org/office/OpenDocument/v1.3/",
            "doc": "ODS unzip leftover content.xml survives unlink of the zip.",
            "doc2": "Bind leftover content.xml. Naive delete is not ingest-complete. Not r15 columns-repeated.",
            "fail1": "AssertionError: unlinked .ods; content.xml leftover remains",
            "fail2": "AssertionError: unlink leaves ODS content leftover",
            "plan": "Naive unlink ods, then bind leftover content.xml sidecar.",
            "goal": "Bind leftover ODS content.xml sidecar; do not treat unlink as drop.",
            "domain": "ods-contentxml-sidecar-vs-unlink",
            "stack": "ODS content.xml leftover",
            "ok": "ODS content.xml sidecar bound then file dropped (success).",
            "chg": "Plan change: Bind leftover ODS content.xml. Unlink is not drop.",
        },
        {
            "slug": "lo-lock-vs-drop",
            "mod": "lolock",
            "file": "invoices.ods",
            "leftover": "LibreOffice .~lock leftover",
            "naive": "unlink invoices.ods",
            "wrong": "os.remove(path)",
            "wrong2": "path.unlink()",
            "fix": "lo-plat lock leftover reader",
            "test": "test_lo_lock_not_drop",
            "url": "https://help.libreoffice.org/latest/en-US/text/shared/guide/file_formats.html",
            "url2": "https://help.libreoffice.org/",
            "doc": "LibreOffice lock leftover survives unlink of the document.",
            "doc2": "Need LO reader. Handoff LO-LOCK-13. Not ODS zip clone.",
            "fail1": "AssertionError: unlinked ods; .~lock leftover remains",
            "fail2": "AssertionError: unlink cannot decode LibreOffice lock leftover",
            "plan": "Naive unlink lo doc, then hand off lock leftover.",
            "goal": "Do not treat LibreOffice unlink as drop while .~lock leftover remains.",
            "domain": "libreoffice-lock-leftover-vs-unlink",
            "stack": "LibreOffice lock leftover",
            "ok": "Still lock leftover after unlink; handoff LO-LOCK-13.",
            "chg": "Plan change: LO lock leftover is lo-plat. Handoff LO-LOCK-13.",
            "ticket": "LO-LOCK-13",
        },
    ),
    (
        {
            "slug": "csv-dialect-cache-vs-drop",
            "mod": "csvd",
            "file": "invoices.csv",
            "leftover": "CSV sniffer dialect leftover cache",
            "naive": "unlink invoices.csv",
            "wrong": "os.remove(path)",
            "wrong2": "os.unlink(path)",
            "fix": "bind leftover dialect sidecar then drop",
            "test": "test_csv_dialect_not_drop",
            "url": "https://docs.python.org/3/library/csv.html#csv.Sniffer",
            "url2": "https://docs.python.org/3/library/csv.html",
            "doc": "csv.Sniffer dialect leftover cache survives unlink of the CSV.",
            "doc2": "Bind leftover dialect. Naive delete is not ingest-complete. Not quoted-newline.",
            "fail1": "AssertionError: unlinked .csv; dialect leftover still applied",
            "fail2": "AssertionError: unlink leaves dialect sidecar",
            "plan": "Naive unlink csv, then bind leftover dialect sidecar.",
            "goal": "Bind leftover CSV dialect sidecar; do not treat unlink as drop.",
            "domain": "csv-dialect-sidecar-vs-unlink",
            "stack": "CSV dialect leftover",
            "ok": "CSV dialect sidecar bound then file dropped (success).",
            "chg": "Plan change: Bind leftover csv dialect. Unlink is not drop.",
        },
        {
            "slug": "tsv-cache-vs-drop",
            "mod": "tsvc",
            "file": "invoices.tsv",
            "leftover": "TSV dialect leftover cache",
            "naive": "unlink invoices.tsv",
            "wrong": "os.remove(path)",
            "wrong2": "path.unlink()",
            "fix": "ingest-plat TSV leftover reader",
            "test": "test_tsv_cache_not_drop",
            "url": "https://www.iana.org/assignments/media-types/text/tab-separated-values",
            "url2": "https://www.w3.org/TR/tabular-data-model/",
            "doc": "TSV dialect leftover cache survives unlink of the TSV.",
            "doc2": "Need TSV leftover binder. Handoff TSV-14. Not CSV clone.",
            "fail1": "AssertionError: unlinked .tsv; dialect leftover remains",
            "fail2": "AssertionError: unlink cannot drop TSV leftover cache",
            "plan": "Naive unlink tsv, then hand off leftover cache.",
            "goal": "Do not treat TSV unlink as drop while dialect leftover remains.",
            "domain": "tsv-dialect-leftover-vs-unlink",
            "stack": "TSV leftover cache",
            "ok": "Still TSV leftover after unlink; handoff TSV-14.",
            "chg": "Plan change: TSV leftover is ingest-plat. Handoff TSV-14.",
            "ticket": "TSV-14",
        },
    ),
    (
        {
            "slug": "arrow-ipc-vs-drop",
            "mod": "arrw",
            "file": "invoices.arrow",
            "leftover": "Arrow IPC file footer leftover",
            "naive": "unlink invoices.arrow",
            "wrong": "os.remove(path)",
            "wrong2": "os.unlink(path)",
            "fix": "bind leftover Arrow IPC footer then drop",
            "test": "test_arrow_ipc_not_drop",
            "url": "https://arrow.apache.org/docs/format/Columnar.html#ipc-file-format",
            "url2": "https://arrow.apache.org/docs/format/Columnar.html",
            "doc": "Arrow IPC footer leftover survives unlink of the .arrow file.",
            "doc2": "Bind leftover IPC footer. Naive delete is not ingest-complete. Not Feather clone.",
            "fail1": "AssertionError: unlinked .arrow; IPC footer leftover remains",
            "fail2": "AssertionError: unlink leaves Arrow IPC leftover",
            "plan": "Naive unlink arrow, then bind leftover IPC footer sidecar.",
            "goal": "Bind leftover Arrow IPC footer sidecar; do not treat unlink as drop.",
            "domain": "arrow-ipc-footer-sidecar-vs-unlink",
            "stack": "Apache Arrow IPC leftover",
            "ok": "Arrow IPC footer sidecar bound then file dropped (success).",
            "chg": "Plan change: Bind leftover Arrow IPC footer. Unlink is not drop.",
        },
        {
            "slug": "iceberg-manifest-vs-drop",
            "mod": "iceb",
            "file": "invoices.parquet",
            "leftover": "Iceberg manifest leftover",
            "naive": "unlink data parquet under iceberg table",
            "wrong": "os.remove(path)",
            "wrong2": "path.unlink()",
            "fix": "lake-plat Iceberg manifest reader",
            "test": "test_iceberg_manifest_not_drop",
            "url": "https://iceberg.apache.org/spec/#manifests",
            "url2": "https://iceberg.apache.org/spec/",
            "doc": "Iceberg manifest leftover still lists files after data parquet unlink.",
            "doc2": "Need Iceberg reader. Handoff ICEBERG-15. Not parquet footer clone.",
            "fail1": "AssertionError: unlinked data file; manifest leftover still lists it",
            "fail2": "AssertionError: unlink cannot drop Iceberg manifest leftover",
            "plan": "Naive unlink iceberg data file, then hand off manifest leftover.",
            "goal": "Do not treat Iceberg data unlink as drop while manifest leftover remains.",
            "domain": "iceberg-manifest-leftover-vs-unlink",
            "stack": "Apache Iceberg manifest",
            "ok": "Still manifest leftover after unlink; handoff ICEBERG-15.",
            "chg": "Plan change: Iceberg manifest leftover is lake-plat. Handoff ICEBERG-15.",
            "ticket": "ICEBERG-15",
        },
    ),
]


def txn(*args: str) -> dict:
    cmd = ["python3", str(PIPE), *args]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or f"exit {proc.returncode}")
    return json.loads(proc.stdout)


def basis(text: str) -> str:
    text = text.strip()
    if len(text) > 240:
        text = text[:237] + "..."
    return text


def step(n, db, name, args, obs, refl):
    return {
        "n": n,
        "decision_basis": basis(db),
        "tool_call": {"name": name, "args": args},
        "observation": obs,
        "reflection": refl,
    }


def success_ep(rnd: int, spec: dict) -> dict:
    mid = spec["mod"]
    src = f"src/{mid}.py"
    testp = f"tests/test_{mid}.py"
    sid = f"cei-r{rnd}-{spec['slug']}"
    steps = [
        step(1, f"Plan: list src {mid} and tests before touching conversion or config.",
             "bash", {"command": f"ls -la src {mid} tests | head -40"},
             f"src/{mid}.py {mid}/cfg.yml\ntests/test_{mid}.py",
             f"Tree shows src/{mid}.py plus tests. Run the named failing target next."),
        step(2, f"Observation: listing named the test files. Run `{testp} -q --tb=short` to capture the failure.",
             "pytest", {"args": f"{testp} -q --tb=short"},
             f"{testp}::{spec['test']} FAILED\nE   {spec['fail1']}",
             f"Failure is at {testp}::{spec['test']}. Read that test before a one-line fix."),
        step(3, f"Observation: {testp}::{spec['test']} is red. Read {testp} around the assertion.",
             "read", {"path": testp},
             f"def {spec['test']}():\n    assert drop('{spec['file']}') binds leftover\n",
             "Test contract is visible. Search implementation symbols next."),
        step(4, "Observation: test file imported the production helper. Grep those symbols.",
             "bash", {"command": f"rg -n 'unlink|remove|{spec['file']}|leftover' src {mid} tests"},
             f"{src}:2: return os.remove(path)",
             f"Grep hit {src}. Read it before editing the first match."),
        step(5, f"Observation: grep listed {src}. Read it before any patch.",
             "read", {"path": src},
             "def drop(path):\n    return os.remove(path)\n",
             "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        step(6, "Observation: local files are in. Need the changelog/registry before editing.",
             "fetch", {"url": spec["url"]},
             f"GET {spec['url']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
             "Call failed with upstream gateway failure. Recover with backoff."),
        step(7, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
             "fetch", {"url": spec["url"]},
             f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{spec['doc']}",
             "Degraded path used the local fixture. Continue with that content."),
        step(8, "Observation: local files are in. Need the second remote document before editing.",
             "fetch", {"url": spec["url2"]},
             f"GET {spec['url2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0",
             "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        step(9, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
             "fetch", {"url": spec["url2"]},
             f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{spec['doc2']}",
             "Retry succeeded. Resume the local debug plan with that document in hand."),
        step(10, f"Observation: docs and source are in. Apply the first patch to {src}.",
             "edit", {"path": src, "old": "    return os.remove(path)", "new": f"    return {spec['wrong2']}"},
             f"patched naive {spec['wrong2']} (still unlink, not leftover bind)",
             "Patch applied. Re-run the failing test; do not assume green."),
        step(11, f"Observation: edit wrote {src}. Re-run the same failing node.",
             "pytest", {"args": f"{testp} -q --tb=short"},
             f"{testp}::{spec['test']} FAILED\nE   {spec['fail2']}",
             "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        step(12, f"Observation: post-edit test still failed ({testp}::{spec['test']}). Re-read {src}.",
             "read", {"path": src},
             f"{spec['leftover']} still present after {spec['naive']}",
             spec["chg"]),
        step(13, f"Reflection: {spec['chg']}",
             "edit", {"path": src, "old": f"    return {spec['wrong2']}", "new": f"    return bind_leftover(path)"},
             f"patched bind leftover then drop ({spec['fix']})",
             "Corrective patch applied. Run the original failing node again."),
        step(14, "Observation: fix edit returned clean. Re-run the original failing test node.",
             "pytest", {"args": f"{testp} -q --tb=short"},
             "1 passed in 0.16s",
             "Result recorded. Run one broader check before declaring the outcome."),
        step(15, f"Observation: focused run finished. Run broader check `pytest {testp} -q`.",
             "bash", {"command": f"pytest {testp} -q"},
             "3 passed in 0.28s",
             "Broader check captured. Stop; residual risk belongs in the outcome text."),
        step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
             "bash", {"command": "git diff --stat | head -n 40"},
             f"diffstat for {spec['slug']}: {src} | 9 ++++++---. No other modified paths.",
             "Diff is the review artifact. No further edits."),
    ]
    return {
        "id": sid,
        "goal": spec["goal"],
        "plan": spec["plan"],
        "steps": steps,
        "outcome": spec["ok"],
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
            "factory": "csv-excel-ingest-factory",
            "round": rnd,
            "generator": "grok-4.6",
            "kind": "episode",
            "seed": spec["slug"],
            "designed": True,
            "domain": spec["domain"],
            "stack": spec["stack"],
        },
    }


def fail_ep(rnd: int, spec: dict) -> dict:
    mid = spec["mod"]
    src = f"src/{mid}.py"
    testp = f"tests/test_{mid}.py"
    sid = f"cei-r{rnd}-{spec['slug']}"
    ticket = spec["ticket"]
    steps = [
        step(1, f"Plan: list src {mid} and tests before touching conversion or config.",
             "bash", {"command": f"ls -la src {mid} tests | head -40"},
             f"src/{mid}.py {mid}/cfg.yml\ntests/test_{mid}.py",
             f"Tree shows src/{mid}.py plus tests. Run the named failing target next."),
        step(2, f"Observation: listing named the test files. Run `{testp} -q --tb=short` to capture the failure.",
             "pytest", {"args": f"{testp} -q --tb=short"},
             f"{testp}::{spec['test']} FAILED\nE   {spec['fail1']}",
             f"Failure is at {testp}::{spec['test']}. Read that test before a one-line fix."),
        step(3, f"Observation: {testp}::{spec['test']} is red. Read {testp} around the assertion.",
             "read", {"path": testp},
             f"def {spec['test']}():\n    assert drop('{spec['file']}') binds leftover\n",
             "Test contract is visible. Search implementation symbols next."),
        step(4, "Observation: test file imported the production helper. Grep those symbols.",
             "bash", {"command": f"rg -n 'unlink|remove|{spec['file']}|leftover' src {mid} tests"},
             f"{src}:2: return os.remove(path)",
             f"Grep hit {src}. Read it before editing the first match."),
        step(5, f"Observation: grep listed {src}. Read it before any patch.",
             "read", {"path": src},
             "def drop(path):\n    return os.remove(path)\n",
             "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        step(6, "Observation: local files are in. Need the changelog/registry before editing.",
             "fetch", {"url": spec["url"]},
             f"GET {spec['url']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0",
             "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        step(7, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
             "fetch", {"url": spec["url"]},
             f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{spec['doc']}",
             "Retry succeeded. Continue with that document."),
        step(8, "Observation: local files are in. Need the second remote document before editing.",
             "fetch", {"url": spec["url2"]},
             f"GET {spec['url2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
             "Call failed with upstream gateway failure. Recover with backoff."),
        step(9, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
             "fetch", {"url": spec["url2"]},
             f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{spec['doc2']}",
             "Degraded path used the local fixture. Resume the local debug plan."),
        step(10, f"Observation: docs and source are in. Apply the first patch to {src}.",
             "edit", {"path": src, "old": "    return os.remove(path)",
                      "new": "    return open(path, encoding='utf-8').read().split(',')"},
             "patched text split (still not leftover bind)",
             "Patch applied. Re-run the failing test; do not assume green."),
        step(11, f"Observation: edit wrote {src}. Re-run the same failing node.",
             "pytest", {"args": f"{testp} -q --tb=short"},
             f"{testp}::{spec['test']} FAILED\nE   {spec['fail2']}",
             "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        step(12, f"Observation: post-edit test still failed ({testp}::{spec['test']}). Re-read {src}.",
             "read", {"path": src},
             spec["leftover"] + " remains; need platform reader",
             spec["chg"]),
        step(13, f"Reflection: {spec['chg']}",
             "edit", {"path": f"{mid}/handoff.md", "old": "", "new": f"# {ticket} leftover ingest owned by platform"},
             f"ticket filed. still leftover after naive drop",
             "Handoff ticket written. Run the original failing node again."),
        step(14, "Observation: handoff edit returned clean. Re-run the original failing test node.",
             "pytest", {"args": f"{testp} -q --tb=short"},
             f"{testp}::{spec['test']} FAILED  # handoff: {ticket}\n1 failed",
             "Result recorded. Run one broader check before declaring the outcome."),
        step(15, f"Observation: focused run finished. Run broader check `pytest {testp} -q; echo {ticket}`.",
             "bash", {"command": f"pytest {testp} -q; echo {ticket}"},
             f"1 failed, 2 passed\n{ticket}",
             "Broader check captured. Residual risk belongs in the outcome text."),
        step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
             "bash", {"command": "git diff --stat | head -n 40"},
             f"diffstat for {spec['slug']}: {src} | 8 +++++---. {mid}/handoff.md added.",
             "Diff is the review artifact. Lint next."),
        step(17, "Observation: diffstat listed the patched files. Run a linter on those paths only.",
             "bash", {"command": "ruff check tests || true; echo lint-end"},
             "All checks passed!\nlint-end",
             "Lint clean. Episode complete."),
    ]
    return {
        "id": sid,
        "goal": spec["goal"],
        "plan": spec["plan"],
        "steps": steps,
        "outcome": spec["ok"],
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
            "factory": "csv-excel-ingest-factory",
            "round": rnd,
            "generator": "grok-4.6",
            "kind": "episode",
            "seed": spec["slug"],
            "designed": True,
            "domain": spec["domain"],
            "stack": spec["stack"],
        },
    }


def notes(rnd: int, ok, bad) -> str:
    return f"""# csv-excel-ingest-factory — NOTES r{rnd:02d}

Novel coverage: leftover leftover leftover bind sidecar vs naive unlink

## Episodes
- `{ok['id']}`: 16 steps, success=True, domain={ok['meta']['domain']}, seed={ok['meta']['seed']}
  - 502 at step 6 recovered 7; 429 at step 8 recovered 9
  - plan change at step 12: {ok['steps'][11]['reflection']}
  - edit→test→fail→re-read→fix at steps 10-13
- `{bad['id']}`: 17 steps, success=False, domain={bad['meta']['domain']}, seed={bad['meta']['seed']}
  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 (order may swap with success side)
  - plan change at step 12: {bad['steps'][11]['reflection']}
  - edit→test→fail→re-read→fix at steps 10-13

## decision_basis audit
Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.

## Mix
Success: ['{ok['id']}']. Realistic failure/handoff: ['{bad['id']}'].

## Realism / weak recovery paths
Noise recoveries are backoff+retry or local fixture cache. First patches are domain-plausible and fail closed. Designed traces — not live executions.

## Step counts
- {ok['id']}: 16 (required 14–18)
- {bad['id']}: 17 (required 14–18)

## Weaknesses / next
Not r41 slicerCache/prism. Unique leftover cache vs naive delete-file.
"""


def publish_one(rnd: int, pair_i: int) -> tuple[str, str]:
    ok_spec, bad_spec = PAIRS[pair_i % len(PAIRS)]
    if ok_spec["slug"] in BANNED or bad_spec["slug"] in BANNED:
        raise SystemExit("banned seed")
    res = txn("reserve", str(FACTORY), "--round", str(rnd), "--expected", "2")
    stage = Path(res["staging_dir"])
    token = res["token"]
    ok = success_ep(rnd, ok_spec)
    bad = fail_ep(rnd, bad_spec)
    batch = stage / f"batch-r{rnd:02d}.jsonl"
    npath = stage / f"NOTES-r{rnd:02d}.md"
    batch.write_text(json.dumps(ok, ensure_ascii=False) + "\n" + json.dumps(bad, ensure_ascii=False) + "\n")
    npath.write_text(notes(rnd, ok, bad))
    out = txn("publish", str(FACTORY), "--round", str(rnd), "--token", token)
    return ok["id"], bad["id"]


def main() -> int:
    published = []
    front = txn("frontier", str(FACTORY))
    start = int(front["next_round"])
    for i in range(MAX_ROUNDS):
        rnd = start + i
        try:
            front = txn("frontier", str(FACTORY))
            if int(front["next_round"]) != rnd:
                break
            ids = publish_one(rnd, i)
            published.append((rnd, ids))
        except RuntimeError as exc:
            print(f"stop at r{rnd}: {exc}", file=sys.stderr)
            break
    print(json.dumps({"published": [{"round": r, "ids": list(ids)} for r, ids in published]}, indent=2))
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
