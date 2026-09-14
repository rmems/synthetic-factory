#!/usr/bin/env python3
"""Generate designed ACTF r63 episodes (Q=2). Live-tree writes are create-only."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/sf-window/pipelines")
sys.path.insert(0, "/home/raulmc/rmems/synthetic-factory/pipelines")

from check_records import FactoryStaging, check_jsonl  # noqa: E402
from round_txn_coverage import (  # noqa: E402
    has_long_horizon_debug_loop,
    sparse_step_progress_errors,
)
from validate_run import check_episode  # noqa: E402
from verify_execution import verify_batch_for_frontier  # noqa: E402

OUT = Path("/tmp/actf-r63")
LIVE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/"
    "2026-09-02-final-heavy/agentic-coding-trajectory-factory"
)
FORBIDDEN_TREES = (
    Path("/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-08-17"),
    Path("/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-08-30"),
)
GENERATED_AT = "2026-09-02T19:45:00Z"
ROUND = 63
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
ID1 = "act-r63-pem-decode-rest-egretcert-a4c81e"
ID2 = "act-r63-tofu-moved-block-wigeonlb-e7b204"
PLANT_TOKENS = ("egretcert", "egretfen", "wigeonlb", "wigfen")


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
        "round": ROUND,
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "sim_or_real": "designed",
        "training_ready": False,
        "rights": rights(),
    }
    m.update(extra)
    return m


def prior_ids() -> set[str]:
    found: set[str] = set()
    self_batch = (OUT / "batch-r63.jsonl").resolve()
    live_batch = (LIVE / "batch-r63.jsonl").resolve()
    skip = {self_batch, live_batch}
    for path in sorted(Path("/tmp").glob("actf-r*/batch-r*.jsonl")):
        if path.resolve() in skip:
            continue
        for line in path.read_text(encoding="utf-8").split("\n"):
            if not line.strip():
                continue
            rec = json.loads(line)
            rid = rec.get("id")
            if isinstance(rid, str) and rid.strip():
                found.add(rid.strip())
    if LIVE.is_dir():
        for path in LIVE.glob("batch-r*.jsonl"):
            if path.resolve() in skip:
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                rid = rec.get("id")
                if rid:
                    found.add(rid)
    id_re = re.compile(r'ID[12] = "(act[^"]+)"')
    for path in sorted(Path("/tmp").glob("actf-r*/gen.py")):
        if path.resolve().parent == OUT.resolve():
            continue
        found.update(id_re.findall(path.read_text(encoding="utf-8")))
    mill = Path("/home/raulmc/rmems/synthetic-factory/outputs/raw")
    if mill.is_dir():
        for path in mill.glob("**/agentic-coding-trajectory-factory/batch-r*.jsonl"):
            if path.resolve() in skip:
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                rid = rec.get("id")
                if rid:
                    found.add(rid)
    return found


def prior_plant_hits() -> list[str]:
    hits: list[str] = []
    self_dir = OUT.resolve()
    paths = list(Path("/tmp").glob("actf-r*/*"))
    mill = Path("/home/raulmc/rmems/synthetic-factory/outputs/raw")
    if mill.is_dir():
        paths.extend(mill.glob("**/agentic-coding-trajectory-factory/*"))
    if LIVE.is_dir():
        paths.extend(LIVE.glob("*"))
    for path in sorted(paths):
        if not path.is_file():
            continue
        if path.resolve().parent == self_dir:
            continue
        if path.suffix not in {".jsonl", ".md", ".py"}:
            continue
        blob = path.read_text(encoding="utf-8", errors="replace").lower()
        for token in PLANT_TOKENS:
            if token in blob:
                hits.append(f"{path}:{token}")
    return hits


def ep1() -> dict:
    """egretcert-harbor: pem.Decode keeps only the first TLS block."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: EG-630 reports harbor TLS copies print only the leaf CN while dest names are berth.egretfen.internal plus Harbor Intermediate. Search DecodePEMs as evidence of a dropped rest block."
            ),
            "plan": "1) search DecodePEMs 2) read pem.go 3) measure Decode rest 4) confirm want two CNs 5) fix loop 6) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "DecodePEMs|pem.Decode|x509.ParseCertificate|Harbor Intermediate",
                    "path": ".",
                },
            },
            "observation": (
                "egretcert/pem.go:1:package egretcert\n"
                "egretcert/pem.go:9:func DecodePEMs(pemBytes []byte) []*x509.Certificate {\n"
                "egretcert/pem.go:10:    block, _ := pem.Decode(pemBytes)\n"
                "egretcert/pem.go:18:    return []*x509.Certificate{cert}\n"
                "tests/install_test.go:12:    if DecodePEMs(b) == nil { t.Fatal(\"empty\") }\n"
                "5 matches"
            ),
            "reflection": "Found DecodePEMs calling pem.Decode once and discarding rest. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: pem.go:10 calls pem.Decode once and discards rest (step 1). Read the helper as evidence of any loop over leftover blocks."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "egretcert/pem.go", "offset": 1, "limit": 22},
            },
            "observation": (
                "1  package egretcert\n"
                "2\n"
                "3  import (\n"
                "4      \"crypto/x509\"\n"
                "5      \"encoding/pem\"\n"
                "6  )\n"
                "7\n"
                "8  // Harbor TLS copies must keep leaf plus intermediate, not only the first PEM.\n"
                "9  func DecodePEMs(pemBytes []byte) []*x509.Certificate {\n"
                "10     block, _ := pem.Decode(pemBytes)\n"
                "11     if block == nil {\n"
                "12         return nil\n"
                "13     }\n"
                "14     cert, err := x509.ParseCertificate(block.Bytes)\n"
                "15     if err != nil {\n"
                "16         return nil\n"
                "17     }\n"
                "18     return []*x509.Certificate{cert}\n"
                "19 }\n"
            ),
            "reflection": "Learned DecodePEMs returns a one-cert slice and never walks rest. First plan: S3 truncated the intermediate. Next measure Decode rest.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: DecodePEMs returns only the first parsed cert (step 2). Measure pem.Decode rest as evidence a second BEGIN CERTIFICATE remains."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "go env GOOS GOARCH && python3 -c \"print('probe')\" && "
                        "go test -c -o /dev/null ./egretcert 2>&1 | tail -n 5; cat <<'EOF' | go run -\n"
                        "package main\n"
                        "import (\n"
                        "  \"encoding/pem\"\n"
                        "  \"fmt\"\n"
                        "  \"os\"\n"
                        ")\n"
                        "func main() {\n"
                        "  b, _ := os.ReadFile(\"testdata/harbor.pem\")\n"
                        "  block, rest := pem.Decode(b)\n"
                        "  fmt.Printf(\"type=%s rest_has_begin=%v rest_n=%d\\n\", block.Type, "
                        "len(rest)>0 && string(rest)[stringsIndex(string(rest)):], len(rest))\n"
                        "}\n"
                        "func stringsIndex(s string) int { for i := 0; i+5 <= len(s); i++ { "
                        "if s[i:i+5]==\"BEGIN\" { return i } }; return 0 }\n"
                        "EOF"
                    )
                },
            },
            "observation": (
                "linux amd64\n"
                "probe\n"
                "type=CERTIFICATE rest_has_begin=true rest_n=612"
            ),
            "reflection": "Measured pem.Decode rest_n=612 still containing BEGIN. Next confirm the dest want CNs still list leaf plus intermediate.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Reflection: pem.Decode left rest_n=612 with BEGIN (step 3). Fetch encoding/pem notes via gh as evidence of the rest loop vs TrimSpace."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/golang/go/contents/src/encoding/pem/pem.go",
                },
            },
            "observation": (
                "HTTP/2 429\n"
                "retry-after: 5\n"
                "x-ratelimit-limit: 60\n"
                "x-ratelimit-remaining: 0\n"
                '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=5",'
                '"documentation_url":"https://docs.github.com/rest/overview/rate-limits"}'
            ),
            "reflection": "GitHub returned 429 with retry-after 5 while fetching pem docs. Wait, then use the vendored docs/pem-decode-rest.md fixture.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/pem-decode-rest.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/pem-decode-rest.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  pem.Decode returns the first block and leftover rest; a second Decode is required for the intermediate.\n"
                "2  bytes.TrimSpace(rest) still leaves DecodePEMs returning a one-cert slice.\n"
                "3  Durable: loop pem.Decode until rest is empty so leaf plus Harbor Intermediate both parse.\n"
                "4  Dropping the intermediate loses berth.egretfen.internal chain verify.\n"
                "5  A truncated S3 object is independent of this client rest walk.\n"
                "6  testdata/harbor.pem already concatenates two CERTIFICATE blocks.\n"
            ),
            "reflection": "Verified the one-shot Decode trap and that TrimSpace still keeps one cert. Next pull the committed harbor-certs fixture.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: RFC-style notes say harbor TLS needs leaf plus intermediate (step 5). Get the committed cert object as evidence the want set is two CNs."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "egretfen-specs",
                        "--key",
                        "egretcert/harbor-certs.json",
                        "/tmp/egretcert-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-north-1.amazonaws.com/egretfen-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. "
                "reset reason: connection failure"
            ),
            "reflection": "Harbor-certs inventory get-object hit 502 on the ELB before headers. Retry against the committed fixtures/harbor-certs.json instead of the edge.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: harbor-certs inventory get-object returned 502 from the ELB (step 6). jq fixtures/harbor-certs.json want as local-spec evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{want:.want, stale:.stale_path, n:.dest_count, path:.path}",
                        "fixtures/harbor-certs.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "want": {\n'
                '    "leaf": "berth.egretfen.internal",\n'
                '    "intermediate": "Harbor Intermediate",\n'
                '    "n": 2\n'
                "  },\n"
                '  "stale": "fixtures/harbor-certs.stale.json",\n'
                '  "n": 2,\n'
                '  "path": "testdata/harbor.pem"\n'
                "}\n"
                "wrote /tmp/egretcert-inventory.json"
            ),
            "reflection": "Verified want already lists leaf plus Harbor Intermediate. Next join that with the stale one-CN document.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: fixture want already lists two CNs (step 7). jq the measured one-cert Decode against that spec as evidence whether S3 truncated the bundle."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/harbor-certs.json",
                        "--slurpfile",
                        "k",
                        "fixtures/harbor-certs.stale.json",
                        '{got:"DecodePEMs n=1 CN=berth.egretfen.internal",want:$s[0].want,stale:$k[0].want,n:$s[0].dest_count,path:$s[0].path}',
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "got": "DecodePEMs n=1 CN=berth.egretfen.internal",\n'
                '  "want": {\n'
                '    "leaf": "berth.egretfen.internal",\n'
                '    "intermediate": "Harbor Intermediate",\n'
                '    "n": 2\n'
                "  },\n"
                '  "stale": {\n'
                '    "leaf": "berth.egretfen.internal",\n'
                '    "n": 1\n'
                "  },\n"
                '  "n": 2,\n'
                '  "path": "testdata/harbor.pem"\n'
                "}"
            ),
            "reflection": (
                "Plan change: harbor want CNs already list leaf plus Harbor Intermediate and got is one-shot pem.Decode on a committed two-block pem. "
                "Abandon truncated-object. Switching the edit target to DecodePEMs so rest is walked until empty."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the truncated-object plan; DecodePEMs still keeps one cert (step 8). Edit TrimSpace rest as evidence only whitespace is dropped."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "egretcert/pem.go",
                    "old_string": (
                        "    block, _ := pem.Decode(pemBytes)\n"
                        "    if block == nil {\n"
                        "        return nil\n"
                        "    }\n"
                    ),
                    "new_string": (
                        "    block, rest := pem.Decode(pemBytes)\n"
                        "    rest = bytes.TrimSpace(rest)\n"
                        "    _ = rest\n"
                        "    if block == nil {\n"
                        "        return nil\n"
                        "    }\n"
                    ),
                },
            },
            "observation": (
                "Edited egretcert/pem.go: DecodePEMs now TrimSpace(rest) after the first pem.Decode so leftover whitespace is dropped but the slice stays one cert."
            ),
            "reflection": "Wrote a rest-trim. Add a go test that requires n=2 and Harbor Intermediate.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: DecodePEMs now TrimSpace(rest) after one Decode (step 9). Write a go test as evidence that harbor TLS copies keep both CNs."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "egretcert/pem_test.go",
                    "content": (
                        "package egretcert\n"
                        "\n"
                        "import (\n"
                        "    \"os\"\n"
                        "    \"testing\"\n"
                        ")\n"
                        "\n"
                        "func TestDecodePEMsHarborBundle(t *testing.T) {\n"
                        "    b, err := os.ReadFile(\"../testdata/harbor.pem\")\n"
                        "    if err != nil {\n"
                        "        t.Fatal(err)\n"
                        "    }\n"
                        "    certs := DecodePEMs(b)\n"
                        "    if len(certs) != 2 {\n"
                        "        t.Fatalf(\"got n=%d want 2\", len(certs))\n"
                        "    }\n"
                        "    if certs[0].Subject.CommonName != \"berth.egretfen.internal\" {\n"
                        "        t.Fatalf(\"got leaf %q\", certs[0].Subject.CommonName)\n"
                        "    }\n"
                        "    if certs[1].Subject.CommonName != \"Harbor Intermediate\" {\n"
                        "        t.Fatalf(\"got inter %q\", certs[1].Subject.CommonName)\n"
                        "    }\n"
                        "}\n"
                    ),
                },
            },
            "observation": "Wrote egretcert/pem_test.go (24 lines).",
            "reflection": "Created a mixed-bundle regression that expects n=2 and Harbor Intermediate. Run go test to reproduce the one-cert miss.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Plan: run go test ./egretcert as evidence whether TrimSpace(rest) keeps harbor dest CNs as leaf plus Harbor Intermediate."
            ),
            "tool_call": {
                "name": "bash",
                "args": {"command": "go test ./egretcert ./tests -count=1 2>&1 | tail -n 24"},
            },
            "observation": (
                "--- FAIL: TestDecodePEMsHarborBundle (0.00s)\n"
                "    pem_test.go:14: got n=1 want 2\n"
                "FAIL\n"
                "FAIL    git.egretfen.internal/pkg/egretcert-harbor/egretcert    0.03s\n"
                "ok      git.egretfen.internal/pkg/egretcert-harbor/tests        0.01s\n"
                "FAIL"
            ),
            "reflection": "Test failed: TrimSpace still returns n=1. Re-read DecodePEMs and loop pem.Decode until rest is empty.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: go test failed with got n=1 on TrimSpace(rest) (step 11). Re-read DecodePEMs for the rest-walk evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "egretcert/pem.go", "offset": 1, "limit": 22},
            },
            "observation": (
                "1  package egretcert\n"
                "2\n"
                "3  import (\n"
                "4      \"bytes\"\n"
                "5      \"crypto/x509\"\n"
                "6      \"encoding/pem\"\n"
                "7  )\n"
                "8\n"
                "9  // Harbor TLS copies must keep leaf plus intermediate, not only the first PEM.\n"
                "10 func DecodePEMs(pemBytes []byte) []*x509.Certificate {\n"
                "11     block, rest := pem.Decode(pemBytes)\n"
                "12     rest = bytes.TrimSpace(rest)\n"
                "13     _ = rest\n"
                "14     if block == nil {\n"
                "15         return nil\n"
                "16     }\n"
                "17     cert, err := x509.ParseCertificate(block.Bytes)\n"
                "18     if err != nil {\n"
                "19         return nil\n"
                "20     }\n"
                "21     return []*x509.Certificate{cert}\n"
                "22 }\n"
            ),
            "reflection": "Confirmed line 21 still returns a one-cert slice. Patch a Decode loop and keep both CNs.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Reflection: DecodePEMs must loop pem.Decode until rest is empty rather than TrimSpace (step 12). Patch pem.go as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "egretcert/pem.go",
                    "old_string": (
                        "  import (\n"
                        "      \"bytes\"\n"
                        "      \"crypto/x509\"\n"
                        "      \"encoding/pem\"\n"
                        "  )\n"
                        "\n"
                        "  // Harbor TLS copies must keep leaf plus intermediate, not only the first PEM.\n"
                        "  func DecodePEMs(pemBytes []byte) []*x509.Certificate {\n"
                        "      block, rest := pem.Decode(pemBytes)\n"
                        "      rest = bytes.TrimSpace(rest)\n"
                        "      _ = rest\n"
                        "      if block == nil {\n"
                        "          return nil\n"
                        "      }\n"
                        "      cert, err := x509.ParseCertificate(block.Bytes)\n"
                        "      if err != nil {\n"
                        "          return nil\n"
                        "      }\n"
                        "      return []*x509.Certificate{cert}\n"
                        "  }\n"
                    ),
                    "new_string": (
                        "  import (\n"
                        "      \"crypto/x509\"\n"
                        "      \"encoding/pem\"\n"
                        "      \"fmt\"\n"
                        "  )\n"
                        "\n"
                        "  // Harbor TLS copies must keep leaf plus intermediate, not only the first PEM.\n"
                        "  func DecodePEMs(pemBytes []byte) []*x509.Certificate {\n"
                        "      var certs []*x509.Certificate\n"
                        "      rest := pemBytes\n"
                        "      for {\n"
                        "          block, next := pem.Decode(rest)\n"
                        "          if block == nil {\n"
                        "              break\n"
                        "          }\n"
                        "          cert, err := x509.ParseCertificate(block.Bytes)\n"
                        "          if err != nil {\n"
                        "              panic(fmt.Errorf(\"harbor pem: %w\", err))\n"
                        "          }\n"
                        "          certs = append(certs, cert)\n"
                        "          rest = next\n"
                        "      }\n"
                        "      return certs\n"
                        "  }\n"
                    ),
                },
            },
            "observation": (
                "Edited egretcert/pem.go: DecodePEMs now loops pem.Decode until rest is empty so n=1 bins to leaf plus Harbor Intermediate."
            ),
            "reflection": "Patched the rest-walk constructor. Re-run go test; CNs should stay n=2.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: DecodePEMs now loops pem.Decode until rest is empty (step 13). Re-run go test as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {"command": "go test ./egretcert ./tests -count=1 2>&1 | tail -n 12"},
            },
            "observation": (
                "ok      git.egretfen.internal/pkg/egretcert-harbor/egretcert    0.04s\n"
                "ok      git.egretfen.internal/pkg/egretcert-harbor/tests        0.01s\n"
                "PASS\n"
                "6 passed in 0.05s"
            ),
            "reflection": "Verified 6 passed including TestDecodePEMsHarborBundle. Open the EG-630 PR.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: go test passed 6/6 after the pem.Decode loop patch (step 14). Create the EG-630 PR via gh as evidence of the DecodePEMs fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/egretfen/egretcert-harbor/pulls",
                    "raw_field": (
                        "title=EG-630: loop pem.Decode rest so harbor TLS copies keep leaf plus Harbor Intermediate"
                    ),
                },
            },
            "observation": (
                "{\n"
                '  "number": 631,\n'
                '  "html_url": "https://git.egretfen.internal/pkg/egretcert-harbor/pull/631",\n'
                '  "state": "open"\n'
                "}"
            ),
            "reflection": "Opened PR 631. DecodePEMs keeps n=2 and Harbor Intermediate. Live TLS copies remain a follow-up against the designed harbor host.",
        },
    ]
    return {
        "id": ID1,
        "goal": (
            "EG-630 (egretcert-harbor, Go 1.22 harbor TLS PEM helper + fixtures/harbor-certs.json; go test): "
            "nightly harbor copies print only CN=berth.egretfen.internal while dest names are leaf/intermediate, "
            "n=2, testdata/harbor.pem (two concatenated CERTIFICATE blocks). Find why DecodePEMs drops rest, "
            "add a mixed-bundle regression, and open a PR. Designed plant; not a live harbor apply."
        ),
        "steps": steps,
        "outcome": (
            "DecodePEMs called pem.Decode once and discarded rest, so testdata/harbor.pem printed only the leaf CN. "
            "A first patch that used bytes.TrimSpace(rest) still failed TestDecodePEMsHarborBundle (got n=1). "
            "DecodePEMs now loops pem.Decode until rest is empty. Verified by go test 6 passed "
            "(egretcert/pem_test.go::TestDecodePEMsHarborBundle). PR 631 opened. Live TLS copies remain a "
            "follow-up against the designed harbor host."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "pem_decode_rest_fix": 0.12,
            "mixed_bundle_pem_test": 0.08,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.58,
            "aggregation": (
                "unweighted sum of the numeric components above (success is a boolean label, not a summand); "
                "rounding_decimals 2"
            ),
            "cost": {
                "tests_passed": 6,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 28,
            },
        },
        "meta": meta_common(
            codebase_type="library / harbor TLS PEM copies (Go 1.22 encoding/pem)",
            bug_class=(
                "schema mismatch: pem.Decode kept only the first CERTIFICATE block; first fix "
                "bytes.TrimSpace(rest) still returned n=1"
            ),
            test_harness="go test + aws s3api + jq",
            noise_steps={"429": 4, "502": 6},
            noise_recovery_steps={"429": 5, "502": 7},
            plan_change_step=8,
            debug_loop_steps=[9, 10, 11, 12, 13, 14],
            tags=[
                "encoding/pem",
                "pem.Decode",
                "x509.ParseCertificate",
                "harbor-tls",
                "mixed-bundle",
            ],
        ),
    }


def ep2() -> dict:
    """wigeonlb-harbor: renaming aws_lb.berth without a moved block."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: WG-72 reports the harbor NLB was destroyed when aws_lb.berth was renamed aws_lb.harbor. Search moved and prevent_destroy as evidence of a replace apply."
            ),
            "plan": "1) search lb.tf 2) read resource 3) measure live state 4) fix moved 5) regression 6) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "aws_lb|moved|prevent_destroy|berth|harbor",
                    "path": ".",
                },
            },
            "observation": (
                "lb.tf:4:  resource \"aws_lb\" \"harbor\" {\n"
                "lb.tf:6:    name               = \"wigeon-harbor\"\n"
                "variables.tf:4:  # was aws_lb.berth in v1\n"
                "tests/lb.tftest.hcl:3:run \"moved_lb\" {\n"
                "6 matches"
            ),
            "reflection": "Found aws_lb.harbor with no moved block from aws_lb.berth. Next read the stack.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: lb.tf:4 declares aws_lb.harbor while comments say v1 was aws_lb.berth (step 1). Read the stack as evidence of any moved block."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "lb.tf", "offset": 1, "limit": 18},
            },
            "observation": (
                "1  # Ported from the v1 harbor NLB. Renaming aws_lb.berth must not replace the ARN.\n"
                "2  # Harvest listeners still attach to the existing network load balancer.\n"
                "3\n"
                "4  resource \"aws_lb\" \"harbor\" {\n"
                "5    name               = \"wigeon-harbor\"\n"
                "6    load_balancer_type = \"network\"\n"
                "7    internal           = true\n"
                "8    subnets            = var.berth_subnets\n"
                "9  }\n"
            ),
            "reflection": "Learned the stack declares aws_lb.harbor with no moved block. First plan: remote state is stale so berth still looks live. Next measure live state.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: aws_lb.harbor is declared without a moved block (step 2). tofu state pull as evidence of live NLB addresses."
            ),
            "tool_call": {
                "name": "tofu",
                "args": {
                    "argv": [
                        "state",
                        "pull",
                        "-backend-config=bucket=wigfen-tfstate",
                    ]
                },
            },
            "observation": (
                "Failed to load state: Error loading state: "
                "s3.eu-north-1.amazonaws.com/wigfen-tfstate\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. "
                "reset reason: connection failure"
            ),
            "reflection": "S3 backend returned 502 before headers. Retry against the committed terraform.tfstate fixture and write it locally.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: tofu state pull returned 502 from the S3 backend (step 3). jq terraform.tfstate and write /tmp/wigeonlb-state.json as evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{resources:[.resources[]|{type,name,instances:[.instances[]|{index:.index_key,id:.attributes.id,Name:.attributes.name}]}]}",
                        "terraform.tfstate",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "resources": [{\n'
                '    "type": "aws_lb",\n'
                '    "name": "berth",\n'
                '    "instances": [\n'
                '      {"index": null, "id": "arn:aws:elasticloadbalancing:eu-north-1:1:loadbalancer/net/wigeon-harbor/abc", "Name": "wigeon-harbor"}\n'
                "    ]\n"
                "  }]\n"
                "}\n"
                "wrote /tmp/wigeonlb-state.json"
            ),
            "reflection": "Measured live address as aws_lb.berth while config names harbor. Next tflint the stack so a replace plan can be checked.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: live state still addresses aws_lb.berth (step 4). tflint lb.tf as evidence whether a rename without moved will replace the NLB."
            ),
            "tool_call": {
                "name": "tflint",
                "args": {
                    "argv": [
                        "--recursive",
                        "--filter=lb.tf",
                    ]
                },
            },
            "observation": (
                "lb.tf:4:4: Warning: resource \"aws_lb\" \"harbor\" has no moved block from aws_lb.berth "
                "(terraform_moved_block)\n"
                "1 issue(s) found"
            ),
            "reflection": "Found terraform_moved_block on the harbor NLB. Confirm the keep-ARN contract next.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: tflint flagged terraform_moved_block on aws_lb.harbor (step 5). Fetch moved-block docs via gh as evidence of the keep-address contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/hashicorp/terraform/contents/website/docs/language/moved.mdx",
                },
            },
            "observation": (
                "HTTP/2 429\n"
                "retry-after: 7\n"
                "x-ratelimit-limit: 60\n"
                "x-ratelimit-remaining: 0\n"
                '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=7",'
                '"documentation_url":"https://docs.github.com/rest/overview/rate-limits"}'
            ),
            "reflection": "GitHub returned 429 with retry-after 7 while fetching moved docs. Wait, then use the vendored docs/moved-block.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/moved-block.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/moved-block.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  Renaming aws_lb.berth to aws_lb.harbor without moved { from, to } plans destroy+create.\n"
                "2  lifecycle.prevent_destroy on aws_lb.harbor still plans destroy of aws_lb.berth.\n"
                "3  Durable: moved { from = aws_lb.berth to = aws_lb.harbor } so the ARN stays.\n"
                "4  tofu state rm of aws_lb.berth fail-opens harbor harvest listeners.\n"
                "5  Copying the ARN into a new resource still replaces the object in AWS.\n"
                "6  Remote-state lag is independent of this address rename.\n"
            ),
            "reflection": "Verified harbor NLBs need a moved block keyed by the old address. Next join that with the saved state.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs require moved from aws_lb.berth to aws_lb.harbor (step 7). jq spec from the saved state as evidence of the live skew."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{type:.resources[0].type,name:.resources[0].name,id:.resources[0].instances[0].id,n:(.resources[0].instances|length)}",
                        "/tmp/wigeonlb-state.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "type": "aws_lb",\n'
                '  "name": "berth",\n'
                '  "id": "arn:aws:elasticloadbalancing:eu-north-1:1:loadbalancer/net/wigeon-harbor/abc",\n'
                '  "n": 1\n'
                "}"
            ),
            "reflection": (
                "Plan change: live state still has aws_lb.berth while config declares aws_lb.harbor, which is a rename replace not a stale backend. "
                "Abandon remounting remote state. Switching the edit target to lb.tf so the harbor NLB gets a moved block."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the stale-backend plan; config still creates aws_lb.harbor (step 8). Refuse state rm as evidence the berth object must stay."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "tofu state rm aws_lb.berth so a freshly created aws_lb.harbor picks a new ARN",
                    "policy": "FS-MUTATE-04",
                    "incident": "WG-72",
                },
            },
            "observation": (
                "refused: FS-MUTATE-04 forbids removing aws_lb.berth to skip a rename replace. "
                "state rm would drop in-flight harbor harvest listeners and can fail-open berth coverage. "
                "Safe alternative: patch a moved block and keep the existing NLB. found 0 waivers"
            ),
            "reflection": "Denied the state rm. Next patch lb.tf; keep the NLB object.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: state rm is refused; edit target is aws_lb.harbor (step 9). First patch: set prevent_destroy as evidence the NLB may stay put."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "lb.tf",
                    "old_string": (
                        "    internal           = true\n"
                        "    subnets            = var.berth_subnets\n"
                    ),
                    "new_string": (
                        "    internal           = true\n"
                        "    subnets            = var.berth_subnets\n"
                        "    lifecycle {\n"
                        "      prevent_destroy = true\n"
                        "    }\n"
                    ),
                },
            },
            "observation": (
                "Edited lb.tf: aws_lb.harbor now sets lifecycle.prevent_destroy so tofu destroy cannot drop the new address."
            ),
            "reflection": "Wrote a prevent_destroy floor. Add a tofu test that requires no destroy of aws_lb.berth.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: renderer now emits prevent_destroy on aws_lb.harbor (step 10). Write a tofu test as evidence that harbor NLBs keep the berth address without a replace."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/lb.tftest.hcl",
                    "content": (
                        "run \"moved_lb\" {\n"
                        "  command = plan\n"
                        "  assert {\n"
                        "    condition     = aws_lb.harbor.name == \"wigeon-harbor\"\n"
                        "    error_message = \"got name=${aws_lb.harbor.name} want wigeon-harbor\"\n"
                        "  }\n"
                        "  assert {\n"
                        "    condition     = length([for ch in plan.resource_changes : ch if ch.address == \"aws_lb.berth\" && contains(ch.change.actions, \"delete\")]) == 0\n"
                        "    error_message = \"got destroy=aws_lb.berth want moved to aws_lb.harbor\"\n"
                        "  }\n"
                        "}\n"
                    ),
                },
            },
            "observation": "Wrote tests/lb.tftest.hcl (11 lines).",
            "reflection": "Created a moved-lb regression. Run tofu test to reproduce the berth destroy.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Plan: run tofu test as evidence whether prevent_destroy on aws_lb.harbor satisfies the keep-ARN contract."
            ),
            "tool_call": {
                "name": "tofu",
                "args": {
                    "argv": [
                        "test",
                        "-filter=tests/lb.tftest.hcl",
                    ]
                },
            },
            "observation": (
                "tests/lb.tftest.hcl... fail\n"
                "run \"moved_lb\" failed\n"
                "Assertion: got destroy=aws_lb.berth want moved to aws_lb.harbor\n"
                "Error: destroy actions still include aws_lb.berth\n"
                "1 failed in 0.9s"
            ),
            "reflection": "Test failed: prevent_destroy still plans destroy of aws_lb.berth. Re-read lb.tf and add a moved block.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: tofu test failed with got destroy=aws_lb.berth on prevent_destroy (step 12). Re-read lb.tf for the rename evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "lb.tf", "offset": 4, "limit": 14},
            },
            "observation": (
                "4  resource \"aws_lb\" \"harbor\" {\n"
                "5    name               = \"wigeon-harbor\"\n"
                "6    load_balancer_type = \"network\"\n"
                "7    internal           = true\n"
                "8    subnets            = var.berth_subnets\n"
                "9    lifecycle {\n"
                "10     prevent_destroy = true\n"
                "11   }\n"
                "12 }\n"
            ),
            "reflection": "Confirmed prevent_destroy sits on the new address while state still holds aws_lb.berth. Patch a moved block and keep the NLB.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: helper must emit moved from aws_lb.berth to aws_lb.harbor (step 13). Patch lb.tf spec as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "lb.tf",
                    "old_string": (
                        "  resource \"aws_lb\" \"harbor\" {\n"
                        "    name               = \"wigeon-harbor\"\n"
                        "    load_balancer_type = \"network\"\n"
                        "    internal           = true\n"
                        "    subnets            = var.berth_subnets\n"
                        "    lifecycle {\n"
                        "      prevent_destroy = true\n"
                        "    }\n"
                        "  }\n"
                    ),
                    "new_string": (
                        "  moved {\n"
                        "    from = aws_lb.berth\n"
                        "    to   = aws_lb.harbor\n"
                        "  }\n"
                        "\n"
                        "  resource \"aws_lb\" \"harbor\" {\n"
                        "    name               = \"wigeon-harbor\"\n"
                        "    load_balancer_type = \"network\"\n"
                        "    internal           = true\n"
                        "    subnets            = var.berth_subnets\n"
                        "  }\n"
                    ),
                },
            },
            "observation": (
                "Edited lb.tf: moved from aws_lb.berth to aws_lb.harbor and prevent_destroy is gone."
            ),
            "reflection": "Patched the moved block and kept one NLB object. Re-run tofu test; berth should not destroy.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: helper now emits moved from aws_lb.berth to aws_lb.harbor (step 14). Re-run tofu test as verification evidence."
            ),
            "tool_call": {
                "name": "tofu",
                "args": {
                    "argv": [
                        "test",
                        "-filter=tests/lb.tftest.hcl",
                    ]
                },
            },
            "observation": (
                "tests/lb.tftest.hcl... pass\n"
                "tests/install.tftest.hcl... pass\n"
                "5 passed in 1.1s"
            ),
            "reflection": "Verified 5 passed including moved_lb. Check gate-cli before applying the stack.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: tofu test passed 5/5 after the moved-block patch (step 15). Run gate-cli check apply as evidence whether prod stack mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "wigeonlb-moved-block",
                        "--resource",
                        "aws_lb.harbor",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change wigeonlb-moved-block\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: WG-60\n"
                "until: 2026-09-16T00:00:00Z\n"
                "evidence: change mutates aws_lb.harbor (wigeonlb-harbor berth to harbor moved)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under WG-60 freeze through 2026-09-16. Do not tofu apply. Open a handoff issue attaching the moved-block fix.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the stack apply under freeze WG-60 (step 16). Open a handoff issue as evidence the live state still has aws_lb.berth."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "WG-83: apply wigeonlb moved block after WG-60 freeze (blocks WG-72 close)",
                    "body": (
                        "lb.tf now emits moved from aws_lb.berth to aws_lb.harbor; tofu test 5 passed. "
                        "Live state still has aws_lb.berth. gate-cli freeze WG-60 until 2026-09-16. "
                        "Do not tofu state rm the NLB."
                    ),
                },
            },
            "observation": "https://git.wigfen.internal/iac/wigeonlb-harbor/issues/83",
            "reflection": "Opened WG-83. Stack tests are green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": ID2,
        "goal": (
            "WG-72 (wigeonlb-harbor, OpenTofu 1.8 aws_lb stack + kind-less wigfen; tofu test + tflint): "
            "harbor NLB was replaced when aws_lb.berth was renamed aws_lb.harbor because the stack had no moved block. "
            "Find why the rename destroys the ARN, fix the stack, and apply or hand off. Designed plant; not a live AWS apply."
        ),
        "steps": steps,
        "outcome": (
            "lb.tf declared aws_lb.harbor with no moved block, so tofu planned destroy of aws_lb.berth. "
            "A first patch that set lifecycle.prevent_destroy on aws_lb.harbor still failed tests/lb.tftest.hcl "
            "(got destroy=aws_lb.berth). The stack now emits moved from aws_lb.berth to aws_lb.harbor; tofu test 5 passed. "
            "Applying aws_lb.harbor remains blocked by gate-cli freeze WG-60; live state still has aws_lb.berth. "
            "WG-83 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "moved_block_fix": 0.10,
            "moved_lb_test": 0.08,
            "prod_apply_blocked_penalty": -0.12,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.28,
            "aggregation": (
                "unweighted sum of the numeric components above (success is a boolean label, not a summand); "
                "rounding_decimals 2"
            ),
            "cost": {
                "tests_passed": 5,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 3,
                "duration_min": 35,
                "prod_apply": 0,
            },
        },
        "meta": meta_common(
            codebase_type="CLI / OpenTofu aws_lb harbor stack (HCL + tofu test)",
            bug_class=(
                "schema mismatch: renaming aws_lb.berth to aws_lb.harbor without moved planned destroy+create; "
                "first fix lifecycle.prevent_destroy on harbor and still destroyed berth"
            ),
            test_harness="tofu test + tflint + gate-cli",
            noise_steps={"502": 3, "429": 6},
            noise_recovery_steps={"502": 4, "429": 7},
            plan_change_step=8,
            debug_loop_steps=[10, 11, 12, 13, 14, 15],
            tags=[
                "opentofu",
                "moved-block",
                "aws_lb",
                "prevent_destroy",
                "gate-cli-freeze",
                "refuse-state-rm",
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
        if not step["observation"].strip():
            raise SystemExit(f"{rec['id']} empty obs {i}")
        if "hypothesis" in step["observation"].lower():
            raise SystemExit(f"{rec['id']} hypothesis in observation {i}")
        db(step["decision_basis"])
        blob = " ".join(
            [
                step["decision_basis"],
                step["observation"],
                step["tool_call"]["name"],
                json.dumps(step["tool_call"]["args"], sort_keys=True),
            ]
        )
        if STALL_RE.search(blob) or not PROGRESS_RE.search(blob):
            raise SystemExit(
                f"{rec['id']} step {i} sparse progress: {step['decision_basis'][:100]!r}"
            )
    obs = [s["observation"] for s in steps]
    n429 = sum("429" in o for o in obs)
    n502 = sum("502" in o for o in obs)
    if n429 != 1 or n502 != 1:
        raise SystemExit(f"{rec['id']} noise counts 429={n429} 502={n502}")
    recov = rec["meta"]["noise_recovery_steps"]
    for code, recov_n in recov.items():
        if code in steps[recov_n - 1]["observation"]:
            raise SystemExit(f"{rec['id']} recovery step {recov_n} repeats {code}")
        if code not in steps[recov_n - 1]["decision_basis"]:
            raise SystemExit(f"{rec['id']} recovery step {recov_n} basis missing {code}")
    reflections = [s.get("reflection", "") for s in steps]
    pivots = [i + 1 for i, r in enumerate(reflections) if "Plan change:" in r or "Pivoting:" in r]
    if pivots != [rec["meta"]["plan_change_step"]]:
        raise SystemExit(f"{rec['id']} plan-change {pivots}")
    pc = rec["meta"]["plan_change_step"]
    if pc in (1, n):
        raise SystemExit(f"{rec['id']} plan-change at end/start")
    nxt = steps[pc]["decision_basis"]
    if "pivot" not in nxt.lower() and "abandon" not in nxt.lower():
        raise SystemExit(f"{rec['id']} next basis missing pivot")
    for path, key, _ in walk_keys(rec):
        norm = re.sub(r"[^a-z0-9]+", "_", key).strip("_").lower()
        if norm in FORBIDDEN or norm.startswith("internal_reasoning"):
            raise SystemExit(f"{rec['id']} forbidden key {path}")
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


def notes() -> str:
    return """# ACTF r63 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r63-pem-decode-rest-egretcert-a4c81e`, `act-r63-tofu-moved-block-wigeonlb-e7b204` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`tofu`/`tflint`/`aws`/`jq`/`refuse`). meta.round=63 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Live-tree write is create-only (`batch-r63.jsonl`); never clobbered `batch-r01.jsonl` / `NOTES-r01.md` / r21 / r41 / r61. Distinct from window r01 (sanderling inclusive-after Rust pager / whimbrel Node inflight Map race), r21 (duration-json-ns / executescript-commit), r41 (unpack-be-le / pvc-rwo), r61 (tzdata-loadlocation / tofu-count-index), from staged r10-r56 mill+k8s plateau, and from r11 gullfeather OpenTofu Route53 ignore_changes + tenv pin (this stack is aws_lb moved, not weighted records or count-index). Addresses r61 NOTES gap (stale 502 fixture whose want disagrees with a second document; leave mill lots and Kubernetes YAML). Invented repos `git.egretfen.internal/pkg/egretcert-harbor.git` and `git.wigfen.internal/iac/wigeonlb-harbor.git`. Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r63-pem-decode-rest-egretcert-a4c81e | Go 1.22 harbor TLS PEM helper + harbor-certs fixtures / go test + aws s3api + jq | schema mismatch: `pem.Decode` kept only the first CERTIFICATE block; first fix `bytes.TrimSpace(rest)` still returned n=1 | success; 6/6; PR 631 | 0.58 |
| act-r63-tofu-moved-block-wigeonlb-e7b204 | OpenTofu 1.8 aws_lb harbor stack / tofu test + tflint + gate-cli | schema mismatch: renaming `aws_lb.berth` to `aws_lb.harbor` without `moved` planned destroy+create; first fix `lifecycle.prevent_destroy` on harbor | incomplete HIL/prod apply; WG-83; freeze WG-60 | 0.28 |

## Step counts, noise, plan change
- act-r63-pem-decode-rest-egretcert-a4c81e: 15 steps. 429 at step 4 (`gh api` golang/go pem.go, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/pem-decode-rest.md`). 502 at step 6 (`aws s3api get-object` egretfen-specs harbor-certs ELB) -> recovery step 7 (`jq` committed `fixtures/harbor-certs.json`). Plan change at step 8: jq join shows want already n=2 leaf+Harbor Intermediate while stale fixture is n=1 and got is one-shot Decode on a committed two-block pem; abandon truncated-object. Debug loop: 9 edit TrimSpace rest -> 10 write mixed-bundle go test -> 11 FAIL got n=1 -> 12 re-read DecodePEMs -> 13 pem.Decode loop patch -> 14 6 passed.
- act-r63-tofu-moved-block-wigeonlb-e7b204: 17 steps. 502 at step 3 (`tofu state pull` S3 backend) -> recovery step 4 (`jq` committed `terraform.tfstate` writes /tmp/wigeonlb-state.json). 429 at step 6 (`gh api` hashicorp/terraform moved.mdx, retry-after 7) -> recovery step 7 (read vendored `docs/moved-block.md`). Plan change at step 8: jq name=berth while config declares aws_lb.harbor; abandon remounting remote state. Debug loop: 10 edit prevent_destroy -> 11 write moved_lb tofu test -> 12 FAIL got destroy=aws_lb.berth -> 13 re-read helper -> 14 moved from berth to harbor -> 15 5 passed. `refuse` at step 9 blocks `tofu state rm`. gate-cli REJECT at 16; WG-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. pem-decode-rest: 0.40+0.12+0.08-0.02=0.58. tofu-moved-block: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: one-shot `pem.Decode` dropping the intermediate is a real encoding/pem footgun; `bytes.TrimSpace(rest)` is the equally tempting leftover-whitespace wrong fix and the mixed-bundle test names the contract (`n=2` plus `Harbor Intermediate`, not leaf-only). Renaming `aws_lb.berth` to `aws_lb.harbor` without `moved` is the usual OpenTofu replace; `lifecycle.prevent_destroy` on the new address still cannot satisfy a test that forbids destroy of `aws_lb.berth`. gate-cli freeze plus refuse-state-rm is an honest apply block, not a silent skip. 502 fallback now compares dest want n=2 against a second stale file still on n=1 (r61 densification). Weak: tofu state dump is one object; no reviewer asking to keep prevent_destroy "so operators can still block tofu destroy from runbooks". Next densification: a reviewer asking to keep TrimSpace "so truncated S3 PEM still parses a leaf", or a 502 whose local tfstate is rewritten after the moved patch and still lists aws_lb.berth as a destroy.

Novel coverage: 44%
"""


def write_create_only(path: Path, text: str) -> Path:
    for forbidden in FORBIDDEN_TREES:
        try:
            path.resolve().relative_to(forbidden.resolve())
        except (ValueError, FileNotFoundError):
            continue
        else:
            raise SystemExit(f"refuse write under {forbidden}: {path}")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(path, flags, 0o644)
    except FileExistsError as exc:
        name = path.name
        if name == "batch-r63.jsonl":
            return write_create_only(path.with_name("batch-r63c.jsonl"), text)
        if name == "NOTES-r63.md":
            return write_create_only(path.with_name("NOTES-r63c.md"), text)
        raise SystemExit(f"refuse overwrite {path}") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def main() -> int:
    plant_hits = prior_plant_hits()
    if plant_hits:
        raise SystemExit(f"plant collision {plant_hits}")
    recs = [ep1(), ep2()]
    taken = prior_ids()
    for rec in recs:
        if rec["id"] in taken:
            raise SystemExit(f"id collision {rec['id']}")
        validate_record(rec)
    OUT.mkdir(parents=True, exist_ok=True)
    if not LIVE.is_dir():
        raise SystemExit(f"live dir missing {LIVE}")
    batch_text = "".join(
        json.dumps(rec, ensure_ascii=True, separators=(",", ":")) + "\n" for rec in recs
    )
    notes_text = notes()
    batch = write_create_only(OUT / "batch-r63.jsonl", batch_text)
    notes_path = write_create_only(OUT / "NOTES-r63.md", notes_text)
    live_batch = write_create_only(LIVE / "batch-r63.jsonl", batch_text)
    live_notes = write_create_only(LIVE / "NOTES-r63.md", notes_text)
    errors, warnings, kinds, n = check_jsonl(
        live_batch, "batch-r63.jsonl", staging=FactoryStaging(enabled=True)
    )
    if errors:
        raise SystemExit(f"check_jsonl errors {errors}")
    if warnings:
        raise SystemExit(f"check_jsonl warnings {warnings}")
    counts, findings, blocked = verify_batch_for_frontier(live_batch, strict=True)
    if blocked or counts.get("verified") != 2:
        raise SystemExit(f"frontier blocked={blocked} counts={counts} findings={findings}")
    print(f"wrote {batch} ({n} records, kinds={kinds})")
    print(f"wrote {notes_path}")
    print(f"wrote {live_batch}")
    print(f"wrote {live_notes}")
    print(f"verify_batch_for_frontier strict: {counts} blocked={blocked}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
