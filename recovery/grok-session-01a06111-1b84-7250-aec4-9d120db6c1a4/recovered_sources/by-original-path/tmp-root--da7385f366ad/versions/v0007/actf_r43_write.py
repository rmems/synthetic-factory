#!/usr/bin/env python3
"""Create-only ACTF r43 writer. Never overwrites existing factory files."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

FAC = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "agentic-coding-trajectory-factory"
)
KNOWN_TOOLS = frozenset(
    {
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
)
HIDDEN = {
    "thought",
    "chain_of_thought",
    "scratch",
    "reasoning",
    "inner_monologue",
    "internal_reasoning",
}
LABELS = ("Plan: ", "Observation: ", "Reflection: ", "Tool call: ")
PROGRESS = re.compile(
    r"\b(?:added|changed|created|deleted|disproved|edited|evidence|failed|"
    r"fixed|found|learned|measured|patched|removed|reproduced|"
    r"tested|updated|verified|wrote|denied|opened|confirmed)\b",
    re.I,
)
RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T19:50:00Z",
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


def db(text: str) -> str:
    text = " ".join(text.split())
    if not text.startswith(LABELS):
        raise SystemExit(f"bad prefix ({len(text)}): {text}")
    if not (80 <= len(text) <= 240):
        raise SystemExit(f"basis len {len(text)}: {text}")
    return text


def step(n, basis, name, args, observation, reflection, plan=None):
    if name not in KNOWN_TOOLS:
        raise SystemExit(f"unknown tool {name}")
    s = {
        "n": n,
        "decision_basis": db(basis),
        "tool_call": {"name": name, "args": args},
        "observation": observation,
        "reflection": reflection,
    }
    if plan is not None:
        s["plan"] = plan
    blob = (observation + " " + reflection).casefold()
    if PROGRESS.search(blob) is None:
        raise SystemExit(f"step {n} missing progress term")
    if "hypothesis" in observation.casefold():
        raise SystemExit(f"step {n} observation has hypothesis")
    return s


def walk_hidden(value, path=""):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).casefold() in HIDDEN or str(key).casefold().startswith(
                "internal_reasoning"
            ):
                raise SystemExit(f"hidden key {path}.{key}")
            walk_hidden(item, f"{path}.{key}")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            walk_hidden(item, f"{path}[{i}]")


def count_status(steps, code):
    hits = []
    for s in steps:
        if re.search(rf"\b{code}\b", s["observation"]):
            hits.append(s["n"])
    return hits


EP1_STEPS = [
    step(
        1,
        "Plan: AV-430 reports mill lot archives print sauger.lot.gz while dest invoices want sauger.lot.tar.gz. Search gzip_lot_archive and with_suffix as evidence of a suffix rewrite.",
        "search",
        {"pattern": "gzip_lot_archive|with_suffix|\\.tar\\.gz", "path": "."},
        "avocetarc/archive.py:6:def gzip_lot_archive(spec: str) -> str:\n"
        "avocetarc/archive.py:8:    return str(Path(spec).with_suffix(\".gz\"))\n"
        "tests/test_install.py:11:    assert gzip_lot_archive(\"X\") == \"X\"\n"
        "5 matches",
        "Found gzip_lot_archive wrapping Path.with_suffix('.gz'). Next read the helper.",
        plan="1) search gzip_lot_archive 2) read archive.py 3) measure with_suffix 4) confirm want sauger.lot.tar.gz 5) fix tar-only gzip 6) regression + PR",
    ),
    step(
        2,
        "Observation: archive.py:8 calls Path.with_suffix('.gz') (step 1). Read the helper as evidence of any .tar.gz keep-path.",
        "read_file",
        {"path": "avocetarc/archive.py", "offset": 1, "limit": 16},
        "1  from pathlib import Path\n"
        "2\n"
        "3  # Harbor mill lot archives sauger.lot.tar must gzip to sauger.lot.tar.gz.\n"
        "4  # Dest invoices are ASCII names in fixtures/archives.ndjson. berth2.json stays json.\n"
        "5\n"
        "6  def gzip_lot_archive(spec: str) -> str:\n"
        "7      # Replace the last suffix so mill PLC names stay dotted.\n"
        "8      return str(Path(spec).with_suffix(\".gz\"))\n",
        "Learned gzip_lot_archive uses with_suffix('.gz') as the rewrite. First plan: S3 truncated names. Next measure with_suffix of sauger.lot.tar.",
    ),
    step(
        3,
        "Observation: gzip_lot_archive uses Path.with_suffix('.gz') (step 2). Measure with_suffix of sauger.lot.tar as evidence of a dropped .tar.",
        "bash",
        {
            "command": "python3 -c \"from pathlib import Path; print(Path('sauger.lot.tar').with_suffix('.gz')); print(Path('rail.lot.tar.gz').with_suffix('.gz')); print(Path('berth2.json').with_suffix('.gz'))\""
        },
        "sauger.lot.gz\nrail.lot.tar.gz\nberth2.gz",
        "Measured with_suffix dropping .tar on sauger.lot.tar and rewriting berth2.json to berth2.gz. Next confirm dest invoices still list sauger.lot.tar.gz.",
    ),
    step(
        4,
        "Reflection: with_suffix dropped .tar on sauger.lot.tar (step 3). Fetch pathlib.rst notes via gh as evidence of suffix replacement vs append.",
        "gh",
        {
            "subcommand": "api",
            "method": "GET",
            "path": "repos/python/cpython/contents/Doc/library/pathlib.rst",
        },
        "HTTP/2 429\n"
        "retry-after: 5\n"
        "x-ratelimit-limit: 60\n"
        "x-ratelimit-remaining: 0\n"
        '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=5","documentation_url":"https://docs.github.com/rest/overview/rate-limits"}',
        "Found GitHub 429 with retry-after 5 while fetching pathlib docs. Wait, then use the vendored docs/with-suffix.md fixture.",
    ),
    step(
        5,
        "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/with-suffix.md as local-docs evidence.",
        "read_file",
        {"path": "docs/with-suffix.md", "offset": 1, "limit": 16},
        "1  Path.with_suffix('.gz') replaces only the last suffix, so sauger.lot.tar becomes sauger.lot.gz.\n"
        "2  spec + '.gz' keeps .tar but turns rail.lot.tar.gz into rail.lot.tar.gz.gz and berth2.json into berth2.json.gz.\n"
        "3  Durable: keep names already ending .tar.gz; append .gz only onto .tar; leave berth2.json alone.\n"
        "4  Dest invoices are ASCII archive names, not last-suffix rewrites.\n",
        "Verified the last-suffix trap and that always-append .gz doubles already-gzipped lots. Next pull the committed lot-archives fixture.",
    ),
    step(
        6,
        "Observation: RFC-style notes say pads need .tar kept before .gz (step 5). Get the committed lot-archives object as evidence the want set is sauger.lot.tar.gz.",
        "aws",
        {
            "argv": [
                "s3api",
                "get-object",
                "--bucket",
                "avocetfen-specs",
                "--key",
                "avocetarc/lot-archives.json",
                "/tmp/avocetarc-inventory.json",
            ]
        },
        "download failed: s3.eu-north-1.amazonaws.com/avocetfen-specs\n"
        "HTTP/1.1 502 Bad Gateway\n"
        "server: awselb/2.0\n"
        "upstream connect error or disconnect/reset before headers. reset reason: connection failure",
        "Measured archive inventory get-object 502 on the ELB before headers. Retry against the committed fixtures/lot-archives.json instead of the edge.",
    ),
    step(
        7,
        "Observation: archive inventory get-object returned 502 from the ELB (step 6). jq fixtures/lot-archives.json and stale sauger.lot.gz as local-spec evidence.",
        "jq",
        {
            "argv": [
                "-n",
                "--slurpfile",
                "w",
                "fixtures/lot-archives.json",
                "--slurpfile",
                "s",
                "fixtures/lot-archives.stale.json",
                "{want:$w[0].want, stale:$s[0].want, path:$w[0].path, n:$w[0].dest_count}",
            ]
        },
        "{\n"
        '  "want": {"sauger.lot.tar": "sauger.lot.tar.gz", "rail.lot.tar.gz": "rail.lot.tar.gz", "berth2.json": "berth2.json"},\n'
        '  "stale": {"sauger.lot.tar": "sauger.lot.gz", "rail.lot.tar.gz": "rail.lot.tar.gz.gz", "berth2.json": "berth2.gz"},\n'
        '  "path": "fixtures/archives.ndjson",\n'
        '  "n": 3\n'
        "}",
        "Verified want already lists sauger.lot.tar.gz and berth2.json while the stale dest still lists sauger.lot.gz. Next join that with the measured with_suffix drop.",
    ),
    step(
        8,
        "Observation: fixture want already lists sauger.lot.tar.gz vs stale sauger.lot.gz (step 7). jq the measured with_suffix drop against that spec as evidence whether S3 truncated names.",
        "jq",
        {
            "argv": [
                "-n",
                "--slurpfile",
                "s",
                "fixtures/lot-archives.json",
                '{got:"gzip_lot_archive with_suffix dropped .tar",want:$s[0].want,stale_disagree:true,path:$s[0].path}',
            ]
        },
        "{\n"
        '  "got": "gzip_lot_archive with_suffix dropped .tar",\n'
        '  "want": {"sauger.lot.tar": "sauger.lot.tar.gz", "rail.lot.tar.gz": "rail.lot.tar.gz", "berth2.json": "berth2.json"},\n'
        '  "stale_disagree": true,\n'
        '  "path": "fixtures/archives.ndjson"\n'
        "}",
        "Plan change: verified dest want archives already list sauger.lot.tar.gz and berth2.json and got is with_suffix dropping .tar on a committed 3-line ndjson. Abandon truncated-inventory. Switching the edit target to gzip_lot_archive so mill lots keep .tar.gz.",
    ),
    step(
        9,
        "Reflection: pivoting off the truncated-inventory plan; gzip_lot_archive still uses with_suffix (step 8). Edit always-append .gz as evidence only the suffix string changes.",
        "edit_file",
        {
            "path": "avocetarc/archive.py",
            "old_string": "    return str(Path(spec).with_suffix(\".gz\"))\n",
            "new_string": "    return spec + \".gz\"\n",
        },
        "Edited avocetarc/archive.py: gzip_lot_archive now uses spec + '.gz' so a .gz is always appended after the current name.",
        "Wrote an always-append gzip. Add a pytest that requires sauger.lot.tar.gz and rail.lot.tar.gz.",
    ),
    step(
        10,
        "Observation: gzip_lot_archive now uses spec + '.gz' (step 9). Write a pytest as evidence that rail.lot.tar.gz stays un-doubled while sauger.lot.tar becomes sauger.lot.tar.gz.",
        "write_file",
        {
            "path": "tests/test_archive.py",
            "content": (
                "from avocetarc.archive import gzip_lot_archive\n\n"
                "WANT = {\n"
                '    "sauger.lot.tar": "sauger.lot.tar.gz",\n'
                '    "rail.lot.tar.gz": "rail.lot.tar.gz",\n'
                '    "berth2.json": "berth2.json",\n'
                "}\n\n"
                "def test_gzip_lot_archive_tar_only():\n"
                "    for src, dest in WANT.items():\n"
                "        assert gzip_lot_archive(src) == dest, (src, gzip_lot_archive(src))\n"
            ),
        },
        "Wrote tests/test_archive.py (12 lines).",
        "Created a mixed-archive regression that expects rail.lot.tar.gz to stay rail.lot.tar.gz. Run pytest to reproduce the double-gz print.",
    ),
    step(
        11,
        "Plan: run pytest tests/test_archive.py as evidence whether always-append .gz keeps dest names as sauger.lot.tar.gz and rail.lot.tar.gz.",
        "bash",
        {"command": "pytest tests/test_archive.py tests/test_install.py -q 2>&1 | tail -n 24"},
        "F.\n"
        "=================================== FAILURES ===================================\n"
        "______________ test_gzip_lot_archive_tar_only ______________\n"
        "tests/test_archive.py:11: in test_gzip_lot_archive_tar_only\n"
        "    assert gzip_lot_archive(src) == dest, (src, gzip_lot_archive(src))\n"
        "E   AssertionError: ('rail.lot.tar.gz', 'rail.lot.tar.gz.gz')\n"
        "E   assert 'rail.lot.tar.gz.gz' == 'rail.lot.tar.gz'\n"
        "FAILED tests/test_archive.py::test_gzip_lot_archive_tar_only\n"
        "1 failed, 1 passed in 0.05s",
        "Test failed: always-append .gz still printed rail.lot.tar.gz.gz. Read the reviewer note, then re-read gzip_lot_archive.",
    ),
    step(
        12,
        "Observation: pytest failed with got rail.lot.tar.gz.gz want rail.lot.tar.gz (step 11). Read docs/review-keep-with-suffix.md as evidence whether reviewers require every name to lose .tar.",
        "read_file",
        {"path": "docs/review-keep-with-suffix.md", "offset": 1, "limit": 12},
        "Reviewer r-arc-04 on AV-241: keep Path.with_suffix('.gz') so mill PLC names never contain two dots before gz.\n"
        "Rejected: dest want is sauger.lot.tar.gz; kiln stamps are ASCII archive names, not last-suffix rewrites.\n"
        "found 0 waivers for keeping with_suffix on .tar lots.\n",
        "Found a reviewer asking to keep with_suffix; dest want sauger.lot.tar.gz still disproves that. Re-read gzip_lot_archive and patch the tar-only append.",
    ),
    step(
        13,
        "Observation: reviewer keep-with-suffix was rejected against dest want sauger.lot.tar.gz (step 12). Re-read gzip_lot_archive for the spec + '.gz' evidence.",
        "read_file",
        {"path": "avocetarc/archive.py", "offset": 1, "limit": 12},
        "1  from pathlib import Path\n"
        "2\n"
        "3  # Harbor mill lot archives sauger.lot.tar must gzip to sauger.lot.tar.gz.\n"
        "4  # Dest invoices are ASCII names in fixtures/archives.ndjson. berth2.json stays json.\n"
        "5\n"
        "6  def gzip_lot_archive(spec: str) -> str:\n"
        "7      # Always append .gz so mill PLC names keep every prior suffix.\n"
        "8      return spec + \".gz\"\n",
        "Confirmed line 8 still appends .gz onto rail.lot.tar.gz so the name doubles. Patch the .tar.gz keep plus .tar-only append.",
    ),
    step(
        14,
        "Reflection: gzip_lot_archive must keep .tar.gz and only append onto .tar rather than spec + '.gz' (step 13). Patch archive.py as evidence.",
        "edit_file",
        {
            "path": "avocetarc/archive.py",
            "old_string": "    return spec + \".gz\"\n",
            "new_string": (
                "    if spec.endswith(\".tar.gz\"):\n"
                "        return spec\n"
                "    if spec.endswith(\".tar\"):\n"
                "        return spec + \".gz\"\n"
                "    return spec\n"
            ),
        },
        "Edited avocetarc/archive.py: gzip_lot_archive now keeps .tar.gz, appends .gz only onto .tar, and leaves berth2.json unchanged.",
        "Patched the tar-only constructor. Re-run pytest; rail.lot.tar.gz should stay rail.lot.tar.gz.",
    ),
    step(
        15,
        "Observation: gzip_lot_archive now keeps .tar.gz and only appends onto .tar (step 14). Re-run pytest as verification evidence.",
        "bash",
        {"command": "pytest tests/test_archive.py tests/test_install.py -q 2>&1 | tail -n 12"},
        "......\n6 passed in 0.04s",
        "Verified 6 passed including test_gzip_lot_archive_tar_only. Open the AV-430 PR.",
    ),
    step(
        16,
        "Observation: pytest passed 6/6 after the tar-only gzip (step 15). Create the AV-430 PR via gh as evidence of the gzip_lot_archive fix.",
        "gh",
        {
            "subcommand": "api",
            "method": "POST",
            "path": "repos/avocetfen/avocetarc-lots/pulls",
            "raw_field": "title=AV-430: gzip only .tar mill lot archives so sauger.lot.tar becomes sauger.lot.tar.gz and rail.lot.tar.gz stays undoubled",
        },
        "{\n"
        '  "number": 431,\n'
        '  "html_url": "https://git.avocetfen.internal/pkg/avocetarc-lots/pull/431",\n'
        '  "state": "open"\n'
        "}",
        "Opened PR 431. gzip_lot_archive keeps sauger.lot.tar.gz and berth2.json. Live mill copies remain a follow-up against the designed harbor host.",
    ),
]

EP2_STEPS = [
    step(
        1,
        "Plan: KD-72 reports mill PLC lot rows split dest harbor-a, quay-b so dest JSON drops the comma field. Search ReadLotRow and encoding/csv as evidence of a comma split.",
        "search",
        {"pattern": "ReadLotRow|csv.NewReader|Comma|LazyQuotes", "path": "."},
        "killdeercsv/lot.go:17:func ReadLotRow(r io.Reader) (LotRow, error) {\n"
        "killdeercsv/lot.go:18:    cr := csv.NewReader(r)\n"
        "killdeercsv/lot.go:19:    rec, err := cr.Read()\n"
        "tests/install_test.go:9:    if _, err := ReadLotRow(strings.NewReader(\"x\")); err == nil { t.Fatal(\"empty\") }\n"
        "6 matches",
        "Found ReadLotRow wrapping csv.NewReader with default Comma. Next read the helper.",
        plan="1) search ReadLotRow 2) read lot.go 3) measure comma split 4) confirm want dest harbor-a, quay-b 5) set Comma semicolon 6) go test + handoff",
    ),
    step(
        2,
        "Observation: lot.go:18 constructs csv.NewReader with default Comma (step 1). Read the helper as evidence of any semicolon Comma.",
        "read_file",
        {"path": "killdeercsv/lot.go", "offset": 1, "limit": 28},
        "1  package killdeercsv\n"
        "2\n"
        "3  import (\n"
        "4      \"encoding/csv\"\n"
        "5      \"io\"\n"
        "6  )\n"
        "7\n"
        "8  // Mill PLC lot rows are semicolon-separated; dest may contain commas.\n"
        "9  // Dest traces are ASCII CSV in fixtures/lots.ndjson.\n"
        "10\n"
        "11 type LotRow struct {\n"
        "12     Lot  string\n"
        "13     Mg   string\n"
        "14     Dest string\n"
        "15 }\n"
        "16\n"
        "17 func ReadLotRow(r io.Reader) (LotRow, error) {\n"
        "18     cr := csv.NewReader(r)\n"
        "19     rec, err := cr.Read()\n"
        "20     if err != nil {\n"
        "21         return LotRow{}, err\n"
        "22     }\n"
        "23     if len(rec) < 3 {\n"
        "24         return LotRow{Lot: rec[0]}, nil\n"
        "25     }\n"
        "26     return LotRow{Lot: rec[0], Mg: rec[1], Dest: rec[2]}, nil\n"
        "27 }\n",
        "Learned ReadLotRow never sets Comma so semicolon mill rows split on comma. First plan: remote mill CSV inventory is stale. Next measure csv.Read.",
    ),
    step(
        3,
        "Observation: ReadLotRow uses csv.NewReader with default Comma (step 2). Measure csv.Read of a semicolon mill row as evidence dest splits on comma.",
        "bash",
        {
            "command": "cat <<'EOF' | go run -\npackage main\nimport (\"encoding/csv\"; \"fmt\"; \"strings\")\nfunc main() {\n  r := csv.NewReader(strings.NewReader(\"sauger;1201;harbor-a, quay-b\\n\"))\n  rec, err := r.Read()\n  fmt.Printf(\"%q %v\\n\", rec, err)\n}\nEOF"
        },
        "[\"sauger;1201;harbor-a\" \" quay-b\"] <nil>",
        "Measured csv.Read splitting dest on the comma inside harbor-a, quay-b. Next confirm dest traces still list one dest field.",
    ),
    step(
        4,
        "Observation: ReadLotRow split dest on comma (step 3). Get the committed lot-rows object as evidence the want dest is harbor-a, quay-b.",
        "aws",
        {
            "argv": [
                "s3api",
                "get-object",
                "--bucket",
                "killdeerfen-specs",
                "--key",
                "killdeercsv/lot-rows.json",
                "/tmp/killdeercsv-inventory.json",
            ]
        },
        "download failed: s3.eu-north-1.amazonaws.com/killdeerfen-specs\n"
        "HTTP/1.1 502 Bad Gateway\n"
        "server: awselb/2.0\n"
        "upstream connect error or disconnect/reset before headers. reset reason: connection failure",
        "Measured lot inventory get-object 502 on the ELB before headers. Retry against the committed fixtures/lot-rows.json instead of the edge.",
    ),
    step(
        5,
        "Observation: lot inventory get-object returned 502 from the ELB (step 4). jq fixtures/lot-rows.json and write /tmp/killdeercsv-rows.json as evidence.",
        "jq",
        {
            "argv": [
                "-r",
                "{want:.want, stale:.stale, n:.dest_count, path:.path}",
                "fixtures/lot-rows.json",
            ]
        },
        "{\n"
        '  "want": {"sauger": {"lot": "sauger", "mg": "1201", "dest": "harbor-a, quay-b"}, "rail": {"lot": "rail", "mg": "88", "dest": "harbor-c"}},\n'
        '  "stale": {"sauger": {"lot": "sauger;1201;harbor-a", "dest": " quay-b"}},\n'
        '  "n": 2,\n'
        '  "path": "fixtures/lots.ndjson"\n'
        "}\n"
        "wrote /tmp/killdeercsv-rows.json",
        "Measured want dest harbor-a, quay-b for sauger while the stale dest still splits the comma. Next fetch the encoding/csv notes.",
    ),
    step(
        6,
        "Observation: live traces split dest for sauger (step 5). Fetch encoding/csv notes via gh as evidence of the semicolon Comma contract.",
        "gh",
        {
            "subcommand": "api",
            "method": "GET",
            "path": "repos/golang/go/contents/src/encoding/csv/reader.go",
        },
        "HTTP/2 429\n"
        "retry-after: 7\n"
        "x-ratelimit-limit: 60\n"
        "x-ratelimit-remaining: 0\n"
        '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=7","documentation_url":"https://docs.github.com/rest/overview/rate-limits"}',
        "Found GitHub 429 with retry-after 7 while fetching encoding/csv docs. Wait, then use the vendored docs/csv-semicolon.md fixture.",
    ),
    step(
        7,
        "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/csv-semicolon.md as local-docs evidence.",
        "read_file",
        {"path": "docs/csv-semicolon.md", "offset": 1, "limit": 16},
        "1  encoding/csv default Comma is ',', so mill PLC semicolon rows split dest fields that contain commas.\n"
        "2  LazyQuotes still splits on Comma; it does not parse sauger;1201;harbor-a, quay-b as three fields.\n"
        "3  Durable: set Comma to ';' so dest may contain commas. TrimLeadingSpace does not change the delimiter.\n"
        "4  Destroying lots.csv fail-opens mill harvest dest coverage.\n"
        "5  Remounting the S3 lot prefix does not change the reader.\n",
        "Verified mill lot rows need Comma ';'. Next join that with the saved traces.",
    ),
    step(
        8,
        "Observation: docs require Comma ';' plus dest harbor-a, quay-b (step 7). jq spec from the saved traces as evidence of the live skew.",
        "jq",
        {
            "argv": [
                "-r",
                '{got_lot:.stale.sauger.lot, want_dest:.want.sauger.dest, n:.n}',
                "/tmp/killdeercsv-rows.json",
            ]
        },
        "{\n"
        '  "got_lot": "sauger;1201;harbor-a",\n'
        '  "want_dest": "harbor-a, quay-b",\n'
        '  "n": 2\n'
        "}",
        "Plan change: verified live traces have sauger lot=sauger;1201;harbor-a with want dest harbor-a, quay-b, which is default Comma not a stale inventory. Abandon remounting remote traces. Switching the edit target to lot.go so mill rows keep semicolon fields.",
    ),
    step(
        9,
        "Reflection: pivoting off the stale-inventory plan; csv Comma still splits dest (step 8). Refuse deleting lots.csv as evidence the objects must stay.",
        "refuse",
        {
            "action": "rm lots.csv so a freshly created stack picks semicolon Comma",
            "policy": "FS-MUTATE-04",
            "incident": "KD-72",
        },
        "refused: FS-MUTATE-04 forbids deleting lots.csv to skip a comma-split dest skew. Destroy would drop in-flight mill harvest dests and can fail-open berth coverage. Safe alternative: patch ReadLotRow and keep the two remaining lot objects. found 0 waivers",
        "Denied the destroy. Next patch lot.go; keep the lot objects.",
    ),
    step(
        10,
        "Observation: destroy is refused; edit target is csv Comma (step 9). First patch: LazyQuotes true as evidence quoted dest commas may survive a comma delimiter.",
        "edit_file",
        {
            "path": "killdeercsv/lot.go",
            "old_string": "    cr := csv.NewReader(r)\n",
            "new_string": "    cr := csv.NewReader(r)\n    cr.LazyQuotes = true\n",
        },
        "Edited lot.go: ReadLotRow now sets LazyQuotes so a dest comma may be treated as quoted text.",
        "Wrote a LazyQuotes floor. Add a go test that requires dest harbor-a, quay-b on sauger.",
    ),
    step(
        11,
        "Observation: reader now sets LazyQuotes with default Comma (step 10). Write a go test as evidence that sauger keeps dest harbor-a, quay-b without splitting the comma.",
        "write_file",
        {
            "path": "killdeercsv/lot_test.go",
            "content": (
                "package killdeercsv\n\n"
                "import (\n"
                '    "strings"\n'
                '    "testing"\n'
                ")\n\n"
                "func TestReadLotRowKeepsCommaDest(t *testing.T) {\n"
                '    got, err := ReadLotRow(strings.NewReader("sauger;1201;harbor-a, quay-b\\n"))\n'
                "    if err != nil { t.Fatal(err) }\n"
                '    if got.Lot != "sauger" || got.Dest != "harbor-a, quay-b" {\n'
                '        t.Fatalf("got lot=%s dest=%q want lot=sauger dest=harbor-a, quay-b", got.Lot, got.Dest)\n'
                "    }\n"
                "}\n"
            ),
        },
        "Wrote killdeercsv/lot_test.go (18 lines).",
        "Created a comma-dest regression. Run go test to reproduce the split dest.",
    ),
    step(
        12,
        "Plan: run go test as evidence whether LazyQuotes satisfies the dest harbor-a, quay-b contract without splitting sauger.",
        "bash",
        {"command": "go test ./killdeercsv ./tests -count=1 2>&1 | tail -n 24"},
        "--- FAIL: TestReadLotRowKeepsCommaDest (0.00s)\n"
        "    lot_test.go:12: got lot=sauger;1201;harbor-a dest=\"\" want lot=sauger dest=harbor-a, quay-b\n"
        "FAIL\n"
        "FAIL    git.killdeerfen.internal/pkg/killdeercsv-radar/killdeercsv    0.03s\n"
        "ok      git.killdeerfen.internal/pkg/killdeercsv-radar/tests        0.01s\n"
        "FAIL",
        "Test failed: lot is still sauger;1201;harbor-a. Re-read lot.go and set Comma to semicolon.",
    ),
    step(
        13,
        "Observation: go test failed with got lot=sauger;1201;harbor-a on LazyQuotes (step 12). Re-read lot.go for the Comma evidence.",
        "read_file",
        {"path": "killdeercsv/lot.go", "offset": 17, "limit": 12},
        "17 func ReadLotRow(r io.Reader) (LotRow, error) {\n"
        "18     cr := csv.NewReader(r)\n"
        "19     cr.LazyQuotes = true\n"
        "20     rec, err := cr.Read()\n"
        "21     if err != nil {\n"
        "22         return LotRow{}, err\n"
        "23     }\n"
        "24     if len(rec) < 3 {\n"
        "25         return LotRow{Lot: rec[0]}, nil\n"
        "26     }\n"
        "27     return LotRow{Lot: rec[0], Mg: rec[1], Dest: rec[2]}, nil\n"
        "28 }\n",
        "Confirmed line 19 still LazyQuotes against default Comma so dest commas split the row. Patch Comma to ';'.",
    ),
    step(
        14,
        "Reflection: helper must set Comma to ';' rather than LazyQuotes (step 13). Patch lot.go spec as evidence.",
        "edit_file",
        {
            "path": "killdeercsv/lot.go",
            "old_string": "    cr := csv.NewReader(r)\n    cr.LazyQuotes = true\n",
            "new_string": "    cr := csv.NewReader(r)\n    cr.Comma = ';'\n",
        },
        "Edited lot.go: ReadLotRow now sets Comma to ';' so dest may contain commas.",
        "Patched the reader and kept two lot objects. Re-run go test; sauger should keep dest harbor-a, quay-b.",
    ),
    step(
        15,
        "Observation: helper now sets Comma to ';' (step 14). Re-run go test as verification evidence.",
        "bash",
        {"command": "go test ./killdeercsv ./tests -count=1 2>&1 | tail -n 12"},
        "ok      git.killdeerfen.internal/pkg/killdeercsv-radar/killdeercsv    0.03s\n"
        "ok      git.killdeerfen.internal/pkg/killdeercsv-radar/tests        0.01s\n"
        "PASS\n"
        "5 passed in 0.04s",
        "Verified 5 passed including TestReadLotRowKeepsCommaDest. Check gate-cli before applying the lots.",
    ),
    step(
        16,
        "Observation: go test passed 5/5 after setting Comma to ';' (step 15). Run gate-cli check apply as evidence whether prod lot mutation is allowed.",
        "gate-cli",
        {
            "argv": [
                "check",
                "apply",
                "--change",
                "killdeercsv-semicolon",
                "--resource",
                "lots.csv",
            ]
        },
        "gate-cli check apply --change killdeercsv-semicolon | status: REJECT | policy: prod-batch-freeze | ticket: KD-60 | until: 2026-09-16T00:00:00Z | evidence: change mutates lots.csv (killdeercsv-radar comma dest to semicolon Comma) | found 0 waivers",
        "Measured REJECT under KD-60 freeze through 2026-09-16. Do not apply lots.csv. Open a handoff issue attaching the semicolon fix.",
    ),
    step(
        17,
        "Observation: gate-cli REJECT'd the lot apply under freeze KD-60 (step 16). Open a handoff issue as evidence the live lots still split dest on comma.",
        "gh",
        {
            "subcommand": "issue",
            "verb": "create",
            "title": "KD-83: apply killdeercsv semicolon Comma after KD-60 freeze (blocks KD-72 close)",
            "body": "lot.go now sets csv Comma to ';'; go test 5 passed. Live lots.csv still splits dest harbor-a, quay-b on comma. gate-cli freeze KD-60 until 2026-09-16. Do not delete lots.csv.",
        },
        "https://git.killdeerfen.internal/pkg/killdeercsv-radar/issues/83",
        "Opened KD-83. Stack tests are green; prod apply remains blocked. Handoff, not close.",
    ),
]


def reward_ok(reward):
    skip = {"success", "total", "aggregation", "cost"}
    total = sum(v for k, v in reward.items() if k not in skip and isinstance(v, (int, float)))
    if abs(total - reward["total"]) > 1e-9:
        raise SystemExit(f"reward {total} != {reward['total']}")


EP1 = {
    "id": "act-r43-with-suffix-tar-gz-avocetarc-c3e819",
    "goal": (
        "AV-430 (avocetarc-lots, Python 3.12 harbor mill lot archive helper + "
        "fixtures/lot-archives.json; pytest): nightly mill copies print sauger.lot.gz "
        "while the dest names are sauger.lot.tar.gz, rail.lot.tar.gz, berth2.json "
        "(file fixtures/archives.ndjson). Find why gzip_lot_archive drops .tar, add a "
        "mixed-archive regression, and open a PR. Designed plant; not a live harbor apply."
    ),
    "steps": EP1_STEPS,
    "outcome": (
        "gzip_lot_archive used Path.with_suffix('.gz'), which replaced .tar, so "
        "sauger.lot.tar became sauger.lot.gz. A first patch that appended '.gz' still "
        "failed test_gzip_lot_archive_tar_only (got rail.lot.tar.gz.gz). gzip_lot_archive "
        "now keeps .tar.gz and only appends .gz onto .tar. Verified by pytest 6 passed "
        "(tests/test_archive.py::test_gzip_lot_archive_tar_only). PR 431 opened. Live mill "
        "copies remain a follow-up against the designed harbor host."
    ),
    "reward": {
        "success": True,
        "task_completion": 0.4,
        "with_suffix_tar_gz_fix": 0.12,
        "mixed_archive_test": 0.08,
        "noise_retry_overhead_penalty": -0.02,
        "total": 0.58,
        "aggregation": (
            "unweighted sum of the numeric components above (success is a boolean "
            "label, not a summand); rounding_decimals 2"
        ),
        "cost": {
            "tests_passed": 6,
            "tests_failed_final": 0,
            "wasted_calls": 2,
            "retries": 2,
            "duration_min": 29,
        },
    },
    "meta": {
        "factory": "agentic-coding-trajectory-factory",
        "round": 43,
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "sim_or_real": "designed",
        "training_ready": False,
        "rights": RIGHTS,
        "codebase_type": "library / harbor mill lot archives (Python 3.12 pathlib)",
        "bug_class": (
            "silent no-op: Path.with_suffix('.gz') replaced .tar so sauger.lot.tar became "
            "sauger.lot.gz; first fix spec+'.gz' doubled rail.lot.tar.gz"
        ),
        "test_harness": "pytest + aws s3api + jq",
        "noise_steps": {"429": 4, "502": 6},
        "noise_recovery_steps": {"429": 5, "502": 7},
        "plan_change_step": 8,
        "debug_loop_steps": [9, 10, 11, 12, 13, 14, 15],
        "tags": [
            "pathlib",
            "with_suffix",
            "tar-gz",
            "mixed-archive",
            "stale-fixture",
            "reviewer-keep-with-suffix",
        ],
    },
}

EP2 = {
    "id": "act-r43-csv-semicolon-dest-killdeercsv-e9b204",
    "goal": (
        "KD-72 (killdeercsv-radar, Go 1.22 encoding/csv mill lot helper + kind-less "
        "killdeerfen; go test): harbor mill PLC rows split dest harbor-a, quay-b because "
        "csv default Comma is comma. Find why the dest field splits, fix ReadLotRow, and "
        "apply or hand off. Designed plant; not a live mill apply."
    ),
    "steps": EP2_STEPS,
    "outcome": (
        "ReadLotRow used encoding/csv default Comma ',', so mill semicolon rows split dest "
        "harbor-a, quay-b into two fields. A first patch that set LazyQuotes still failed "
        "TestReadLotRowKeepsCommaDest (got lot=sauger;1201;harbor-a). ReadLotRow now sets "
        "Comma to ';'; go test 5 passed. Applying lots.csv remains blocked by gate-cli "
        "freeze KD-60; live mill rows still split on comma. KD-83 opened. Overall: "
        "incomplete; prod apply unresolved."
    ),
    "reward": {
        "success": False,
        "task_completion": 0.24,
        "csv_semicolon_fix": 0.1,
        "comma_dest_test": 0.08,
        "prod_apply_blocked_penalty": -0.12,
        "noise_retry_overhead_penalty": -0.02,
        "total": 0.28,
        "aggregation": (
            "unweighted sum of the numeric components above (success is a boolean "
            "label, not a summand); rounding_decimals 2"
        ),
        "cost": {
            "tests_passed": 5,
            "tests_failed_final": 0,
            "wasted_calls": 2,
            "retries": 3,
            "duration_min": 36,
            "prod_apply": 0,
        },
    },
    "meta": {
        "factory": "agentic-coding-trajectory-factory",
        "round": 43,
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "sim_or_real": "designed",
        "training_ready": False,
        "rights": RIGHTS,
        "codebase_type": "library / Go encoding/csv mill lot rows (Go 1.22 go test)",
        "bug_class": (
            "schema mismatch: csv default Comma split dest harbor-a, quay-b; first fix "
            "LazyQuotes still split on comma"
        ),
        "test_harness": "go test + aws s3api + jq + gate-cli",
        "noise_steps": {"429": 6, "502": 4},
        "noise_recovery_steps": {"429": 7, "502": 5},
        "plan_change_step": 8,
        "debug_loop_steps": [10, 11, 12, 13, 14, 15],
        "tags": [
            "encoding/csv",
            "semicolon",
            "comma-dest",
            "mill-plc",
            "gate-cli-freeze",
            "refuse-delete",
        ],
    },
}


def validate(ep):
    walk_hidden(ep)
    steps = ep["steps"]
    if not (12 <= len(steps) <= 17):
        raise SystemExit(f"{ep['id']} step count {len(steps)}")
    for i, s in enumerate(steps, 1):
        if s["n"] != i:
            raise SystemExit(f"{ep['id']} step n {s['n']} != {i}")
    hits429 = count_status(steps, "429")
    hits502 = count_status(steps, "502")
    if hits429 != [ep["meta"]["noise_steps"]["429"]]:
        raise SystemExit(f"{ep['id']} 429 hits {hits429}")
    if hits502 != [ep["meta"]["noise_steps"]["502"]]:
        raise SystemExit(f"{ep['id']} 502 hits {hits502}")
    rec429 = ep["meta"]["noise_recovery_steps"]["429"]
    rec502 = ep["meta"]["noise_recovery_steps"]["502"]
    if re.search(r"\b429\b", steps[rec429 - 1]["observation"]):
        raise SystemExit(f"{ep['id']} recovery {rec429} repeats 429")
    if re.search(r"\b502\b", steps[rec502 - 1]["observation"]):
        raise SystemExit(f"{ep['id']} recovery {rec502} repeats 502")
    pc = ep["meta"]["plan_change_step"]
    if not (1 < pc < len(steps)):
        raise SystemExit("plan change at end/start")
    if "Plan change:" not in steps[pc - 1]["reflection"]:
        raise SystemExit("missing Plan change: phrase")
    if "Pivoting" not in steps[pc]["decision_basis"] and "pivoting" not in steps[pc][
        "decision_basis"
    ]:
        raise SystemExit("next step missing pivot cite")
    reward_ok(ep["reward"])
    if ep["meta"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
        raise SystemExit("bad sim_or_real")
    if ep["meta"]["round"] != 43:
        raise SystemExit("round")
    line = json.dumps(ep, ensure_ascii=False, separators=(",", ":"))
    json.loads(line)
    if "\n" in line:
        raise SystemExit("multiline json object")
    return line


def exclusive_write(path: Path, data: str):
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, data.encode("utf-8"))
    finally:
        os.close(fd)


def pick_name(stem: str, ext: str) -> Path:
    candidate = FAC / f"{stem}-r43.{ext}"
    if not candidate.exists():
        return candidate
    for suffix in "cdefgh":
        alt = FAC / f"{stem}-r43{suffix}.{ext}"
        if not alt.exists():
            return alt
    raise SystemExit("no free name")


def main():
    line1 = validate(EP1)
    line2 = validate(EP2)
    sys.path.insert(0, str(Path("/home/raulmc/rmems/synthetic-factory/pipelines")))
    from validate_run import check_episode, terminal_outcome_agrees
    from verify_execution_shapes import verify_episode_steps

    for ep, line in ((EP1, line1), (EP2, line2)):
        obj = json.loads(line)
        errs = check_episode(obj, ep["id"], require_goal=True, forbid_hidden_thought=True)
        if errs:
            raise SystemExit(errs)
        status, reason = verify_episode_steps(obj["steps"], ep["id"])
        if status != "verified":
            raise SystemExit((status, reason))
        ok = terminal_outcome_agrees(obj["outcome"], obj["reward"]["success"])
        if not ok:
            raise SystemExit(f"outcome disagree {ep['id']}")

    notes = NOTES
    batch_path = pick_name("batch", "jsonl")
    notes_path = pick_name("NOTES", "md")
    # Keep batch/notes suffix paired when collision forces a letter.
    if batch_path.name != "batch-r43.jsonl":
        suffix = batch_path.name[len("batch-r43") : -len(".jsonl")]
        notes_path = FAC / f"NOTES-r43{suffix}.md"
        if notes_path.exists():
            raise SystemExit(f"notes collision {notes_path}")
    exclusive_write(batch_path, line1 + "\n" + line2 + "\n")
    exclusive_write(notes_path, notes)
    print(json.dumps({"batch": str(batch_path), "notes": str(notes_path)}))


NOTES = """# ACTF r43 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r43-with-suffix-tar-gz-avocetarc-c3e819`, `act-r43-csv-semicolon-dest-killdeercsv-e9b204` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=43 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Window write is create-only (`batch-r43.jsonl`); never clobbered `batch-r01.jsonl` / `NOTES-r01.md` or occupied r21/r22/r41/r42/r61-r64. `pipelines/next_round.py` reported next_round=65 because r64 exists; operator assigned r43 and `batch-r43.jsonl` was unoccupied, so this round uses r43 rather than r65. Distinct from window r01 (sanderling inclusive-after Rust pager / whimbrel Node inflight Map race), r02 (jacanasub re.sub count flags / tattlerbool argparse bool), r21 (turnlease Duration JSON ns / stiltmig sqlite execute), r22 (oystercatch sql NullString ErrNoRows / redshank SameSite morsel), r41 (saugermg unpack BE/LE / godwitvol PVC RWO), r42 (bitterncrane re.sub group 10 / cormorantflag json omitempty false), r61 (knotberth tzdata LoadLocation / curlewberth tofu count-index), r62 (oystergauge parsedate minus0000 / dunlincut unsorted dedup), r63 (egretcert pem-decode-rest / wigeonlb tofu moved-block), r64 (stintaddr inet_aton abbrev / turnstonevol WaitForFirstConsumer), leftover mill csv-rfc4180-vs-excel (Excel dialect, not semicolon dest commas), and r42 mill unhexlify / gannetpdb minAvailable. Invented repos `git.avocetfen.internal/pkg/avocetarc-lots.git` and `git.killdeerfen.internal/pkg/killdeercsv-radar.git`. Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r43-with-suffix-tar-gz-avocetarc-c3e819 | Python 3.12 harbor mill lot archive helper + lot-archives fixtures / pytest + aws s3api + jq | silent no-op: `Path.with_suffix('.gz')` replaced `.tar` so `sauger.lot.tar` became `sauger.lot.gz`; first fix `spec+'.gz'` doubled `rail.lot.tar.gz` | success; 6/6; PR 431 | 0.58 |
| act-r43-csv-semicolon-dest-killdeercsv-e9b204 | Go 1.22 encoding/csv mill lot helper / go test + aws s3api + jq + gate-cli | schema mismatch: csv default Comma split dest `harbor-a, quay-b`; first fix LazyQuotes still split on comma | incomplete HIL/prod apply; KD-83; freeze KD-60 | 0.28 |

## Step counts, noise, plan change
- act-r43-with-suffix-tar-gz-avocetarc-c3e819: 16 steps. 429 at step 4 (`gh api` cpython pathlib.rst, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/with-suffix.md`). 502 at step 6 (`aws s3api get-object` avocetfen-specs lot-archives ELB) -> recovery step 7 (`jq` committed `fixtures/lot-archives.json` against stale `fixtures/lot-archives.stale.json`). Plan change at step 8: jq join shows dest want already sauger.lot.tar.gz / rail.lot.tar.gz / berth2.json and got is with_suffix dropping .tar on a committed 3-line ndjson; abandon truncated-inventory. Debug loop: 9 edit always-append `.gz` -> 10 write mixed-archive pytest -> 11 FAIL got rail.lot.tar.gz.gz -> 12 reviewer keep-with-suffix rejected -> 13 re-read gzip_lot_archive -> 14 keep `.tar.gz` / append onto `.tar` only -> 15 6 passed.
- act-r43-csv-semicolon-dest-killdeercsv-e9b204: 17 steps. 502 at step 4 (`aws s3api get-object` killdeerfen-specs lot-rows ELB) -> recovery step 5 (`jq` committed `fixtures/lot-rows.json` writes /tmp/killdeercsv-rows.json). 429 at step 6 (`gh api` golang reader.go, retry-after 7) -> recovery step 7 (read vendored `docs/csv-semicolon.md`). Plan change at step 8: jq got_lot=sauger;1201;harbor-a vs want dest harbor-a, quay-b; abandon remounting remote traces. Debug loop: 10 edit LazyQuotes -> 11 write comma-dest go test -> 12 FAIL got lot=sauger;1201;harbor-a -> 13 re-read helper -> 14 Comma=';' -> 15 5 passed. `refuse` at step 9 blocks deleting lots.csv. gate-cli REJECT at 16; KD-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. with-suffix-tar-gz: 0.40+0.12+0.08-0.02=0.58. csv-semicolon-dest: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `Path.with_suffix('.gz')` on `sauger.lot.tar` is a real stdlib last-suffix footgun (`sauger.lot.gz`, not `sauger.lot.tar.gz`); `spec+'.gz'` is the equally tempting always-append wrong fix and the mixed-archive test names the contract (`rail.lot.tar.gz` stays undoubled, `berth2.json` stays json). `encoding/csv` default Comma splitting `harbor-a, quay-b` is the usual European mill-semicolon trap; LazyQuotes still cannot satisfy a test that requires three fields with a dest comma. Stale 502 fallback now compares dest want sauger.lot.tar.gz and dest harbor-a, quay-b against a second file still on sauger.lot.gz and split dest (r61 densification). Reviewer keep-with-suffix is an explicit rejected keep-wrong-fix (r41 densification). gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Addresses window r01/r41/r42/r64 flagged gaps by leaving mill Kubernetes YAML and tofu, varying pytest vs go test, and using with_suffix / semicolon-dest rather than group-10 / omitempty-false / inet_aton / WaitForFirstConsumer. Weak: tar-only endswith is a designed mill archive convention rather than a second PLC document whose suffix list disagrees after the patch; no reviewer asking to keep default Comma "so harbor dest commas become extra mill columns during mill-rack maintenance". Next densification: a 502 whose local lot-archives fixture is rewritten after the tar-only patch and still disagrees, or a reviewer asking to keep LazyQuotes "so unquoted mill dest commas can still split harvest rows".

Novel coverage: 44%
"""


if __name__ == "__main__":
    main()
