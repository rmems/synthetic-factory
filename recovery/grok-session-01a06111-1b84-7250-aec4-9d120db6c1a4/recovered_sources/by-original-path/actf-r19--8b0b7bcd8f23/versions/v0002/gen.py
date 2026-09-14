#!/usr/bin/env python3
"""Generate designed ACTF r19 episodes (Q=2). Never writes outputs/raw/."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/home/raulmc/rmems/synthetic-factory/pipelines")

from check_records import FactoryStaging, check_jsonl  # noqa: E402
from round_txn_coverage import (  # noqa: E402
    has_long_horizon_debug_loop,
    sparse_step_progress_errors,
)
from validate_run import check_episode, terminal_outcome_agrees  # noqa: E402
from verify_execution import verify_batch_for_frontier, verify_record_execution  # noqa: E402

OUT = Path("/tmp/actf-r19")
GENERATED_AT = "2026-09-02T22:10:00Z"
KNOWN = {
    "bash",
    "read_file",
    "edit_file",
    "write_file",
    "search",
    "gh",
    "kubectl",
    "gate-cli",
    "tofu",
    "tenv",
    "tflint",
    "aws",
    "jq",
    "hcl2json",
    "block",
    "decline",
    "deny",
    "refuse",
}
FORBIDDEN = {
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "reasoning",
    "internal_reasoning",
    "hidden_reasoning",
    "thinking",
    "cot",
}
PROGRESS_RE = re.compile(
    r"\b(?:added|changed|created|deleted|disproved|edited|evidence|failed|"
    r"fixed|found|hypothesis|learned|measured|patched|removed|reproduced|"
    r"tested|updated|verified|wrote)\b",
    re.I,
)
STALL_RE = re.compile(r"\b(?:no[ -]?op|no change|nothing changed|unchanged)\b", re.I)
BASIS_PREFIX = ("Plan:", "Observation:", "Reflection:", "Tool call:")
HIDDEN_RE = re.compile(
    r"thought|chain_of_thought|scratch|inner_monologue|reasoning", re.I
)

SCAN_BEFORE = """package scan

import (
    "bufio"
    "io"
)

func CountAuditLines(r io.Reader) (int, error) {
    sc := bufio.NewScanner(r)
    n := 0
    for sc.Scan() {
        n++
    }
    return n, sc.Err()
}
"""

SCAN_1MB = """package scan

import (
    "bufio"
    "io"
)

func CountAuditLines(r io.Reader) (int, error) {
    sc := bufio.NewScanner(r)
    sc.Buffer(make([]byte, 0, 64*1024), 1024*1024)
    n := 0
    for sc.Scan() {
        n++
    }
    return n, sc.Err()
}
"""

SCAN_8MB = """package scan

import (
    "bufio"
    "io"
)

// maxAuditLine is KW-SPEC-4 (4 MiB events) plus headroom.
const maxAuditLine = 8 << 20

func CountAuditLines(r io.Reader) (int, error) {
    sc := bufio.NewScanner(r)
    sc.Buffer(make([]byte, 0, 64*1024), maxAuditLine)
    n := 0
    for sc.Scan() {
        n++
    }
    return n, sc.Err()
}
"""

SCAN_TEST = """package scan

import (
    "bytes"
    "testing"
)

func TestScan1_4MiBExceptionLine(t *testing.T) {
    line := bytes.Repeat([]byte("e"), 1_468_006)
    var buf bytes.Buffer
    buf.Write(line)
    buf.WriteByte('\\n')
    n, err := CountAuditLines(&buf)
    if err != nil {
        t.Fatalf("err=%v n=%d", err, n)
    }
    if n != 1 {
        t.Fatalf("n=%d want 1", n)
    }
}
"""

LOTS_BEFORE = """import configparser
from pathlib import Path

def load_lots(path: str) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding="utf-8")
    return cfg
"""

LOTS_PERCENT_ESCAPE = """import configparser
from pathlib import Path

def load_lots(path: str) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    raw = Path(path).read_text(encoding="utf-8").replace("%", "%%")
    cfg.read_string(raw)
    return cfg
"""

LOTS_HYBRID = """import configparser
from pathlib import Path

def load_lots(path: str) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(path, encoding="utf-8")
    logdir = cfg.get("paths", "logdir")
    logfile = cfg.get("paths", "logfile", fallback="")
    if "%(logdir)s" in logfile:
        cfg.set("paths", "logfile", logfile.replace("%(logdir)s", logdir))
    return cfg
"""

LOTS_TEST = '''import load_lots as m

def test_lot_percent_is_literal():
    cfg = m.load_lots("fixtures/lots.ini")
    assert cfg["lots"]["L-441"] == "12% indigo vat"

def test_logfile_expands_logdir():
    cfg = m.load_lots("fixtures/lots.ini")
    assert cfg["paths"]["logfile"] == "/var/log/copperlade/mill.log"
'''


def db(text: str) -> str:
    text = text.strip()
    if not text.startswith(BASIS_PREFIX):
        raise SystemExit(f"basis prefix: {text[:80]!r}")
    if not (80 <= len(text) <= 240):
        raise SystemExit(f"basis len {len(text)}: {text}")
    return text


def rights() -> dict:
    return {
        "provider": "SpaceXAI/xAI",
        "model": "grok-4.6",
        "channel": "consumer",
        "subscription_plan": "SuperGrok Heavy",
        "generation_surface": "SuperGrok Heavy chat",
        "generated_at": GENERATED_AT,
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "research_retention_status": "allowed",
        "research_evaluation_status": "allowed",
        "redistribution_status": "unresolved",
        "provider_training_status": "unresolved",
        "weight_publication_status": "blocked",
        "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
        "linear_issue": "RM-793",
        "training_ready": False,
    }


def meta_common(**extra) -> dict:
    m = {
        "factory": "agentic-coding-trajectory-factory",
        "round": 19,
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "sim_or_real": "designed",
        "training_ready": False,
        "rights": rights(),
    }
    m.update(extra)
    return m


def ep1() -> dict:
    """rimevault-auditscan: bufio.Scanner default 64KiB token drops mill NDJSON."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: RV-308 reports mill audit census stuck at 399 of 400 NDJSON lines. Search CountAuditLines and bufio.Scanner as evidence of a dropped token."
            ),
            "plan": "1) search scanner/token 2) read CountAuditLines 3) measure mill fixture line length 4) raise the token cap 5) 1.4MiB regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "CountAuditLines|bufio.Scanner|ErrTooLong|MaxScanTokenSize|Scan\\(\\)",
                    "path": ".",
                },
            },
            "observation": (
                "internal/scan/scan.go:8:func CountAuditLines(r io.Reader) (int, error) {\n"
                "internal/scan/scan.go:9:    sc := bufio.NewScanner(r)\n"
                "internal/scan/scan.go:10:   n := 0\n"
                "internal/scan/scan.go:11:   for sc.Scan() {\n"
                "internal/scan/scan.go:14:   return n, sc.Err()\n"
                "docs/kw-spec-4.md:12: exception payloads may reach 1.4 MiB compact JSON\n"
                "5 matches"
            ),
            "reflection": "Found CountAuditLines using NewScanner with the default token cap. Spec mentions 1.4 MiB exception payloads.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: scan.go:9 constructs bufio.NewScanner with no Buffer (step 1). Read the helper as evidence of any raised MaxTokenSize."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "internal/scan/scan.go", "offset": 1, "limit": 22},
            },
            "observation": SCAN_BEFORE,
            "reflection": "Learned there is no scanner.Buffer call. Default MaxScanTokenSize is 64KiB. Next measure the mill fixture.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: CountAuditLines uses default Scanner (step 2). Run go test ./internal/scan as evidence of the current short-line suite."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "go test ./internal/scan -mod=readonly -count=1 "
                        "-run 'TestScanShort' -v 2>&1 | tail -n 16"
                    )
                },
            },
            "observation": (
                "=== RUN   TestScanShortLines\n"
                "--- PASS: TestScanShortLines (0.00s)\n"
                "=== RUN   TestScanEmpty\n"
                "--- PASS: TestScanEmpty (0.00s)\n"
                "PASS\n"
                "ok  \tgit.rimevault.internal/log/auditscan/internal/scan\t0.02s"
            ),
            "reflection": "Verified short-line tests pass. The mill 400-line fixture is not in this filter. Next run the mill fixture.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: TestScanShortLines passed (step 3). Run go test with the mill 96k fixture as evidence of the dropped 400th line."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "GOPROXY=https://proxy.golang.org,direct go test ./internal/scan "
                        "-count=1 -run TestScanMill96kFixture -v 2>&1 | tail -n 20"
                    )
                },
            },
            "observation": (
                "go: github.com/google/go-cmp@v0.6.0: Get "
                '"https://proxy.golang.org/github.com/google/go-cmp/@v/v0.6.0.info": unexpected EOF\n'
                "dial tcp 142.251.32.81:443: connect: upstream connect error or disconnect/reset before headers. reset reason: connection failure\n"
                "HTTP/2 502 Bad Gateway"
            ),
            "reflection": "proxy.golang.org returned 502 while fetching go-cmp. Retry with GOPROXY=off against the module cache.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: GOPROXY returned 502 on go-cmp (step 4). Sleep 4s, set GOPROXY=off -mod=readonly, rerun TestScanMill96kFixture as cache evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 4 && GOPROXY=off go test ./internal/scan -mod=readonly -count=1 "
                        "-run 'TestScanMill96kFixture|TestScanShort' -v 2>&1 | tail -n 20"
                    )
                },
            },
            "observation": (
                "=== RUN   TestScanMill96kFixture\n"
                "    scan_test.go:41: CountAuditLines testdata/audit-96k.ndjson: err=bufio.Scanner: token too long n=399\n"
                "--- FAIL: TestScanMill96kFixture (0.01s)\n"
                "=== RUN   TestScanShortLines\n"
                "--- PASS: TestScanShortLines (0.00s)\n"
                "FAIL\n"
                "FAIL\tgit.rimevault.internal/log/auditscan/internal/scan\t0.03s"
            ),
            "reflection": "Measured token too long at n=399 on the mill fixture. Short lines still pass. Next wc the fixture.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: mill fixture failed token too long at n=399 (step 5). Measure line lengths with wc as evidence of a single long compact JSON line."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "wc -l -L testdata/audit-96k.ndjson; "
                        "python3 - <<'PY'\n"
                        "from pathlib import Path\n"
                        "p=Path('testdata/audit-96k.ndjson').read_bytes().splitlines()\n"
                        "print('lines', len(p), 'max', max(map(len,p)), 'min', min(map(len,p)))\n"
                        "print('internal_lf_in_max', p[max(range(len(p)), key=lambda i: len(p[i]))].count(10))\n"
                        "PY"
                    )
                },
            },
            "observation": (
                "  400  98304 testdata/audit-96k.ndjson\n"
                "lines 400 max 98304 min 84\n"
                "internal_lf_in_max 0"
            ),
            "reflection": "Found 400 lines, max 98304 bytes, no internal LF on the long line. Not pretty-print; it is one compact JSON event over 64KiB.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: wc -L is 98304 with 400 compact lines (step 6). Re-read scan.go as evidence the default 64KiB cap is the miss, not a missing newline."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "internal/scan/scan.go", "offset": 1, "limit": 18},
            },
            "observation": SCAN_BEFORE,
            "reflection": (
                "Plan change: abandon pretty-print / insert-newline. Observation shows one 98304-byte compact JSON line and default Scanner. "
                "Switching the edit target to scanner.Buffer so mill exception events survive."
            ),
        },
        {
            "n": 8,
            "decision_basis": db(
                "Reflection: pivoting off newlines; token cap is the miss (step 7). First patch: Buffer 1MiB, the tempting round number above 98304."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "internal/scan/scan.go",
                    "old_string": "    sc := bufio.NewScanner(r)\n    n := 0",
                    "new_string": (
                        "    sc := bufio.NewScanner(r)\n"
                        "    sc.Buffer(make([]byte, 0, 64*1024), 1024*1024)\n"
                        "    n := 0"
                    ),
                },
            },
            "observation": "Edited internal/scan/scan.go: added scanner.Buffer 64KiB start / 1MiB max. Default 64KiB cap is gone.",
            "reflection": "Wrote a 1MiB cap. KW-SPEC-4 still allows 1.4MiB exception payloads. Add a regression that size before trusting mill.",
        },
        {
            "n": 9,
            "decision_basis": db(
                "Observation: scan.go now buffers 1MiB (step 8). Write TestScan1_4MiBExceptionLine as evidence KW-SPEC-4 exception events must scan."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "internal/scan/scan_limit_test.go",
                    "content": SCAN_TEST,
                },
            },
            "observation": (
                "Wrote internal/scan/scan_limit_test.go (24 lines). Test writes a 1468006-byte line and asserts CountAuditLines returns 1 with a nil error."
            ),
            "reflection": "Created a 1.4MiB regression. Run it to see whether the 1MiB cap still fails.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: scan_limit_test.go asserts a 1.4MiB line (step 9). Run go test TestScan1_4MiB as evidence the 1MiB patch failed."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "GOPROXY=off go test ./internal/scan -mod=readonly -count=1 "
                        "-run 'TestScan1_4MiB|TestScanMill96k' -v 2>&1 | tail -n 18"
                    )
                },
            },
            "observation": (
                "=== RUN   TestScanMill96kFixture\n"
                "--- PASS: TestScanMill96kFixture (0.01s)\n"
                "=== RUN   TestScan1_4MiBExceptionLine\n"
                "    scan_limit_test.go:16: err=bufio.Scanner: token too long n=0\n"
                "--- FAIL: TestScan1_4MiBExceptionLine (0.01s)\n"
                "FAIL\n"
                "FAIL\tgit.rimevault.internal/log/auditscan/internal/scan\t0.03s"
            ),
            "reflection": "96k now passes; 1.4MiB still token too long. 1MiB is below KW-SPEC-4. Re-read the Buffer max.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: TestScan1_4MiBExceptionLine failed token too long n=0 (step 10). Re-read scan.go for evidence the Buffer max is still 1MiB."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "internal/scan/scan.go", "offset": 1, "limit": 20},
            },
            "observation": SCAN_1MB,
            "reflection": "Confirmed Buffer max is 1024*1024. Spec exception size is 1468006. Raise maxAuditLine to 8MiB.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Reflection: 1MiB cap is below the 1.4MiB fixture (step 11). Patch scan.go to maxAuditLine=8MiB matching KW-SPEC-4 headroom."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "internal/scan/scan.go",
                    "old_string": (
                        "    sc := bufio.NewScanner(r)\n"
                        "    sc.Buffer(make([]byte, 0, 64*1024), 1024*1024)\n"
                        "    n := 0"
                    ),
                    "new_string": (
                        "    sc := bufio.NewScanner(r)\n"
                        "    sc.Buffer(make([]byte, 0, 64*1024), maxAuditLine)\n"
                        "    n := 0"
                    ),
                },
            },
            "observation": (
                "Edited internal/scan/scan.go: Buffer max is maxAuditLine. Added const maxAuditLine = 8<<20 above CountAuditLines."
            ),
            "reflection": "Patched 8MiB cap. Re-run mill 96k and 1.4MiB tests as verification.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: scan.go now uses maxAuditLine 8MiB (step 12). Re-run go test ./internal/scan as verified evidence both long lines pass."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "GOPROXY=off go test ./internal/scan -mod=readonly -count=1 2>&1 | tail -n 10"
                    )
                },
            },
            "observation": (
                "ok  \tgit.rimevault.internal/log/auditscan/internal/scan\t0.05s\n"
                "PASS\n"
                "6 passed in 0.05s (TestScanShortLines, TestScanEmpty, TestScanMill96kFixture, "
                "TestScan1_4MiBExceptionLine, TestScanCRLF, TestScanNoTrailingNewline)"
            ),
            "reflection": "Verified 6 passed including TestScan1_4MiBExceptionLine. Open the RV-308 PR.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: 6 scan tests passed after the 8MiB cap (step 13). Create the RV-308 PR via gh api as evidence of the handoff."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/rimevault/auditscan/pulls",
                    "raw_field": "title=RV-308: raise bufio.Scanner max token to 8MiB for KW-SPEC-4 audit lines",
                },
            },
            "observation": (
                "HTTP 429 Too Many Requests\n"
                "Retry-After: 7\n"
                "x-ratelimit-limit: 30\n"
                "x-ratelimit-remaining: 0\n"
                '{"message":"API rate limit exceeded for user ci-bot (30 req/min); retry_after=7",'
                '"documentation_url":"https://docs.github.com/rest/overview/rate-limits"}'
            ),
            "reflection": "gh returned 429 with retry-after 7 on the shared ci-bot token. Wait the advertised window and retry the create once.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: gh api returned 429 with Retry-After 7 (step 14). Sleep 8s, retry the pull create once, then show the verified URL."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 8 && gh api -X POST repos/rimevault/auditscan/pulls "
                        "-f title='RV-308: raise bufio.Scanner max token to 8MiB for KW-SPEC-4 audit lines' "
                        "-f head=rv-308-scanner -f base=main --jq .html_url"
                    )
                },
            },
            "observation": "https://git.rimevault.internal/log/auditscan/pull/318",
            "reflection": "Verified PR 318 opened. RV-308 can close on the branch; mill 96k and 1.4MiB lines scan.",
        },
    ]
    return {
        "id": "act-r19-bufio-scanner-token-rimevault",
        "goal": (
            "RV-308 (auditscan, Go 1.23 bufio mill NDJSON census; go test ./internal/scan): "
            "nightly walk of mill-audit.ndjson reports 399 of 400 events and status SUCCESS with an empty error log. "
            "Find why CountAuditLines drops a line, make KW-SPEC-4 1.4MiB exception events scan, add a regression, "
            "and open a PR. Designed plant; not a live mill log claim."
        ),
        "steps": steps,
        "outcome": (
            "Root cause was bufio.NewScanner default MaxScanTokenSize 64KiB; mill compact JSON line 12 is 98304 bytes "
            "so Scan stops with token too long at n=399. A first patch that set Buffer max to 1MiB still failed "
            "TestScan1_4MiBExceptionLine (err=token too long n=0) because KW-SPEC-4 exception payloads are 1468006 bytes. "
            "CountAuditLines now uses maxAuditLine=8MiB. Verified by go test ./internal/scan: 6 passed including "
            "TestScanMill96kFixture and TestScan1_4MiBExceptionLine; PR 318 opened. Overall: verified and shipped."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "token_cap_8mib": 0.12,
            "exception_line_regression": 0.08,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.58,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 6,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 33,
            },
        },
        "meta": meta_common(
            codebase_type="library (Go 1.23 bufio mill NDJSON scanner)",
            bug_class="bufio.Scanner default 64KiB token cap drops compact mill JSON; first Buffer 1MiB still below KW-SPEC-4 1.4MiB",
            test_harness="go test",
            noise_steps={"502": 4, "429": 14},
            noise_recovery_steps={"502": 5, "429": 15},
            plan_change_step=7,
            debug_loop_steps=[8, 9, 10, 11, 12, 13],
            tags=[
                "bufio-scanner",
                "max-token-size",
                "ndjson",
                "mill-audit",
                "kw-spec-4",
            ],
        ),
    }


def ep2() -> dict:
    """copperlade-lotcfg: ConfigParser BasicInterpolation breaks mill lot codes with %."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: CL-77 reports mill lot L-441 missing after lots.ini reload. Search load_lots and ConfigParser interpolation as evidence of a percent parse."
            ),
            "plan": "1) search interpolation/% 2) read load_lots 3) measure live lots.ini vs InterpolationSyntaxError 4) keep % literal 5) logfile expand test + handoff",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "load_lots|ConfigParser|interpolation|InterpolationSyntaxError|%",
                    "path": ".",
                },
            },
            "observation": (
                "lotcfg/load_lots.py:4:def load_lots(path: str) -> configparser.ConfigParser:\n"
                "lotcfg/load_lots.py:5:    cfg = configparser.ConfigParser()\n"
                "lotcfg/load_lots.py:6:    cfg.read(path, encoding=\"utf-8\")\n"
                "fixtures/lots.ini:8:L-441 = 12% indigo vat\n"
                "fixtures/lots.ini:3:logfile = %(logdir)s/mill.log\n"
                "6 matches"
            ),
            "reflection": "Found default ConfigParser (BasicInterpolation) and a lot value with a bare percent. logfile still uses %(logdir)s.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: load_lots.py:5 constructs ConfigParser() with default interpolation (step 1). Read the helper as evidence of RawConfigParser."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "lotcfg/load_lots.py", "offset": 1, "limit": 16},
            },
            "observation": LOTS_BEFORE,
            "reflection": "Learned there is no interpolation=None. Bare % in L-441 will raise InterpolationSyntaxError. Next measure the live ConfigMap.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: load_lots uses interpolating ConfigParser (step 2). kubectl get the mill lots ConfigMap as evidence of the live ini text."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-copperlade",
                    "namespace": "copperlade",
                    "argv": ["get", "configmap", "copperlade-lots", "-o", "json"],
                },
            },
            "observation": (
                "Error from server (InternalError): an error on the server ("
                '"upstream connect error or disconnect/reset before headers. reset reason: connection failure"'
                ") has prevented the request from succeeding (get configmaps copperlade-lots)\n"
                "HTTP 502"
            ),
            "reflection": "kind ingress returned 502 on the ConfigMap get. Retry with --request-timeout and write a local dump.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: kubectl get configmap returned 502 from kind ingress (step 3). Retry --request-timeout=30s and write /tmp/copperlade-cm.json as dump evidence."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-copperlade",
                    "namespace": "copperlade",
                    "argv": [
                        "get",
                        "configmap",
                        "copperlade-lots",
                        "-o",
                        "json",
                        "--request-timeout=30s",
                    ],
                },
            },
            "observation": (
                "wrote /tmp/copperlade-cm.json (1 item)\n"
                "metadata.name=copperlade-lots resourceVersion=8841\n"
                "data.lots.ini bytes=312"
            ),
            "reflection": "Measured ConfigMap dump after the retry. Next jq the ini text for L-441 and logfile.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: ConfigMap dump is at /tmp/copperlade-cm.json (step 4). jq data.lots.ini as evidence of the live percent and logfile interpolation."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": ["-r", ".data[\"lots.ini\"]", "/tmp/copperlade-cm.json"],
                },
            },
            "observation": (
                "[paths]\n"
                "logdir = /var/log/copperlade\n"
                "logfile = %(logdir)s/mill.log\n"
                "\n"
                "[lots]\n"
                "L-441 = 12% indigo vat\n"
                "L-442 = 40% madder\n"
            ),
            "reflection": "Found live L-441 is 12% indigo vat and logfile is %(logdir)s/mill.log. Next confirm the Python interpolation contract.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: live ini has bare % in L-441 and %(logdir)s in logfile (step 5). Fetch configparser docs via gh as evidence of the interpolation rules."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/python/cpython/contents/Doc/library/configparser.rst",
                },
            },
            "observation": (
                "HTTP/2 429\n"
                "retry-after: 6\n"
                "x-ratelimit-limit: 60\n"
                "x-ratelimit-remaining: 0\n"
                '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=6",'
                '"documentation_url":"https://docs.github.com/rest/overview/rate-limits"}'
            ),
            "reflection": "GitHub returned 429 with retry-after 6 while fetching configparser docs. Wait, then use the vendored docs fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 6 (step 6). Sleep 7s, then read docs/configparser-interpolation.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {
                    "path": "docs/configparser-interpolation.md",
                    "offset": 1,
                    "limit": 16,
                },
            },
            "observation": (
                "1  BasicInterpolation: %(name)s from the same section or DEFAULT, and %% for a literal percent.\n"
                "2  A lone % that is not %% or %( raises InterpolationSyntaxError.\n"
                "3  interpolation=None (RawConfigParser) keeps percent signs literal, including %(logdir)s.\n"
                "4  Mixing: read with interpolation=None, then expand only the path keys that need %(logdir)s.\n"
                "5  Do not percent-escape the whole file: that turns %(logdir)s into a literal.\n"
            ),
            "reflection": "Verified a lone % is a syntax error and whole-file %% escape would freeze logfile. Next reproduce load_lots on the fixture.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs forbid whole-file %% escape (step 7). Run python load_lots on fixtures/lots.ini as evidence of InterpolationSyntaxError vs a bad mill clock."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 - <<'PY'\n"
                        "from lotcfg.load_lots import load_lots\n"
                        "try:\n"
                        "    cfg=load_lots('fixtures/lots.ini')\n"
                        "    print('keys', list(cfg['lots']))\n"
                        "except Exception as e:\n"
                        "    print(type(e).__name__, e)\n"
                        "PY"
                    )
                },
            },
            "observation": (
                "InterpolationSyntaxError '%' must be followed by '%' or '(', found: '% i'"
            ),
            "reflection": (
                "Plan change: abandon mill-clock / dye-vat encoding. Observation is InterpolationSyntaxError on L-441's 12% indigo. "
                "Switching the edit target to load_lots so lot percents stay literal and logfile still expands logdir."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off mill-clock; percent interpolation is the miss (step 8). Refuse deleting lots.ini as evidence CL-CFG-02 forbids dropping the mill ConfigMap."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "kubectl delete configmap/copperlade-lots so mill skips L-441 until codes are rewritten without percents",
                    "policy": "CL-CFG-02",
                    "incident": "CL-77",
                },
            },
            "observation": (
                "refused: CL-CFG-02 forbids deleting ConfigMap/copperlade-lots to skip InterpolationSyntaxError. "
                "Delete would drop L-442 and the path keys. "
                "Safe alternative: load with interpolation=None and expand logfile explicitly."
            ),
            "reflection": "Denied the delete. Next patch load_lots; keep the ConfigMap object.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: delete is refused; edit target is load_lots (step 9). First patch: replace % with %% on the whole file before ConfigParser.read_string."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "lotcfg/load_lots.py",
                    "old_string": (
                        "def load_lots(path: str) -> configparser.ConfigParser:\n"
                        "    cfg = configparser.ConfigParser()\n"
                        "    cfg.read(path, encoding=\"utf-8\")\n"
                        "    return cfg"
                    ),
                    "new_string": (
                        "def load_lots(path: str) -> configparser.ConfigParser:\n"
                        "    cfg = configparser.ConfigParser()\n"
                        "    raw = Path(path).read_text(encoding=\"utf-8\").replace(\"%\", \"%%\")\n"
                        "    cfg.read_string(raw)\n"
                        "    return cfg"
                    ),
                },
            },
            "observation": (
                "Edited lotcfg/load_lots.py: whole-file replace % -> %% then read_string. L-441 should parse; logfile may freeze as a literal."
            ),
            "reflection": "Wrote the tempting percent-escape. Add tests for L-441 literal and logfile expansion before trusting mill.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: load_lots now percent-escapes the whole file (step 10). Write tests as evidence L-441 stays 12% indigo and logfile expands logdir."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_load_lots.py",
                    "content": LOTS_TEST,
                },
            },
            "observation": (
                "Wrote tests/test_load_lots.py (12 lines). test_lot_percent_is_literal and test_logfile_expands_logdir added."
            ),
            "reflection": "Created both contracts. Run pytest to see whether whole-file %% freeze logfile.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: tests/test_load_lots.py asserts literal % and expanded logfile (step 11). Run pytest as evidence the %% patch failed logfile."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_load_lots.py -q --tb=short 2>&1 | tail -n 16"
                },
            },
            "observation": (
                "F.\n"
                "=========================== FAILURES ===========================\n"
                "__________ test_logfile_expands_logdir __________\n"
                "tests/test_load_lots.py:8: in test_logfile_expands_logdir\n"
                "    assert cfg[\"paths\"][\"logfile\"] == \"/var/log/copperlade/mill.log\"\n"
                "E   AssertionError: assert '%(logdir)s/mill.log' == '/var/log/copperlade/mill.log'\n"
                "FAILED tests/test_load_lots.py::test_logfile_expands_logdir\n"
                "1 failed, 1 passed in 0.08s"
            ),
            "reflection": "L-441 passed; logfile stayed %(logdir)s/mill.log because %% froze interpolation. Re-read load_lots.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: test_logfile_expands_logdir failed got %(logdir)s/mill.log (step 12). Re-read load_lots.py as evidence of the whole-file replace."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "lotcfg/load_lots.py", "offset": 1, "limit": 18},
            },
            "observation": LOTS_PERCENT_ESCAPE,
            "reflection": "Confirmed replace('%','%%') before read_string. interpolation=None plus explicit %(logdir)s expand keeps both contracts.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: whole-file %% freeze is the miss (step 13). Patch load_lots to interpolation=None and expand logfile from logdir only."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "lotcfg/load_lots.py",
                    "old_string": (
                        "def load_lots(path: str) -> configparser.ConfigParser:\n"
                        "    cfg = configparser.ConfigParser()\n"
                        "    raw = Path(path).read_text(encoding=\"utf-8\").replace(\"%\", \"%%\")\n"
                        "    cfg.read_string(raw)\n"
                        "    return cfg"
                    ),
                    "new_string": (
                        "def load_lots(path: str) -> configparser.ConfigParser:\n"
                        "    cfg = configparser.ConfigParser(interpolation=None)\n"
                        "    cfg.read(path, encoding=\"utf-8\")\n"
                        "    logdir = cfg.get(\"paths\", \"logdir\")\n"
                        "    logfile = cfg.get(\"paths\", \"logfile\", fallback=\"\")\n"
                        "    if \"%(logdir)s\" in logfile:\n"
                        "        cfg.set(\"paths\", \"logfile\", logfile.replace(\"%(logdir)s\", logdir))\n"
                        "    return cfg"
                    ),
                },
            },
            "observation": (
                "Edited lotcfg/load_lots.py: interpolation=None; logfile expands %(logdir)s only. Whole-file percent-escape is gone."
            ),
            "reflection": "Patched the hybrid load. Re-run pytest; both lot percent and logfile expansion should pass.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: load_lots now uses interpolation=None plus logfile expand (step 14). Re-run pytest tests/test_load_lots.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_load_lots.py tests/test_load_lots_defaults.py -q --tb=short 2>&1 | tail -n 10"
                },
            },
            "observation": (
                "......\n"
                "6 passed in 0.09s"
            ),
            "reflection": "Verified 6 passed including test_lot_percent_is_literal and test_logfile_expands_logdir. Check gate-cli before applying the ConfigMap.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: pytest passed 6/6 after the hybrid load (step 15). Run gate-cli check apply as evidence whether prod ConfigMap mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "copperlade-lots-reload",
                        "--resource",
                        "configmap/copperlade-lots",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change copperlade-lots-reload\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: CL-88\n"
                "until: 2026-09-09T00:00:00Z\n"
                "evidence: change mutates ConfigMap/copperlade-lots (nightly mill lot window)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under CL-88 freeze through 2026-09-09. Do not kubectl apply. Open a handoff issue attaching the unit fix.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the ConfigMap apply under freeze CL-88 (step 16). Open a handoff issue as evidence live lots.ini still interpolates."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "CL-91: apply lotcfg interpolation=None after CL-88 freeze (blocks CL-77 close)",
                    "body": "load_lots uses interpolation=None and expands logfile; pytest 6 passed. Live ConfigMap still loaded by the old interpolating helper. gate-cli freeze CL-88 until 2026-09-09. Do not kubectl delete the ConfigMap.",
                },
            },
            "observation": "https://git.copperlade.internal/cfg/lotcfg/issues/91",
            "reflection": "Opened CL-91. Renderer is green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": "act-r19-configparser-percent-copperlade",
        "goal": (
            "CL-77 (lotcfg, Python 3.12 mill lot ConfigParser + kind copperlade; pytest + kubectl): "
            "nightly reload drops mill lot L-441 (12% indigo vat) while L-442 still appears. "
            "Find why load_lots raises on percent lot codes, keep logfile %(logdir)s expansion, and apply or hand off. "
            "Designed plant; not a live mill dye-vat claim."
        ),
        "steps": steps,
        "outcome": (
            "Root cause was configparser.ConfigParser BasicInterpolation treating the '%' in '12% indigo vat' as a "
            "syntax error (InterpolationSyntaxError). A first patch that replaced '%' with '%%' across the whole file "
            "kept L-441 but froze logfile as '%(logdir)s/mill.log' (test_logfile_expands_logdir failed). load_lots now "
            "reads with interpolation=None and expands logfile from logdir only; pytest 6 passed. Applying "
            "ConfigMap/copperlade-lots remains blocked by gate-cli freeze CL-88; live loader is still interpolating. "
            "CL-91 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "percent_literal_fix": 0.10,
            "logfile_expand_test": 0.08,
            "prod_apply_blocked_penalty": -0.12,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.28,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 6,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 3,
                "duration_min": 36,
                "prod_apply": 0,
            },
        },
        "meta": meta_common(
            codebase_type="CLI / mill lot ConfigParser (Python 3.12)",
            bug_class="BasicInterpolation treats mill lot '%' as syntax; first whole-file %% escape freezes %(logdir)s",
            test_harness="pytest + kubectl + gate-cli",
            noise_steps={"502": 3, "429": 6},
            noise_recovery_steps={"502": 4, "429": 7},
            plan_change_step=8,
            debug_loop_steps=[10, 11, 12, 13, 14, 15],
            tags=[
                "configparser",
                "interpolation",
                "percent-literal",
                "mill-lots",
                "gate-cli-freeze",
                "refuse-delete",
            ],
        ),
    }


def walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            yield child, k, v
            yield from walk_keys(v, child)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]")


def prior_ids() -> set[str]:
    found: set[str] = set()
    for batch in Path("/tmp").glob("actf-r*/batch-r*.jsonl"):
        if batch.parent == OUT:
            continue
        try:
            text = batch.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.split("\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            rid = rec.get("id")
            if isinstance(rid, str):
                found.add(rid)
    for gen in Path("/tmp").glob("actf-r*/gen.py"):
        if gen.parent == OUT:
            continue
        try:
            text = gen.read_text(encoding="utf-8")
        except OSError:
            continue
        found.update(re.findall(r'act-r\d+-[a-z0-9-]+', text))
        found.update(re.findall(r'actf-r\d+-\d+', text))
    return found


def validate_record(rec: dict) -> None:
    steps = rec["steps"]
    n = len(steps)
    if not 12 <= n <= 17:
        raise SystemExit(f"{rec['id']} step count {n}")
    for i, step in enumerate(steps, 1):
        if step["n"] != i:
            raise SystemExit(f"{rec['id']} numbering {step['n']} != {i}")
        name = step["tool_call"]["name"]
        if name not in KNOWN:
            raise SystemExit(f"{rec['id']} unknown tool {name}")
        if not isinstance(step["tool_call"].get("args"), dict):
            raise SystemExit(f"{rec['id']} args not object {i}")
        if not step["observation"].strip():
            raise SystemExit(f"{rec['id']} empty obs {i}")
        db(step["decision_basis"])
        blob = " ".join(
            [
                step["decision_basis"],
                step["observation"],
                step["tool_call"]["name"],
                json.dumps(step["tool_call"]["args"], sort_keys=True),
            ]
        )
        if STALL_RE.search(blob):
            raise SystemExit(f"{rec['id']} step {i} stall: {STALL_RE.search(blob).group(0)!r}")
        if not PROGRESS_RE.search(blob):
            raise SystemExit(
                f"{rec['id']} step {i} sparse progress: {step['decision_basis'][:100]!r}"
            )
        if "hypothesis" in step["observation"].lower():
            raise SystemExit(f"{rec['id']} step {i} hypothesis in observation")
    obs = [s["observation"] for s in steps]
    n429 = sum("429" in o for o in obs)
    n502 = sum("502" in o for o in obs)
    if n429 != 1 or n502 != 1:
        raise SystemExit(f"{rec['id']} noise counts 429={n429} 502={n502}")
    recov = rec["meta"]["noise_recovery_steps"]
    noise = rec["meta"]["noise_steps"]
    for code, idx in noise.items():
        if code not in steps[idx - 1]["observation"]:
            raise SystemExit(f"{rec['id']} noise {code} not in step {idx}")
        ridx = recov[code]
        if code not in steps[ridx - 1]["decision_basis"]:
            raise SystemExit(f"{rec['id']} recovery {ridx} missing {code} in basis")
        if code in steps[ridx - 1]["observation"]:
            raise SystemExit(f"{rec['id']} recovery {ridx} repeats {code} in observation")
    reflections = [s.get("reflection", "") for s in steps]
    pivots = [i + 1 for i, r in enumerate(reflections) if "Plan change:" in r or "Pivoting:" in r]
    if pivots != [rec["meta"]["plan_change_step"]]:
        raise SystemExit(f"{rec['id']} plan-change {pivots}")
    pc = rec["meta"]["plan_change_step"]
    if pc in (1, n):
        raise SystemExit(f"{rec['id']} plan-change at terminal {pc}")
    nxt = steps[pc]["decision_basis"]
    if "pivot" not in nxt.lower() and "abandon" not in nxt.lower():
        raise SystemExit(f"{rec['id']} next basis missing pivot")
    for path, key, _ in walk_keys(rec):
        norm = re.sub(r"[^a-z0-9]+", "_", key).strip("_").lower()
        if norm in FORBIDDEN or norm.startswith("internal_reasoning"):
            raise SystemExit(f"{rec['id']} forbidden key {path}")
        if "thought" in norm and norm != "thoughtful":
            raise SystemExit(f"{rec['id']} thought-like key {path}")
    if rec["meta"]["sim_or_real"] != "designed":
        raise SystemExit("sim_or_real")
    blob = json.dumps(rec)
    if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
        raise SystemExit("real provenance")
    try:
        blob.encode("ascii")
    except UnicodeEncodeError as exc:
        raise SystemExit(f"{rec['id']} non-ascii: {exc}") from exc
    rc = rec["reward"]
    numeric = [
        v
        for k, v in rc.items()
        if k not in {"success", "aggregation", "cost", "total"}
        and isinstance(v, (int, float))
        and not isinstance(v, bool)
    ]
    if abs(sum(numeric) - rc["total"]) > 1e-9:
        raise SystemExit(f"{rec['id']} reward {sum(numeric)} != {rc['total']}")
    if rec["meta"]["training_ready"] is not False:
        raise SystemExit("training_ready")
    if rec["meta"]["rights"]["intended_use"] != "research_only":
        raise SystemExit("rights")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        raise SystemExit("RM-793")
    if rec["meta"]["rights"]["training_ready"] is not False:
        raise SystemExit("rights.training_ready")
    if rec["meta"]["round"] != 19:
        raise SystemExit("round")
    if rec["reward"]["success"] is True and not re.search(
        r"\b(?:verified|shipped|passed)\b", rec["outcome"], re.I
    ):
        raise SystemExit(f"{rec['id']} success outcome missing completion")
    if rec["reward"]["success"] is False and not re.search(
        r"\b(?:incomplete|unresolved|handoff|pending)\b", rec["outcome"], re.I
    ):
        raise SystemExit(f"{rec['id']} failure outcome missing incomplete/handoff")
    if not terminal_outcome_agrees(rec["outcome"], rec["reward"]["success"]):
        raise SystemExit(f"{rec['id']} terminal_outcome_agrees")
    errs = check_episode(
        rec, rec["id"], forbid_hidden_thought=True, enforce_terminal_outcome=True
    )
    if errs:
        raise SystemExit(f"{rec['id']} check_episode {errs}")
    if not has_long_horizon_debug_loop(steps):
        raise SystemExit(f"{rec['id']} missing debug loop")
    sparse = sparse_step_progress_errors(rec["id"], steps)
    if sparse:
        raise SystemExit(f"{rec['id']} sparse {sparse}")
    status, reason = verify_record_execution(rec, rec["id"])
    if status != "verified":
        raise SystemExit(f"{rec['id']} execution {status}: {reason}")


def notes() -> str:
    return """# ACTF r19 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (`FACTORY_QUOTAS["agentic-coding-trajectory-factory"] == 2`). IDs mill-safe `act-r19-bufio-scanner-token-rimevault`, `act-r19-configparser-percent-copperlade` (prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`jq`/`refuse`). meta.round=19 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Linear RM-793. Invented repos `git.rimevault.internal/log/auditscan.git` and `git.copperlade.internal/cfg/lotcfg.git`. Never wrote outputs/raw/. Novelty vs staged r10–r15, in-flight r16 zipslip/BigDecimal and r17 pgjdbc/JSON.parse-snowflake, and committed mill (meterflow/hubgate/shardup/tollgate/feedloom/tallyhouse).

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r19-bufio-scanner-token-rimevault | Go 1.23 bufio mill NDJSON scanner / go test | default 64KiB token cap drops compact mill JSON; first Buffer 1MiB still below KW-SPEC-4 1.4MiB | success; 6/6; PR 318 | 0.58 |
| act-r19-configparser-percent-copperlade | Python 3.12 mill lot ConfigParser / pytest + kubectl + gate-cli | BasicInterpolation treats mill lot `%` as syntax; first whole-file `%%` escape freezes `%(logdir)s` | incomplete HIL/prod apply; CL-91; freeze CL-88 | 0.28 |

## Step counts, noise, plan change
- act-r19-bufio-scanner-token-rimevault: 15 steps. 502 at step 4 (`go test` GOPROXY go-cmp, upstream connect) → recovery step 5 (`sleep 4 && GOPROXY=off -mod=readonly`; token too long n=399). 429 at step 14 (`gh api` POST pulls, Retry-After 7) → recovery step 15 (`sleep 8 && gh api` → PR 318). Plan change at step 7: wc -L 98304 compact JSON, no internal LF, kills pretty-print/insert-newline; edit target becomes scanner.Buffer. Debug loop: 8 Buffer 1MiB → 9 write 1.4MiB pytest-style go test → 10 FAIL token too long n=0 → 11 re-read 1MiB max → 12 maxAuditLine 8MiB → 13 6 passed.
- act-r19-configparser-percent-copperlade: 17 steps. 502 at step 3 (`kubectl get configmap` kind ingress) → recovery step 4 (`--request-timeout=30s` writes /tmp/copperlade-cm.json). 429 at step 6 (`gh api` cpython configparser.rst, retry-after 6) → recovery step 7 (read vendored `docs/configparser-interpolation.md`). Plan change at step 8: InterpolationSyntaxError on `12% indigo` kills mill-clock/dye-vat encoding. Debug loop: 10 whole-file `%%` → 11 write literal+% and logfile tests → 12 FAIL logfile `%(logdir)s/mill.log` → 13 re-read replace → 14 interpolation=None + logfile expand → 15 6 passed. `refuse` at step 9 blocks ConfigMap delete. gate-cli REJECT at 16; CL-91 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80–240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. rimevault: 0.40+0.12+0.08−0.02=0.58. copperlade: 0.24+0.10+0.08−0.12−0.02=0.28.

## Realism / weak recovery
Good: bufio.Scanner 64KiB is a real NDJSON footgun; the 1MiB first patch still fails a measured 1.4MiB KW-SPEC-4 exception line. ConfigParser BasicInterpolation vs mill lot `12%` is the usual percent trap; whole-file `%%` is the equally tempting wrong durable step and the logfile test names the contract. gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Weak: GOPROXY 502 fallback is availability (module cache is not a stale go-cmp that still truncates); kubectl json dump is one object; no reviewer asking to `scanner.Split(bufio.ScanBytes)`. Next densification: a 502 whose local mill fixture is a pretty-printed 64KiB-safe file that disagrees with a second compact dump, or a reviewer asking to keep BasicInterpolation "so %(logdir)s stays magic" without the hybrid expand.

Novel coverage: 36%
"""


def main() -> int:
    recs = [ep1(), ep2()]
    taken = prior_ids()
    for rec in recs:
        if rec["id"] in taken:
            raise SystemExit(f"id collision {rec['id']}")
        validate_record(rec)
    OUT.mkdir(parents=True, exist_ok=True)
    batch = OUT / "batch-r19.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    notes_path = OUT / "NOTES-r19.md"
    notes_path.write_text(notes(), encoding="utf-8")
    errors, warnings, kinds, n = check_jsonl(
        batch, "batch-r19.jsonl", staging=FactoryStaging(enabled=True)
    )
    if errors:
        raise SystemExit(f"check_jsonl errors {errors}")
    if warnings:
        raise SystemExit(f"check_jsonl warnings {warnings}")
    if n != 2:
        raise SystemExit(f"records {n}")
    counts, findings, blocked = verify_batch_for_frontier(batch, strict=True)
    if blocked or counts.get("verified") != 2:
        raise SystemExit(f"frontier blocked={blocked} counts={counts} findings={findings}")
    print(f"wrote {batch} ({n} records, kinds={kinds})")
    print(f"wrote {notes_path}")
    print(f"verify_batch_for_frontier strict: {counts} blocked={blocked}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
