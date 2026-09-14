PARSE_BEFORE = '''def parse_lots(text: str) -> list[tuple[str, str]]:
    rows = []
    for line in text.split("\\n"):
        if not line:
            continue
        lot, note = line.split(",", 1)
        rows.append((lot, note))
    return rows
'''

PARSE_RSTRIP = '''def parse_lots(text: str) -> list[tuple[str, str]]:
    rows = []
    for line in text.split("\\n"):
        if not line:
            continue
        lot, note = line.rstrip().split(",", 1)
        rows.append((lot, note))
    return rows
'''

PARSE_SPLITLINES = '''def parse_lots(text: str) -> list[tuple[str, str]]:
    rows = []
    for line in text.splitlines():
        if not line:
            continue
        lot, note = line.split(",", 1)
        rows.append((lot, note))
    return rows
'''

PARSE_TEST = '''from lotcrlf.parse import parse_lots


def test_crlf_note_has_no_cr():
    rows = parse_lots("WB-440,berth 9\\r\\n")
    assert rows == [("WB-440", "berth 9")]


def test_trailing_space_note_kept():
    rows = parse_lots("WB-441,berth 9 \\n")
    assert rows == [("WB-441", "berth 9 ")]
'''


def ep2() -> dict:
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: LC-418 reports mill lot notes from week36.csv miss the catalog. Search parse_lots split rstrip splitlines for evidence of LF-only splitting that keeps CR."
            ),
            "plan": "1) search parse_lots 2) read parse.py 3) reproduce CR leftover 4) splitlines 5) unit tests; mill CSV NFS is a later handoff",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "parse_lots|splitlines|rstrip|split\\(",
                    "path": "src/lotcrlf",
                },
            },
            "observation": (
                "src/lotcrlf/parse.py:1:def parse_lots(text: str) -> list[tuple[str, str]]:\n"
                "src/lotcrlf/parse.py:4:    for line in text.split(\"\\n\"):\n"
                "src/lotcrlf/parse.py:7:        lot, note = line.split(\",\", 1)\n"
                "tests/test_parse.py:8:    parse_lots(\"WB-440,berth 9\\r\\n\")\n"
                "Found 4 matches; splitlines is unused."
            ),
            "reflection": "Found text.split on LF only. A mill PLC CRLF row would leave \\r on the note so catalog lookup of berth 9 misses.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: parse.py:4 uses text.split on LF and never splitlines (step 1). Read parse.py for evidence of rstrip, newline='', or csv.reader."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "src/lotcrlf/parse.py", "offset": 1, "limit": 16},
            },
            "observation": PARSE_BEFORE,
            "reflection": "Measured a bare split('\\n') with no rstrip. If week36.csv is CRLF, note becomes 'berth 9\\r' and the mill catalog key misses.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: parse_lots is split on LF with the CR still on the note (step 2). Run pytest for evidence the CRLF fixture already failed the catalog."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest -q tests/test_parse.py --tb=short 2>&1 | tail -n 20"
                },
            },
            "observation": (
                "F.....                                                                   [100%]\n"
                "=================================== FAILURES ===================================\n"
                "______________________________ test_crlf_row ______________________________\n"
                "tests/test_parse.py:10: in test_crlf_row\n"
                "    assert parse_lots(\"WB-440,berth 9\\r\\n\") == [(\"WB-440\", \"berth 9\")]\n"
                "E   AssertionError: assert [('WB-440', 'berth 9\\r')] == [('WB-440', 'berth 9')]\n"
                "FAILED tests/test_parse.py::test_crlf_row - AssertionError\n"
                "1 failed, 5 passed in 0.11s"
            ),
            "reflection": "Reproduced a trailing CR on the mill note. Unix-LF fixtures that never contain \\r still pass.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: test_crlf_row failed because note was berth 9 plus CR (step 3). pip install pytest-cov so coverage evidence can join the same suite."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pip install pytest-cov==5.0.0 2>&1 | tail -n 16"
                },
            },
            "observation": (
                "Looking in indexes: https://pypi.org/simple\n"
                "Collecting pytest-cov==5.0.0\n"
                "  Downloading pytest_cov-5.0.0-py3-none-any.whl (21 kB)\n"
                "ERROR: Could not install packages due to an OSError: 429 Too Many Requests\n"
                "Retry-After: 6\n"
                '{"error":"rate_limit_exceeded","retry_after":6,'
                '"message":"pypi.org CDN 429 for /simple/pytest-cov/"}\n'
            ),
            "reflection": "pypi.org returned 429 with retry-after 6. Sleep then retry install once; do not tight-loop the simple index.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: pip install returned 429 with retry_after 6 (step 4). Sleep 7s and retry install once as evidence the index recovered."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 7 && pip install pytest-cov==5.0.0 2>&1 | tail -n 8; "
                        "pytest -q tests/test_parse.py --tb=line 2>&1 | tail -n 6"
                    )
                },
            },
            "observation": (
                "Successfully installed pytest-cov-5.0.0 coverage-7.6.1\n"
                "F.....                                                                   [100%]\n"
                "FAILED tests/test_parse.py::test_crlf_row - AssertionError: assert [('WB-440', 'berth 9\\r')] == [('WB-440', 'berth 9')]\n"
                "1 failed, 5 passed in 0.10s"
            ),
            "reflection": "Install recovered. CRLF note still carries CR, so the defect is local split('\\n') not a missing pytest plugin.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: pytest-cov installed and CRLF parse still failed trailing CR (step 5). Dump split vs splitlines vs rstrip as evidence pad spaces would be lost."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 - <<'PY'\n"
                        "import json\n"
                        "from pathlib import Path\n"
                        "raw = 'WB-440,berth 9\\r\\n'\n"
                        "pad = 'WB-441,berth 9 \\n'\n"
                        "nl = raw.split('\\n')[0].split(',', 1)[1]\n"
                        "sl = raw.splitlines()[0].split(',', 1)[1]\n"
                        "rs = pad.split('\\n')[0].rstrip().split(',', 1)[1]\n"
                        "keep = pad.splitlines()[0].split(',', 1)[1]\n"
                        "meta = {\n"
                        "  'raw_repr': repr(raw),\n"
                        "  'split_nl_note': repr(nl),\n"
                        "  'splitlines_note': repr(sl),\n"
                        "  'rstrip_pad_note': repr(rs),\n"
                        "  'splitlines_pad_note': repr(keep),\n"
                        "  'cr_left': '\\r' in nl,\n"
                        "}\n"
                        "Path('/tmp/lotcrlf-meta.json').write_text(json.dumps(meta))\n"
                        "print(json.dumps(meta, indent=2))\n"
                        "PY"
                    )
                },
            },
            "observation": (
                "{\n"
                '  "raw_repr": "\'WB-440,berth 9\\\\r\\\\n\'",\n'
                '  "split_nl_note": "\'berth 9\\\\r\'",\n'
                '  "splitlines_note": "\'berth 9\'",\n'
                '  "rstrip_pad_note": "\'berth 9\'",\n'
                '  "splitlines_pad_note": "\'berth 9 \'",\n'
                '  "cr_left": true\n'
                "}\n"
                "Wrote /tmp/lotcrlf-meta.json from that dump. Found split LF keeps CR; rstrip also drops the PLC pad space on berth 9."
            ),
            "reflection": "Measured CR leftover on split('\\n') and rstrip eating 'berth 9 '. Latin-1 decode would not remove the CR; mill CSV is UTF-8 CRLF.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: dump cr_left true, splitlines_note berth 9, rstrip_pad_note lost the trailing space (step 6). jq the dump for evidence mill CSV is CRLF."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "filter": "{cr_left, split_nl_note, splitlines_note, rstrip_pad_note, splitlines_pad_note}",
                    "file": "/tmp/lotcrlf-meta.json",
                },
            },
            "observation": (
                "{\n"
                '  "cr_left": true,\n'
                '  "split_nl_note": "\'berth 9\\\\r\'",\n'
                '  "splitlines_note": "\'berth 9\'",\n'
                '  "rstrip_pad_note": "\'berth 9\'",\n'
                '  "splitlines_pad_note": "\'berth 9 \'"\n'
                "}\n"
                "Found LC-SPEC-2 in docs/lot-spec.md:6: mill CSV is CRLF; trailing spaces on notes are PLC pad and must stay."
            ),
            "reflection": (
                "Plan change: abandon re-encoding week36.csv as Unix LF / latin-1. Observation shows mill notes are UTF-8 CRLF with pad spaces. "
                "Switching the edit target to str.splitlines so CR is dropped and berth 9 pad is kept."
            ),
        },
        {
            "n": 8,
            "decision_basis": db(
                "Reflection: plan now targets splitlines, not latin-1 LF rewrite (step 7). First patch: rstrip each LF-split line."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "src/lotcrlf/parse.py",
                    "old_string": PARSE_BEFORE.strip(),
                    "new_string": PARSE_RSTRIP.strip(),
                },
            },
            "observation": (
                "Edited src/lotcrlf/parse.py: parse_lots now rstrip()s each LF-split line before the comma split. splitlines is still unused."
            ),
            "reflection": "rstrip is the tempting wrong durable step. CRLF notes would match; mill PLC pad 'berth 9 ' would collapse to 'berth 9'.",
        },
        {
            "n": 9,
            "decision_basis": db(
                "Observation: parse_lots now rstrip()s LF-split lines (step 8). Write CRLF and trailing-space tests as evidence both contracts must hold."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_parse_guard.py",
                    "content": PARSE_TEST,
                },
            },
            "observation": (
                "Wrote tests/test_parse_guard.py (14 lines). Asserts CRLF note is berth 9 and the PLC pad space on WB-441 is kept."
            ),
            "reflection": "Created a paired regression. Run it to see whether rstrip actually keeps the mill pad space.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: test_parse_guard.py asserts CRLF strip and pad-space keep (step 9). Run pytest for evidence the rstrip patch failed."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "pytest -q tests/test_parse.py tests/test_parse_guard.py --tb=short 2>&1 | tail -n 18"
                    )
                },
            },
            "observation": (
                ".F......                                                                 [100%]\n"
                "=================================== FAILURES ===================================\n"
                "________________________ test_trailing_space_note_kept ________________________\n"
                "tests/test_parse_guard.py:12: in test_trailing_space_note_kept\n"
                "    assert rows == [(\"WB-441\", \"berth 9 \")]\n"
                "E   AssertionError: assert [('WB-441', 'berth 9')] == [('WB-441', 'berth 9 ')]\n"
                "E   rstrip() ate the PLC pad space\n"
                "FAILED tests/test_parse_guard.py::test_trailing_space_note_kept - AssertionError\n"
                "1 failed, 7 passed in 0.13s"
            ),
            "reflection": "CRLF tests passed; pad space was stripped. Need splitlines so CR is a line break and trailing spaces stay.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: test_trailing_space_note_kept failed because note lost the pad space (step 10). Re-read parse.py for evidence rstrip is still set."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "src/lotcrlf/parse.py", "offset": 1, "limit": 16},
            },
            "observation": PARSE_RSTRIP,
            "reflection": "Found rstrip on each LF-split line. LC-SPEC-2 wants splitlines; drop rstrip so pad spaces cannot be eaten.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Reflection: rstrip ate the PLC pad space (step 11). Patch parse_lots to str.splitlines so CR is verified gone and pad spaces stay."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "src/lotcrlf/parse.py",
                    "old_string": PARSE_RSTRIP.strip(),
                    "new_string": PARSE_SPLITLINES.strip(),
                },
            },
            "observation": (
                "Edited src/lotcrlf/parse.py: parse_lots now iterates text.splitlines() then comma-splits. rstrip on the line is gone."
            ),
            "reflection": "Patched the mill CSV line split. Re-run parse and parse_guard tests.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: parse_lots now uses splitlines (step 12). Re-run pytest as verified evidence CRLF notes match and pad spaces stay."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "pytest -q tests/test_parse.py tests/test_parse_guard.py 2>&1 | tail -n 8"
                    )
                },
            },
            "observation": (
                "........                                                                 [100%]\n"
                "8 passed in 0.12s "
                "(test_crlf_row, test_crlf_note_has_no_cr, test_trailing_space_note_kept, plus 5 others)"
            ),
            "reflection": "Verified 8 passed including the CRLF pair. Unit line splitting is done; the mill CSV NFS copy is still required before LC-418 can close.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: unit tests passed; need the mill CSV NFS copy (step 13). GET the nockwick mill lots as evidence a live CRLF file can parse."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "curl -sS -o /tmp/mill-lots.csv -w '%{http_code}' "
                        "https://nfs.nockwick.internal/v1/lotcrlf/week36.csv"
                    )
                },
            },
            "observation": (
                "curl: (22) The requested URL returned error: 502\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "content-type: text/plain\n"
                "x-envoy-upstream-service-time: 30012\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection timeout\n"
                "000"
            ),
            "reflection": "nfs.nockwick.internal returned 502 upstream timeout. Retry once with backoff; if it stays down, the live CRLF round-trip stays unverified and LC-418 cannot close.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: mill NFS GET returned 502 upstream timeout (step 14). Sleep 5s, retry once, and if empty record evidence that the mill is unavailable."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 5 && curl -sS -o /tmp/mill-lots.csv -w '%{http_code}\\n' "
                        "https://nfs.nockwick.internal/v1/lotcrlf/week36.csv "
                        "|| echo LAB_UNAVAILABLE; ls /tmp/mill-lots.csv 2>&1 | head"
                    )
                },
            },
            "observation": (
                "LAB_UNAVAILABLE\n"
                "ls: cannot access '/tmp/mill-lots.csv': No such file or directory"
            ),
            "reflection": "NFS share stayed unavailable after backoff. Open LC-319 as the mill-CSV handoff; do not claim the live CRLF mill file on the nockwick box.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: mill-lots.csv was missing after LAB_UNAVAILABLE (step 15). Open gh issue create for LC-319 as evidence the unresolved mill ACK is tracked."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "repo": "nockwick/lotcrlf",
                    "title": "LC-319: mill week36 CRLF CSV required before closing LC-418 splitlines parse",
                    "body": "Unit tests splitlines CRLF notes + pad-space keep; nfs.nockwick.internal unreachable.",
                },
            },
            "observation": "https://git.nockwick.internal/lots/lotcrlf/issues/319",
            "reflection": "Created LC-319. lotcrlf unit tests are green; live mill-CSV confirmation is a separate ticket.",
        },
    ]
    return {
        "id": ID2,
        "goal": (
            "LC-418 (lotcrlf, Python 3.12 str.split; pytest): mill lot notes from week36.csv miss the catalog because parse_lots "
            "splits on LF only, so a PLC CRLF row leaves `\\r` on the note (`berth 9\\r`). Reproduce with the CRLF fixture, make "
            "parse_lots honor LC-SPEC-2 (CRLF line breaks, keep PLC pad spaces), and keep existing parse tests green. Designed "
            "plant; the mill NFS copy is a lab path, not a live lot claim."
        ),
        "steps": steps,
        "outcome": (
            "Root cause was text.split on LF, so mill CRLF notes kept a trailing CR and missed the catalog. A first patch that "
            "rstrip()ed each LF-split line made the CRLF row match and then dropped the PLC pad space on `berth 9 `. parse_lots "
            "now uses str.splitlines. Verified by pytest tests/test_parse.py tests/test_parse_guard.py: 8 passed including "
            "test_crlf_note_has_no_cr and test_trailing_space_note_kept. The mill NFS CSV stayed unreachable, so live CRLF "
            "confirmation is unresolved; LC-319 was opened as the handoff. Overall: incomplete; unit line splitting only."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "splitlines_applied": 0.10,
            "pad_space_kept": 0.08,
            "hil_unverified_penalty": -0.14,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.26,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 8,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 41,
                "hil_jobs": 0,
            },
        },
        "meta": meta_common(
            codebase_type="data pipeline (Python 3.12 mill lot CSV splitter)",
            bug_class="split on LF leaves CR on mill notes; rstrip also drops PLC pad spaces",
            test_harness="pytest",
            noise_steps={"429": 4, "502": 14},
            noise_recovery_steps={"429": 5, "502": 15},
            plan_change_step=7,
            debug_loop_steps=[8, 9, 10, 11, 12, 13],
            tags=[
                "python-3.12",
                "crlf",
                "splitlines",
                "rstrip",
                "mill-csv",
                "hil-handoff",
            ],
        ),
    }
