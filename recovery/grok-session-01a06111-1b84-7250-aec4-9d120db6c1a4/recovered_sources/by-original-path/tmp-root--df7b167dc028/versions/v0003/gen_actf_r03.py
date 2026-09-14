#!/usr/bin/env python3
"""CREATE-ONLY ACTF r03 into the 2026-09-02-final-heavy live tree."""
from __future__ import annotations

import json
import os
import re
import sys

DEST = "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/agentic-coding-trajectory-factory"
KNOWN_TOOLS = frozenset({
    "bash", "read_file", "edit_file", "write_file", "search",
    "gh", "kubectl", "gate-cli", "tofu", "tenv", "tflint", "aws", "jq", "hcl2json",
    "block", "decline", "deny", "refuse",
})
BANNED_KEYS = {
    "thought", "chain_of_thought", "scratch", "reasoning", "inner_monologue",
    "internal_reasoning", "internal_reasoning_verbatim",
}
PROGRESS_RE = re.compile(
    r"\b(found|measured|reproduced|failed|edited|tested|verified|patched)\b",
    re.I,
)

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T21:40:00Z",
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


def db(s: str) -> str:
    if not s.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"bad prefix: {s[:40]!r}")
    if not (80 <= len(s) <= 240):
        raise SystemExit(f"db len {len(s)}: {s}")
    return s


def step(n, basis, tool, args, obs, refl, plan=None):
    d = {
        "n": n,
        "decision_basis": db(basis),
        "tool_call": {"name": tool, "args": args},
        "observation": obs,
        "reflection": refl,
    }
    if plan is not None:
        d["plan"] = plan
        # plan first for envelope clone of r01/r02
        d = {
            "n": n,
            "decision_basis": d["decision_basis"],
            "plan": plan,
            "tool_call": d["tool_call"],
            "observation": obs,
            "reflection": refl,
        }
    return d


def banned(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in BANNED_KEYS or k.startswith("internal_reasoning"):
                raise SystemExit(f"banned key {k} at {path}")
            banned(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            banned(v, f"{path}[{i}]")


def validate_episode(rec):
    banned(rec)
    steps = rec["steps"]
    if not (12 <= len(steps) <= 17):
        raise SystemExit(f"{rec['id']} step count {len(steps)}")
    ns = [s["n"] for s in steps]
    if ns != list(range(1, len(steps) + 1)):
        raise SystemExit(f"{rec['id']} n gap {ns}")
    tools = [s["tool_call"]["name"] for s in steps]
    for t in tools:
        if t not in KNOWN_TOOLS:
            raise SystemExit(f"{rec['id']} unknown tool {t}")
    obs = [s["observation"] for s in steps]
    n429 = sum("429" in o for o in obs)
    n502 = sum("502" in o for o in obs)
    if n429 != 1 or n502 != 1:
        raise SystemExit(f"{rec['id']} noise 429={n429} 502={n502}")
    # recoveries must not re-emit codes
    noise_idx = []
    for i, o in enumerate(obs):
        if "429" in o or "502" in o:
            noise_idx.append(i)
            recov = obs[i + 1]
            if "429" in recov or "502" in recov:
                raise SystemExit(f"{rec['id']} recovery step {i+2} repeats noise")
    pivots = [s for s in steps if "Plan change:" in s.get("reflection", "") or "Pivoting:" in s.get("reflection", "")]
    if len(pivots) != 1:
        raise SystemExit(f"{rec['id']} plan changes {len(pivots)}")
    if pivots[0]["n"] in (1, len(steps)):
        raise SystemExit(f"{rec['id']} plan change at terminal step")
    for s in steps:
        blob = s["reflection"] + " " + s["observation"]
        if not PROGRESS_RE.search(blob):
            raise SystemExit(f"{rec['id']} step {s['n']} missing progress term")
        if "hypothesis" in s["observation"].lower():
            raise SystemExit(f"{rec['id']} step {s['n']} hypothesis in observation")
    if rec["meta"]["round"] != 3:
        raise SystemExit("round")
    if rec["meta"]["factory"] != "agentic-coding-trajectory-factory":
        raise SystemExit("factory")
    if rec["meta"]["sim_or_real"] != "designed":
        raise SystemExit("sim_or_real")
    if not rec["id"].startswith("act-r03-"):
        raise SystemExit(f"id prefix {rec['id']}")


def exclusive_write(path, data: bytes):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


GO_TEST = '''package willeturl

import "testing"

func TestNormalizeCallbackSchemeSlash(t *testing.T) {
	got := NormalizeCallback("https://harbor.internal/berth")
	if got != "https://harbor.internal/berth" {
		t.Fatalf("https got %q", got)
	}
	got = NormalizeCallback("http://partner.internal/grant")
	if got != "http://partner.internal/grant" {
		t.Fatalf("http got %q", got)
	}
	got = NormalizeCallback("https://harbor.internal/berth/../gate")
	if got != "https://harbor.internal/gate" {
		t.Fatalf("dotdot got %q", got)
	}
}
'''

JEST_TEST = """const { contentLength } = require('../scauphmac/length');

test('utf8 content-length for Berth Å and north', () => {
  expect(contentLength('Berth Å')).toBe(8);
  expect(contentLength('north')).toBe(5);
});
"""

ep_a_steps = [
    step(
        1,
        "Plan: WL-320 reports partner callbacks collapse https:// to https:/. Search NormalizeCallback and path.Clean as evidence of a scheme-slash fold.",
        "search",
        {"pattern": "NormalizeCallback|path.Clean|https://|scheme", "path": "."},
        "willeturl/callback.go:8:func NormalizeCallback(u string) string {\nwilleturl/callback.go:9:    return path.Clean(u)\ntests/smoke_test.go:7:    if NormalizeCallback(u) == \"\" { t.Fatal(u) }\nfixtures/callback-urls.json:4:    \"https://harbor.internal/berth\",\n4 matches",
        "Found NormalizeCallback wrapping path.Clean. Next read the helper.",
        plan="1) search NormalizeCallback 2) read callback.go 3) measure path.Clean 4) confirm want :// 5) keep scheme 6) regression + PR",
    ),
    step(
        2,
        "Observation: callback.go:9 returns path.Clean(u) with no scheme guard (step 1). Read the helper as evidence of any Cut on ://.",
        "read_file",
        {"path": "willeturl/callback.go", "offset": 1, "limit": 20},
        "1  package willeturl\n2\n3  import \"path\"\n4\n5  // Harbor partner callbacks must keep scheme:// while still folding /berth/../gate.\n6  // A truncated S3 object is independent of this client Clean.\n7\n8  func NormalizeCallback(u string) string {\n9      return path.Clean(u)\n10 }\n",
        "Measured NormalizeCallback as a path.Clean passthrough. First plan: S3 truncated the https row. Next run path.Clean on URLs.",
    ),
    step(
        3,
        "Observation: NormalizeCallback is a passthrough of path.Clean (step 2). Measure path.Clean on https and http URLs as evidence of a scheme-slash fold.",
        "bash",
        {"command": "cat > /tmp/willeturl-clean.go <<'EOF'\npackage main\nimport (\"fmt\"; \"path\")\nfunc main() {\n  for _, u := range []string{\"https://harbor.internal/berth\", \"http://partner.internal/grant\", \"https://harbor.internal/berth/../gate\"} {\n    fmt.Printf(\"%s -> %s\\n\", u, path.Clean(u))\n  }\n}\nEOF\ngo run /tmp/willeturl-clean.go"},
        "https://harbor.internal/berth -> https:/harbor.internal/berth\nhttp://partner.internal/grant -> http:/partner.internal/grant\nhttps://harbor.internal/berth/../gate -> https:/harbor.internal/gate",
        "Measured path.Clean folding :// to :/. Next confirm dest want still lists https:// and http://.",
    ),
    step(
        4,
        "Reflection: path.Clean printed https:/ and http:/ (step 3). Fetch path.Clean notes via gh as evidence of the scheme-slash contract.",
        "gh",
        {"subcommand": "api", "method": "GET", "path": "repos/golang/go/contents/src/path/path.go"},
        "HTTP/2 429\nretry-after: 5\nx-ratelimit-limit: 60\nx-ratelimit-remaining: 0\n{\"message\":\"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=5\",\"documentation_url\":\"https://docs.github.com/rest/overview/rate-limits\"}",
        "GitHub failed with a rate-limit retry-after 5 while fetching path.Clean docs. Wait, then use the vendored docs/path-clean-scheme.md fixture.",
    ),
    step(
        5,
        "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/path-clean-scheme.md as local-docs evidence.",
        "read_file",
        {"path": "docs/path-clean-scheme.md", "offset": 1, "limit": 16},
        "1  path.Clean treats the URL as a slash path, so https://host becomes https:/host.\n2  strings.Replace(path.Clean(u), \"https:/\", \"https://\", 1) repairs https but leaves http:/.\n3  Durable: split on ://, Clean only the path, rejoin scheme://host+cleaned.\n4  /berth/../gate must still fold to /gate after the scheme is restored.\n5  Dropping the http row loses the partner grant callback.\n6  A truncated S3 object is independent of this client Clean.\n",
        "Verified the :// fold and that an https-only Replace still emits http:/. Next pull the committed callback-urls fixture.",
    ),
    step(
        6,
        "Observation: RFC-style notes say callbacks must keep scheme:// (step 5). Get the committed callback-urls object as evidence the want set keeps https://.",
        "aws",
        {"argv": ["s3api", "get-object", "--bucket", "willetfen-specs", "--key", "willeturl/callback-urls.json", "/tmp/willeturl-inventory.json"]},
        "download failed: s3.eu-north-1.amazonaws.com/willetfen-specs\nHTTP/1.1 502 Bad Gateway\nserver: awselb/2.0\nupstream connect error or disconnect/reset before headers. reset reason: connection failure",
        "Callback inventory get-object failed on the ELB before headers. Retry against the committed fixtures/callback-urls.json instead of the edge.",
    ),
    step(
        7,
        "Observation: callback urls get-object returned 502 from the ELB (step 6). jq fixtures/callback-urls.json want as local-spec evidence.",
        "jq",
        {"argv": ["-r", "{want:.want, n:.dest_count, path:.path, stale:.stale}", "fixtures/callback-urls.json"]},
        "{\n  \"want\": {\n    \"https\": \"https://harbor.internal/berth\",\n    \"http\": \"http://partner.internal/grant\",\n    \"dotdot\": \"https://harbor.internal/gate\"\n  },\n  \"n\": 3,\n  \"path\": \"fixtures/callbacks.ndjson\",\n  \"stale\": \"fixtures/callback-urls.stale.json\"\n}",
        "Verified want already lists https://, http://, and the folded /gate. Next join that with the stale fixture and the measured https:/ stamp.",
    ),
    step(
        8,
        "Observation: fixture want already lists https:// and http:// (step 7). jq the measured https:/ stamp against that spec and the stale file as evidence whether S3 truncated callbacks.",
        "jq",
        {"argv": ["-n", "--slurpfile", "s", "fixtures/callback-urls.json", "--slurpfile", "k", "fixtures/callback-urls.stale.json", "{got:\"path.Clean https:/ and http:/\",want:$s[0].want,stale:$k[0].want,n:$s[0].dest_count,path:$s[0].path}"]},
        "{\n  \"got\": \"path.Clean https:/ and http:/\",\n  \"want\": {\n    \"https\": \"https://harbor.internal/berth\",\n    \"http\": \"http://partner.internal/grant\",\n    \"dotdot\": \"https://harbor.internal/gate\"\n  },\n  \"stale\": {\n    \"https\": \"https:/harbor.internal/berth\",\n    \"http\": \"http:/partner.internal/grant\",\n    \"dotdot\": \"https:/harbor.internal/gate\"\n  },\n  \"n\": 3,\n  \"path\": \"fixtures/callbacks.ndjson\"\n}",
        "Plan change: callback want stamps already list scheme:// and got is path.Clean https:/ on a committed 3-line ndjson. Abandon truncated-object. Switching the edit target to NormalizeCallback so Clean runs only on the path.",
    ),
    step(
        9,
        "Reflection: pivoting off the truncated-object plan; NormalizeCallback still emits https:/ (step 8). Edit https:/ Replace as evidence only https is repaired.",
        "edit_file",
        {
            "path": "willeturl/callback.go",
            "old_string": "func NormalizeCallback(u string) string {\n    return path.Clean(u)\n}\n",
            "new_string": "func NormalizeCallback(u string) string {\n    return strings.Replace(path.Clean(u), \"https:/\", \"https://\", 1)\n}\n",
        },
        "Edited willeturl/callback.go: NormalizeCallback now Replace https:/ so http:/ stays collapsed.",
        "Edited an https-only Replace. Add a go test that requires https:// and http:// plus /berth/../gate.",
    ),
    step(
        10,
        "Observation: NormalizeCallback now Replace-repairs only https:/ (step 9). Write a go test as evidence dest callbacks keep scheme://.",
        "write_file",
        {"path": "tests/callback_test.go", "content": GO_TEST},
        "Wrote tests/callback_test.go (18 lines).",
        "Tested via a mixed-scheme regression that expects http:// to stay ://. Run go test to reproduce the http:/ stamp.",
    ),
    step(
        11,
        "Plan: run go test tests as evidence whether https:/ Replace keeps dest callbacks on scheme:// including http.",
        "bash",
        {"command": "go test ./... -count=1 2>&1 | tail -n 24"},
        "=== RUN   TestInstall\n--- PASS: TestInstall (0.00s)\n=== RUN   TestNormalizeCallbackSchemeSlash\n    callback_test.go:12: http got \"http:/partner.internal/grant\"\n--- FAIL: TestNormalizeCallbackSchemeSlash (0.00s)\nFAIL\nFAIL\twilleturl\t0.01s\nFAIL",
        "Test failed: https Replace still emits http:/. Re-read NormalizeCallback and reject a keep-Replace review.",
    ),
    step(
        12,
        "Observation: go test failed with got http:/ on https Replace (step 11). Read the keep-Replace review as evidence whether dest may stay collapsed for http.",
        "read_file",
        {"path": "docs/review-keep-replace.md", "offset": 1, "limit": 12},
        "1  Reviewer (WL-320 comment 4): keep strings.Replace https:/ so operators can grep collapsed https URLs from runbooks.\n2  Claim: http partners are legacy and HMAC still matches on https:/harbor.\n3  Dest contract named in fixtures/callback-urls.json is https://, http://, and /gate.\n4  Reject keep-Replace: partner grant callbacks already use http:// and HMAC is over the :// form.\n",
        "Rejected the keep-Replace review; dest want is scheme:// not http:/. Re-read NormalizeCallback and split on ://.",
    ),
    step(
        13,
        "Observation: keep-Replace review was rejected; dest want stays scheme:// (step 12). Re-read NormalizeCallback for the Replace evidence.",
        "read_file",
        {"path": "willeturl/callback.go", "offset": 1, "limit": 14},
        "1  package willeturl\n2\n3  import \"path\"\n4\n5  // Harbor partner callbacks must keep scheme:// while still folding /berth/../gate.\n6  // A truncated S3 object is independent of this client Clean.\n7\n8  func NormalizeCallback(u string) string {\n9      return strings.Replace(path.Clean(u), \"https:/\", \"https://\", 1)\n10 }\n",
        "Confirmed line 9 still Replace-repairs only https:/. Patch Cut on :// and Clean the path.",
    ),
    step(
        14,
        "Reflection: NormalizeCallback must split on :// and Clean only the path (step 13). Patch callback.go as evidence.",
        "edit_file",
        {
            "path": "willeturl/callback.go",
            "old_string": "package willeturl\n\nimport \"path\"\n\n// Harbor partner callbacks must keep scheme:// while still folding /berth/../gate.\n// A truncated S3 object is independent of this client Clean.\n\nfunc NormalizeCallback(u string) string {\n    return strings.Replace(path.Clean(u), \"https:/\", \"https://\", 1)\n}\n",
            "new_string": "package willeturl\n\nimport (\n    \"path\"\n    \"strings\"\n)\n\n// Harbor partner callbacks must keep scheme:// while still folding /berth/../gate.\n// A truncated S3 object is independent of this client Clean.\n\nfunc NormalizeCallback(u string) string {\n    scheme, rest, ok := strings.Cut(u, \"://\")\n    if !ok {\n        return path.Clean(u)\n    }\n    host, pth, ok := strings.Cut(rest, \"/\")\n    if !ok {\n        return scheme + \"://\" + rest\n    }\n    cleaned := path.Clean(\"/\" + pth)\n    if cleaned == \"/\" {\n        return scheme + \"://\" + host\n    }\n    return scheme + \"://\" + host + cleaned\n}\n",
        },
        "Edited willeturl/callback.go: NormalizeCallback now Cuts on ://, Cleans only the path, and rejoins scheme://host.",
        "Patched the scheme-preserving Clean. Re-run go test; http:// should stay :// and /berth/../gate should fold.",
    ),
    step(
        15,
        "Observation: NormalizeCallback now Cuts on :// and Cleans only the path (step 14). Re-run go test as verification evidence.",
        "bash",
        {"command": "go test ./... -count=1 2>&1 | tail -n 16"},
        "=== RUN   TestInstall\n--- PASS: TestInstall (0.00s)\n=== RUN   TestNormalizeCallbackSchemeSlash\n--- PASS: TestNormalizeCallbackSchemeSlash (0.00s)\n=== RUN   TestNormalizeEmpty\n--- PASS: TestNormalizeEmpty (0.00s)\n=== RUN   TestNormalizeRelative\n--- PASS: TestNormalizeRelative (0.00s)\n=== RUN   TestNormalizeHostOnly\n--- PASS: TestNormalizeHostOnly (0.00s)\n=== RUN   TestNormalizeDotDotGate\n--- PASS: TestNormalizeDotDotGate (0.00s)\nPASS\nok  \twilleturl\t0.02s",
        "Verified 6 passed including TestNormalizeCallbackSchemeSlash. Open the WL-320 PR.",
    ),
    step(
        16,
        "Observation: go test passed 6/6 after the :// Cut patch (step 15). Create the WL-320 PR via gh as evidence of the NormalizeCallback fix.",
        "gh",
        {"subcommand": "api", "method": "POST", "path": "repos/willetfen/willeturl-harbor/pulls", "raw_field": "title=WL-320: keep scheme:// when path.Clean folds partner callbacks instead of emitting https:/"},
        "{\n  \"number\": 301,\n  \"html_url\": \"https://git.willetfen.internal/pkg/willeturl-harbor/pull/301\",\n  \"state\": \"open\"\n}",
        "Verified PR 301 opened. NormalizeCallback keeps scheme:// for https and http. Live callback copies remain a follow-up against the designed harbor host.",
    ),
]

ep_b_steps = [
    step(
        1,
        "Plan: SC-72 reports HMAC bodies signed with Content-Length 7 for Berth Å. Search contentLength and .length as evidence of UTF-16 code units.",
        "search",
        {"pattern": "contentLength|byteLength|\\.length|utf8|Berth", "path": "."},
        "scauphmac/length.js:4:function contentLength(s) {\nscauphmac/length.js:5:  return s.length;\nscauphmac/sign.js:9:  headers['content-length'] = String(contentLength(body));\ntests/smoke.test.js:6:  expect(contentLength('north')).toBe(5);\n5 matches",
        "Found contentLength returning s.length. Next read the helper.",
        plan="1) search contentLength 2) read length.js 3) measure .length vs byteLength 4) confirm want 8 5) Buffer.byteLength utf8 6) apply or hand off",
    ),
    step(
        2,
        "Observation: length.js:5 returns s.length with no byteLength (step 1). Read the helper as evidence of any utf8 byte count.",
        "read_file",
        {"path": "scauphmac/length.js", "offset": 1, "limit": 16},
        "1  // Harbor HMAC bodies must advertise UTF-8 Content-Length (Berth Å is 8 bytes).\n2  // Deleting hmac-cache.json fail-opens partner signatures.\n3\n4  function contentLength(s) {\n5    return s.length;\n6  }\n7\n8  function loadBody(path) {\n9    return require('fs').readFileSync(path, 'utf8');\n10 }\n11\n12 module.exports = { contentLength, loadBody };\n",
        "Learned contentLength uses JS string length. First plan: S3 traces omitted the Å body so length looks like north=5. Next measure .length vs byteLength.",
    ),
    step(
        3,
        "Observation: contentLength returns s.length (step 2). Measure .length versus Buffer.byteLength as evidence of a 7-byte Content-Length on Berth Å.",
        "bash",
        {"command": "node -e \"const s='Berth Å'; console.log('length', s.length); console.log('utf8', Buffer.byteLength(s)); console.log('utf16le', Buffer.byteLength(s,'utf16le')); console.log('north', 'north'.length, Buffer.byteLength('north'));\""},
        "length 7\nutf8 8\nutf16le 14\nnorth 5 5",
        "Measured .length=7, utf8=8, utf16le=14 for Berth Å. Next confirm dest want Content-Length is 8.",
    ),
    step(
        4,
        "Observation: Berth Å .length is 7 while utf8 byteLength is 8 (step 3). Get the committed hmac-traces object as evidence the want length is 8.",
        "aws",
        {"argv": ["s3api", "get-object", "--bucket", "scaupfen-specs", "--key", "scauphmac/hmac-traces.json", "/tmp/scauphmac-inventory.json"]},
        "download failed: s3.eu-north-1.amazonaws.com/scaupfen-specs\nHTTP/1.1 502 Bad Gateway\nserver: awselb/2.0\nupstream connect error or disconnect/reset before headers. reset reason: connection failure",
        "HMAC traces get-object failed on the ELB before headers. Retry against the committed fixtures/hmac-traces.json instead of the edge.",
    ),
    step(
        5,
        "Observation: hmac traces get-object returned 502 from the ELB (step 4). jq fixtures/hmac-traces.json want as local-spec evidence.",
        "jq",
        {"argv": ["-r", "{want:.want, got:.got, n:.dest_count, path:.path, stale:.stale}", "fixtures/hmac-traces.json"]},
        "{\n  \"want\": {\n    \"berth-a\": 8,\n    \"north\": 5,\n    \"gate\": 4\n  },\n  \"got\": 7,\n  \"n\": 3,\n  \"path\": \"fixtures/bodies.ndjson\",\n  \"stale\": \"fixtures/hmac-traces.stale.json\"\n}\nwrote /tmp/scauphmac-traces.json",
        "Verified want already lists 8 for Berth Å. Next fetch Node Buffer.byteLength notes.",
    ),
    step(
        6,
        "Observation: fixture want_length is 8 while got is 7 (step 5). Fetch Buffer.byteLength notes via gh as evidence of utf8 vs utf16le.",
        "gh",
        {"subcommand": "api", "method": "GET", "path": "repos/nodejs/node/contents/doc/api/buffer.md"},
        "HTTP/2 429\nretry-after: 7\nx-ratelimit-limit: 60\nx-ratelimit-remaining: 0\n{\"message\":\"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=7\",\"documentation_url\":\"https://docs.github.com/rest/overview/rate-limits\"}",
        "GitHub failed with a rate-limit retry-after 7 while fetching buffer docs. Wait, then use the vendored docs/byte-length-utf8.md fixture.",
    ),
    step(
        7,
        "Observation: gh api returned 429 with retry-after 7 (step 6). Sleep 8s, then read docs/byte-length-utf8.md as local-docs evidence.",
        "read_file",
        {"path": "docs/byte-length-utf8.md", "offset": 1, "limit": 16},
        "1  String.prototype.length counts UTF-16 code units; Å is 1 so 'Berth Å'.length is 7.\n2  Buffer.byteLength(s, 'utf16le') is 14 and cannot match dest Content-Length 8.\n3  Durable: Buffer.byteLength(s, 'utf8') (8 for Berth Å, 5 for north).\n4  Deleting hmac-cache.json fail-opens partner signatures.\n5  A dummy ASCII-only body still does not prove the Å contract.\n6  Remote-trace lag is independent of this byteLength.\n",
        "Verified Content-Length needs utf8 byteLength, not utf16le. Next join that with the saved traces and the stale fixture.",
    ),
    step(
        8,
        "Observation: docs require utf8 byteLength 8, not .length 7 (step 7). jq the saved traces against the stale file as evidence of the length skew.",
        "jq",
        {"argv": ["-n", "--slurpfile", "s", "fixtures/hmac-traces.json", "--slurpfile", "k", "fixtures/hmac-traces.stale.json", "{got:$s[0].got,want:$s[0].want,stale:$k[0].want,n:$s[0].dest_count,path:$s[0].path}"]},
        "{\n  \"got\": 7,\n  \"want\": {\n    \"berth-a\": 8,\n    \"north\": 5,\n    \"gate\": 4\n  },\n  \"stale\": {\n    \"berth-a\": 7,\n    \"north\": 5,\n    \"gate\": 4\n  },\n  \"n\": 3,\n  \"path\": \"fixtures/bodies.ndjson\"\n}",
        "Plan change: traces already include Berth Å want 8 and got is .length 7 on a committed 3-line ndjson. Abandon remounting remote traces. Switching the edit target to contentLength so UTF-8 byteLength is used.",
    ),
    step(
        9,
        "Reflection: pivoting off the omitted-Å plan; contentLength still returns 7 (step 8). Refuse deleting hmac-cache.json as evidence the objects must stay.",
        "refuse",
        {"action": "rm -f hmac-cache.json so a freshly created cache picks byteLength", "policy": "FS-MUTATE-04", "incident": "SC-72"},
        "refused: FS-MUTATE-04 forbids deleting hmac-cache.json to skip a string.length skew. Delete would drop in-flight partner signatures and can fail-open coverage. Safe alternative: patch contentLength and keep the cache file. found 0 waivers",
        "Denied the delete. Next patch length.js; keep the hmac cache.",
    ),
    step(
        10,
        "Observation: delete is refused; edit target is s.length (step 9). First patch: utf16le byteLength as evidence Å may be counted as 14.",
        "edit_file",
        {
            "path": "scauphmac/length.js",
            "old_string": "  function contentLength(s) {\n    return s.length;\n  }\n",
            "new_string": "  function contentLength(s) {\n    return Buffer.byteLength(s, 'utf16le');\n  }\n",
        },
        "Edited scauphmac/length.js: contentLength now Buffer.byteLength utf16le so Berth Å becomes 14.",
        "Edited a utf16le byteLength. Add a jest that requires Berth Å Content-Length 8.",
    ),
    step(
        11,
        "Observation: contentLength now uses utf16le byteLength (step 10). Write a jest as evidence that Berth Å stays Content-Length 8.",
        "write_file",
        {"path": "tests/length.test.js", "content": JEST_TEST},
        "Wrote tests/length.test.js (7 lines).",
        "Created a mixed-body regression that expects Berth Å to stay 8. Run npm test to reproduce the 14-byte stamp.",
    ),
    step(
        12,
        "Plan: run npm test tests/length.test.js as evidence whether utf16le byteLength satisfies the dest Content-Length 8 contract.",
        "bash",
        {"command": "npm test --silent -- tests/length.test.js tests/smoke.test.js 2>&1 | tail -n 24"},
        "FAIL tests/length.test.js\n  ● utf8 content-length for Berth Å and north\n\n    expect(received).toBe(expected)\n\n    Expected: 8\n    Received: 14\n\n      3 | test('utf8 content-length for Berth Å and north', () => {\n      4 |   expect(contentLength('Berth Å')).toBe(8);\n\nTest Suites: 1 failed, 1 passed, 2 total\nTests:       1 failed, 1 passed, 2 total",
        "Test failed: utf16le still emits 14. Re-read contentLength and switch to utf8 byteLength.",
    ),
    step(
        13,
        "Observation: npm test failed with got 14 on utf16le byteLength (step 12). Re-read length.js for the encoding evidence.",
        "read_file",
        {"path": "scauphmac/length.js", "offset": 1, "limit": 12},
        "1  // Harbor HMAC bodies must advertise UTF-8 Content-Length (Berth Å is 8 bytes).\n2  // Deleting hmac-cache.json fail-opens partner signatures.\n3\n4  function contentLength(s) {\n5    return Buffer.byteLength(s, 'utf16le');\n6  }\n7\n8  function loadBody(path) {\n9    return require('fs').readFileSync(path, 'utf8');\n10 }\n11\n12 module.exports = { contentLength, loadBody };\n",
        "Confirmed line 5 still counts utf16le 14. Patch utf8 byteLength and keep north=5.",
    ),
    step(
        14,
        "Reflection: helper must emit UTF-8 byteLength 8 for Berth Å (step 13). Patch length.js spec as evidence of the dest contract.",
        "edit_file",
        {
            "path": "scauphmac/length.js",
            "old_string": "  function contentLength(s) {\n    return Buffer.byteLength(s, 'utf16le');\n  }\n",
            "new_string": "  function contentLength(s) {\n    return Buffer.byteLength(s, 'utf8');\n  }\n",
        },
        "Edited scauphmac/length.js: contentLength now Buffer.byteLength utf8 so Berth Å is 8 and north stays 5.",
        "Patched utf8 byteLength and kept contentLength. Re-run npm test; Å should stay 8.",
    ),
    step(
        15,
        "Observation: helper now emits UTF-8 byteLength for Berth Å (step 14). Re-run npm test as verification evidence.",
        "bash",
        {"command": "npm test --silent -- tests/length.test.js tests/smoke.test.js 2>&1 | tail -n 12"},
        "PASS tests/length.test.js\nPASS tests/smoke.test.js\nTest Suites: 2 passed, 2 total\nTests:       4 passed, 4 total",
        "Verified 4 passed including utf8 content-length for Berth Å. Check gate-cli before applying hmac-cache.",
    ),
    step(
        16,
        "Observation: npm test passed 4/4 after the utf8 byteLength patch (step 15). Run gate-cli check apply as evidence whether prod hmac mutation is allowed.",
        "gate-cli",
        {"argv": ["check", "apply", "--change", "scauphmac-byte-length-utf8", "--resource", "hmac-cache.json"]},
        "gate-cli check apply --change scauphmac-byte-length-utf8\nstatus: REJECT\npolicy: prod-batch-freeze\nticket: SC-60\nuntil: 2026-09-16T00:00:00Z\nevidence: change mutates hmac-cache.json (scauphmac-harbor string.length to utf8 byteLength)\nfound 0 waivers",
        "Measured REJECT under SC-60 freeze through 2026-09-16. Do not flash hmac-cache. Open a handoff issue attaching the utf8 byteLength fix.",
    ),
    step(
        17,
        "Observation: gate-cli REJECT'd the hmac apply under freeze SC-60 (step 16). Open a handoff issue as evidence live still has string.length.",
        "gh",
        {"subcommand": "issue", "verb": "create", "title": "SC-83: apply scauphmac utf8 byteLength after SC-60 freeze (blocks SC-72 close)", "body": "length.js now emits Buffer.byteLength utf8; npm test 4 passed. Live hmac still has string.length. gate-cli freeze SC-60 until 2026-09-16. Do not delete hmac-cache.json."},
        "https://git.scaupfen.internal/cli/scauphmac-harbor/issues/83",
        "Opened SC-83. CLI tests are green; prod apply remains blocked. Handoff, not close.",
    ),
]

ep_a = {
    "id": "act-r03-path-clean-scheme-willeturl-c8d41a",
    "goal": "WL-320 (willeturl-harbor, Go 1.22 partner callback helper + fixtures/callback-urls.json; go test): nightly dest copies print https:/harbor.internal/berth while partner HMAC is over https://harbor.internal/berth (file fixtures/callbacks.ndjson). Find why NormalizeCallback folds ://, add a mixed-scheme regression, and open a PR. Designed plant; not a live harbor apply.",
    "steps": ep_a_steps,
    "outcome": "NormalizeCallback passed URLs through path.Clean, so https:// collapsed to https:/ and http:// to http:/. A first patch that strings.Replace https:/ still failed TestNormalizeCallbackSchemeSlash (got http:/partner.internal/grant). NormalizeCallback now Cuts on ://, Cleans only the path, and rejoins scheme://host. Verified by go test 6 passed (tests/callback_test.go::TestNormalizeCallbackSchemeSlash). PR 301 opened. Live callback copies remain a follow-up against the designed harbor host.",
    "reward": {
        "success": True,
        "task_completion": 0.4,
        "scheme_slash_fix": 0.12,
        "mixed_scheme_test": 0.08,
        "noise_retry_overhead_penalty": -0.02,
        "total": 0.58,
        "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
        "cost": {
            "tests_passed": 6,
            "tests_failed_final": 0,
            "wasted_calls": 2,
            "retries": 2,
            "duration_min": 28,
        },
    },
    "meta": {
        "factory": "agentic-coding-trajectory-factory",
        "round": 3,
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "sim_or_real": "designed",
        "training_ready": False,
        "rights": RIGHTS,
        "codebase_type": "library / partner callback helper (Go 1.22 path.Clean)",
        "bug_class": "schema mismatch: path.Clean folds https:// to https:/; first fix strings.Replace https:/ leaves http:/",
        "test_harness": "go test + aws s3api + jq",
        "noise_steps": {"429": 4, "502": 6},
        "noise_recovery_steps": {"429": 5, "502": 7},
        "plan_change_step": 8,
        "debug_loop_steps": [9, 10, 11, 12, 13, 14, 15],
        "tags": ["go-1.22", "path.Clean", "scheme-slash", "strings.Cut", "go-test", "callback-url"],
    },
}

ep_b = {
    "id": "act-r03-string-length-utf8-scauphmac-d4e91b",
    "goal": "SC-72 (scauphmac-harbor, Node 20 HMAC CLI + kind-less scaupfen; jest via npm test + gate-cli): partner HMAC bodies for Berth Å were signed with Content-Length 7 because string.length counts UTF-16 code units. Find why the Å body is 7, fix contentLength, and apply or hand off. Designed plant; not a live hmac apply.",
    "steps": ep_b_steps,
    "outcome": "contentLength returned s.length, so Berth Å advertised Content-Length 7 instead of UTF-8 8. A first patch that used Buffer.byteLength(s, 'utf16le') still failed tests/length.test.js (received 14). The CLI now emits Buffer.byteLength(s, 'utf8'); npm test 4 passed. Applying hmac-cache.json remains blocked by gate-cli freeze SC-60; live hmac still has string.length. SC-83 opened. Overall: incomplete; prod apply unresolved.",
    "reward": {
        "success": False,
        "task_completion": 0.24,
        "utf8_byte_length_fix": 0.1,
        "berth_a_length_test": 0.08,
        "prod_apply_blocked_penalty": -0.12,
        "noise_retry_overhead_penalty": -0.02,
        "total": 0.28,
        "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
        "cost": {
            "tests_passed": 4,
            "tests_failed_final": 0,
            "wasted_calls": 2,
            "retries": 3,
            "duration_min": 33,
            "prod_apply": 0,
        },
    },
    "meta": {
        "factory": "agentic-coding-trajectory-factory",
        "round": 3,
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "sim_or_real": "designed",
        "training_ready": False,
        "rights": RIGHTS,
        "codebase_type": "CLI / partner HMAC body length (Node 20 Buffer.byteLength)",
        "bug_class": "schema mismatch: string.length counts UTF-16 units so Berth Å is 7; first fix utf16le byteLength is 14",
        "test_harness": "jest via npm test + aws s3api + jq + gate-cli",
        "noise_steps": {"502": 4, "429": 6},
        "noise_recovery_steps": {"502": 5, "429": 7},
        "plan_change_step": 8,
        "debug_loop_steps": [10, 11, 12, 13, 14, 15],
        "tags": ["node-20", "string-length", "byteLength", "utf8", "hmac", "gate-cli-freeze", "refuse-delete"],
    },
}

NOTES = """# ACTF r03 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r03-path-clean-scheme-willeturl-c8d41a`, `act-r03-string-length-utf8-scauphmac-d4e91b` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`aws`/`jq`/`gate-cli`/`refuse`). meta.round=3 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Live-tree write is create-only (`batch-r03.jsonl`); never clobbered `batch-r01.jsonl` / `NOTES-r01.md` / r02 / r21 / r22 / r41 / r42 / r61-r64 and never wrote 2026-08-17/2026-08-30. Distinct from window r01 (sanderling inclusive-after / whimbrel inflight Map), r02 (jacanasub re.sub count-vs-flags / tattlerbool argparse type=bool), r21 duration-json-ns / executescript, r22 sql-nullstring / samesite-morsel, r41 unpack-be-le / PVC RWO, r42 (bitterncrane re.sub group10 / cormorantflag json omitempty false — this is path.Clean :// fold, not bool omitempty), r61 tzdata / tofu count-index, r62 parsedate -0000 / dunlincut unsorted dedup, r63 pem decode / tofu moved-block, r64 inet_aton / WaitForFirstConsumer, urljoin-drop-segment (last-path join, not scheme slash), os-path-join-absolute, and unicode-nfd-nfc (normalization form, not UTF-16 length). Addresses r02 NOTES gap (stale 502 fixture whose want disagrees with a second document; reviewer keep-wrong-fix) while leaving mill lots and Kubernetes YAML. Invented repos `git.willetfen.internal/pkg/willeturl-harbor.git` and `git.scaupfen.internal/cli/scauphmac-harbor.git`. Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r03-path-clean-scheme-willeturl-c8d41a | Go 1.22 partner callback helper + callback-urls fixtures / go test + aws s3api + jq | schema mismatch: `path.Clean` folds `https://` to `https:/`; first fix `strings.Replace https:/` leaves `http:/` | success; 6/6; PR 301 | 0.58 |
| act-r03-string-length-utf8-scauphmac-d4e91b | Node 20 HMAC CLI / jest via npm test + aws s3api + jq + gate-cli | schema mismatch: `string.length` counts UTF-16 units so Berth Å is 7; first fix utf16le byteLength is 14 | incomplete HIL/prod apply; SC-83; freeze SC-60 | 0.28 |

## Step counts, noise, plan change
- act-r03-path-clean-scheme-willeturl-c8d41a: 16 steps. 429 at step 4 (`gh api` golang/go path.go, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/path-clean-scheme.md`). 502 at step 6 (`aws s3api get-object` willetfen-specs callback-urls ELB) -> recovery step 7 (`jq` committed `fixtures/callback-urls.json` against stale `fixtures/callback-urls.stale.json`). Plan change at step 8: jq join shows want already scheme:// while stale still lists https:/; abandon truncated-object. Debug loop: 9 edit https Replace -> 10 write mixed-scheme go test -> 11 FAIL got http:/ -> 12 reviewer keep-Replace rejected -> 13 re-read callback.go -> 14 Cut :// + path.Clean patch -> 15 6 passed.
- act-r03-string-length-utf8-scauphmac-d4e91b: 17 steps. 502 at step 4 (`aws s3api get-object` scaupfen-specs hmac-traces ELB) -> recovery step 5 (`jq` committed `fixtures/hmac-traces.json` writes /tmp/scauphmac-traces.json). 429 at step 6 (`gh api` nodejs buffer.md, retry-after 7) -> recovery step 7 (`sleep 8` + read `docs/byte-length-utf8.md`). Plan change at step 8: jq join shows want already 8 for Berth Å while stale still lists 7; abandon remounting remote traces. Debug loop: 10 edit utf16le -> 11 write jest -> 12 FAIL received 14 -> 13 re-read length.js -> 14 utf8 byteLength -> 15 4 passed. `refuse` at step 9 blocks deleting hmac-cache.json. gate-cli REJECT at 16; SC-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. path-clean-scheme: 0.40+0.12+0.08-0.02=0.58. string-length-utf8: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `path.Clean` collapsing `https://` to `https:/` is a real Go slash-path footgun; `strings.Replace(..., "https:/", "https://", 1)` is the equally tempting https-only wrong fix and the mixed-scheme test names the contract (`http://partner.internal/grant` plus `/berth/../gate` -> `/gate`). `String.length` on `Berth Å` is the usual UTF-16 Content-Length trap; `Buffer.byteLength(..., 'utf16le')` still cannot satisfy a test that requires UTF-8 8 rather than 14. Stale 502 fallback now compares dest want scheme:// / 8 against a second file still on https:/ / 7 (r02 densification). Reviewer keep-Replace is an explicit rejected keep-wrong-fix (r02 densification). gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Addresses r02 NOTES gap while leaving mill lots and Kubernetes YAML, varying go test vs jest, and using scheme-slash vs UTF-16 length. Weak: go measure shells a /tmp main instead of `go test` on the module; utf16le first fix is a second encoding rather than a reviewer asking to keep `.length` "so ASCII dashboards keep showing 7 for Berth Å". Next densification: a 502 whose local callback-urls fixture is rewritten after the Cut patch and still lists https:/, or a reviewer asking to keep utf16le "so Windows HMAC clients can grep 14-byte lengths from runbooks".

Novel coverage: 51%
"""


def main():
    for rec in (ep_a, ep_b):
        validate_episode(rec)
        print(rec["id"], "steps", len(rec["steps"]),
              "db", [len(s["decision_basis"]) for s in rec["steps"]],
              "success", rec["reward"]["success"])

    batch_name, notes_name = "batch-r03.jsonl", "NOTES-r03.md"
    batch_path = os.path.join(DEST, batch_name)
    notes_path = os.path.join(DEST, notes_name)
    if os.path.exists(batch_path) or os.path.exists(notes_path):
        batch_name, notes_name = "batch-r03c.jsonl", "NOTES-r03c.md"
        batch_path = os.path.join(DEST, batch_name)
        notes_path = os.path.join(DEST, notes_name)
        print("collision; using c-suffix", batch_name)

    body = (
        json.dumps(ep_a, ensure_ascii=False, separators=(",", ":"))
        + "\n"
        + json.dumps(ep_b, ensure_ascii=False, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    notes = NOTES.encode("utf-8")
    try:
        exclusive_write(batch_path, body)
        exclusive_write(notes_path, notes)
    except FileExistsError as e:
        raise SystemExit(f"refusing overwrite: {e}")
    print("WROTE", batch_path)
    print("WROTE", notes_path)


if __name__ == "__main__":
    main()
