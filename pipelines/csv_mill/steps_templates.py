"""Declarative episode steps preserved from the reviewed CSV mill templates."""

from ._contract import bind_import_twin

TEST_COMMAND = "{test} -q --tb=short"
SOURCE_PATH = "{src}"
PRIMARY_DOCUMENT = "{doc}"
SECONDARY_DOCUMENT = "{doc2}"

EPISODES = {
    True: {
        "goal": "Honor leftover leftover leftover {keep}; {naive} is not the index.",
        "plan": "Read {short}, try first patch, then leftover leftover leftover {keep}.",
        "outcome": "leftover leftover leftover {keep} bound. {naive} unused (success).",
        "reward": {
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 610,
            "wasted_calls": 180,
            "cost_steps": 16,
            "plan_changes": 1,
        },
    },
    False: {
        "goal": "Do not drop leftover leftover leftover {keep} when binding {naive}.",
        "plan": "Read drop-{keep}, try {naive}, then hand off dropped leftover leftover leftover {keep} grain.",
        "outcome": "Still drop-{keep}; leftover leftover leftover {keep} grain is {drop_stack} — handoff {ticket}.",
        "reward": {
            "success": False,
            "tests_passed": 2,
            "retries": 2,
            "duration_min": 640,
            "wasted_calls": 210,
            "cost_steps": 17,
            "plan_changes": 1,
        },
    },
}


SUCCESS = (
    (
        "Plan",
        "list src {short} and tests before touching conversion or config.",
        "bash",
        {"command": "ls -la src {short} tests | head -40"},
        "{src} {cfg}\n{test}",
        "Tree shows {src} plus tests. Run the named failing target next.",
    ),
    (
        "Observation",
        "listing named the test files. Run `{test} -q --tb=short` to capture the failure.",
        "pytest",
        {"args": TEST_COMMAND},
        "{test}::{test_ok} FAILED\n"
        "E   AssertionError: leftover {naive} parse missed leftover leftover leftover {keep}",
        "Failure is at {test}::{test_ok}. Read that test before a one-line fix.",
    ),
    (
        "Observation",
        "{test}::{test_ok} is red. Read {test} around the assertion.",
        "read",
        {"path": "{test}"},
        "def {test_ok}():\n    assert parse(b'x')['kind'] == {mod!r}\n",
        "Test contract is visible. Search implementation symbols next.",
    ),
    (
        "Observation",
        "test file imported the production helper. Grep those symbols.",
        "bash",
        {"command": "rg -n '{keep}|{naive}' src {short} tests"},
        "{src}:2: return {{{naive!r}: True}}",
        "Grep hit {src}. Read it before editing the first match.",
    ),
    (
        "Observation",
        "grep listed {src}. Read it before any patch.",
        "read",
        {"path": SOURCE_PATH},
        "def parse(blob):\n    return {{{naive!r}: True}}\n",
        "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
    ),
    (
        "Observation",
        "local files are in. Need the changelog/registry before editing.",
        "fetch",
        {"url": PRIMARY_DOCUMENT},
        "GET {doc}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
        "Call failed with upstream gateway failure. Recover with backoff.",
    ),
    (
        "Observation",
        "the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
        "fetch",
        {"url": PRIMARY_DOCUMENT},
        "retry after 2s backoff; local vendor fixture\n"
        "HTTP/1.1 200 OK\n"
        "leftover leftover leftover {keep} is required; naive {naive} is not enough.",
        "Degraded path used the local fixture. Continue with that content.",
    ),
    (
        "Observation",
        "local files are in. Need the second remote document before editing.",
        "fetch",
        {"url": SECONDARY_DOCUMENT},
        "GET {doc2}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0",
        "Call failed with rate-limit status with Retry-After. Recover with backoff.",
    ),
    (
        "Observation",
        "the prior call returned rate-limit status with Retry-After. Sleep then retry.",
        "fetch",
        {"url": SECONDARY_DOCUMENT},
        "sleep + jitter retry of the same URL\n"
        "HTTP/1.1 200 OK\n"
        "Keep leftover leftover leftover {keep}. Not r106-r113 clones. Not search-index.",
        "Retry succeeded. Resume the local debug plan with that document in hand.",
    ),
    (
        "Observation",
        "docs and source are in. Apply the first patch to {src}.",
        "edit",
        {
            "path": SOURCE_PATH,
            "old": "    return {{{naive!r}: True}}",
            "new": "    return {{{naive!r}: True, {first_wrong!r}: True}}",
        },
        "patched first apply still wrong for leftover leftover leftover {keep}",
        "Patch applied. Re-run the failing test; do not assume green.",
    ),
    (
        "Observation",
        "edit wrote {src}. Re-run the same failing node.",
        "pytest",
        {"args": TEST_COMMAND},
        "{test}::{test_ok} FAILED\n"
        "E   AssertionError: first patch is not leftover leftover leftover {keep}",
        "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
    ),
    (
        "Observation",
        "post-edit test still failed ({test}::{test_ok}). Re-read {src}.",
        "read",
        {"path": SOURCE_PATH},
        "leftover leftover leftover {keep} is the real index; first patch is {naive}-only",
        "Plan change: Bind leftover leftover leftover {keep}. {naive} parse is not the index.",
    ),
    (
        "Reflection",
        "Bind leftover leftover leftover {keep}. {naive} parse is not the index.",
        "edit",
        {
            "path": SOURCE_PATH,
            "old": "    return {{{naive!r}: True, {first_wrong!r}: True}}",
            "new": "    return {{'kind': {mod!r}, {keep!r}: True}}",
        },
        "patched leftover leftover leftover {keep}",
        "Corrective patch applied. Run the original failing node again.",
    ),
    (
        "Observation",
        "fix edit returned clean. Re-run the original failing test node.",
        "pytest",
        {"args": TEST_COMMAND},
        "1 passed in 0.16s",
        "Result recorded. Run one broader check before declaring the outcome.",
    ),
    (
        "Observation",
        "focused run finished. Run broader check `pytest {test} -q`.",
        "bash",
        {"command": "pytest {test} -q"},
        "3 passed in 0.28s",
        "Broader check captured. Stop; residual risk belongs in the outcome text.",
    ),
    (
        "Observation",
        "broader check is on disk. Show the diff of patched files for the handoff note.",
        "bash",
        {"command": "git diff --stat | head -n 40"},
        "diffstat for {slug}: {src} | 9 ++++++---. No other modified paths.",
        "Diff is the review artifact. No further edits.",
    ),
)

FAILURE = (
    (
        "Plan",
        "list src {dshort} and tests before touching conversion or config.",
        "bash",
        {"command": "ls -la src {dshort} tests | head -40"},
        "{src} {cfg}\n{test}",
        "Tree shows {src} plus tests. Run the named failing target next.",
    ),
    (
        "Observation",
        "listing named the test files. Run `{test} -q --tb=short` to capture the failure.",
        "pytest",
        {"args": TEST_COMMAND},
        "{test}::{test_fail} FAILED\n"
        "E   AssertionError: dropped leftover leftover leftover {keep}; {naive} still owned",
        "Failure is at {test}::{test_fail}. Read that test before a one-line fix.",
    ),
    (
        "Observation",
        "{test}::{test_fail} is red. Read {test} around the assertion.",
        "read",
        {"path": "{test}"},
        "def {test_fail}():\n    assert 'handoff' in parse(b'x')\n",
        "Test contract is visible. Search implementation symbols next.",
    ),
    (
        "Observation",
        "test file imported the production helper. Grep those symbols.",
        "bash",
        {"command": "rg -n '{keep}|{naive}|drop' src {dshort} tests"},
        "{src}:2: return {{{naive!r}: True}}",
        "Grep hit {src}. Read it before editing the first match.",
    ),
    (
        "Observation",
        "grep listed {src}. Read it before any patch.",
        "read",
        {"path": SOURCE_PATH},
        "def parse(blob):\n    return {{{naive!r}: True}}\n",
        "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
    ),
    (
        "Observation",
        "local files are in. Need the changelog/registry before editing.",
        "fetch",
        {"url": PRIMARY_DOCUMENT},
        "GET {doc}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0",
        "Call failed with rate-limit status with Retry-After. Recover with backoff.",
    ),
    (
        "Observation",
        "the prior call returned rate-limit status with Retry-After. Sleep then retry.",
        "fetch",
        {"url": PRIMARY_DOCUMENT},
        "sleep + jitter retry of the same URL\n"
        "HTTP/1.1 200 OK\n"
        "{drop_stack} is platform; hand off {ticket}.",
        "Retry succeeded. Continue with that document.",
    ),
    (
        "Observation",
        "local files are in. Need the second remote document before editing.",
        "fetch",
        {"url": SECONDARY_DOCUMENT},
        "GET {doc2}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
        "Call failed with upstream gateway failure. Recover with backoff.",
    ),
    (
        "Observation",
        "the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
        "fetch",
        {"url": SECONDARY_DOCUMENT},
        "retry after 2s backoff; local vendor fixture\n"
        "HTTP/1.1 200 OK\n"
        "Handoff {ticket}. Not leftover leftover leftover unlink clones.",
        "Degraded path used the local fixture. Resume the local debug plan.",
    ),
    (
        "Observation",
        "docs and source are in. Apply the first patch to {src}.",
        "edit",
        {
            "path": SOURCE_PATH,
            "old": "    return {{{naive!r}: True}}",
            "new": "    return {{{naive!r}: True, 'flatten': True}}",
        },
        "patched first apply still {drop_stack}-owned",
        "Patch applied. Re-run the failing test; do not assume green.",
    ),
    (
        "Observation",
        "edit wrote {src}. Re-run the same failing node.",
        "pytest",
        {"args": TEST_COMMAND},
        "{test}::{test_fail} FAILED\n"
        "E   AssertionError: cannot mint leftover leftover leftover {keep} here",
        "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
    ),
    (
        "Observation",
        "post-edit test still failed ({test}::{test_fail}). Re-read {src}.",
        "read",
        {"path": SOURCE_PATH},
        "Dropped leftover leftover leftover {keep} is ingest-plat; cannot bind {naive}-as-key",
        "Plan change: Dropped leftover leftover leftover {keep} is ingest-plat. Handoff {ticket}.",
    ),
    (
        "Reflection",
        "Dropped leftover leftover leftover {keep} is ingest-plat. Handoff {ticket}.",
        "edit",
        {
            "path": "{drop}/handoff.md",
            "old": "",
            "new": "# {ticket} leftover leftover leftover {keep} grain owned by ingest-plat",
        },
        "ticket filed. still drop-{keep}",
        "Handoff ticket written. Run the original failing node again.",
    ),
    (
        "Observation",
        "handoff edit returned clean. Re-run the original failing test node.",
        "pytest",
        {"args": TEST_COMMAND},
        "{test}::{test_fail} FAILED  # handoff: {ticket}\n1 failed",
        "Result recorded. Run one broader check before declaring the outcome.",
    ),
    (
        "Observation",
        "focused run finished. Run broader check `pytest {test} -q; echo {ticket}`.",
        "bash",
        {"command": "pytest {test} -q; echo {ticket}"},
        "1 failed, 2 passed\n{ticket}",
        "Broader check captured. Residual risk belongs in the outcome text.",
    ),
    (
        "Observation",
        "broader check is on disk. Show the diff of patched files for the handoff note.",
        "bash",
        {"command": "git diff --stat | head -n 40"},
        "diffstat for {fail}: {src} | 8 +++++---. {drop}/handoff.md added.",
        "Diff is the review artifact. Lint next.",
    ),
    (
        "Observation",
        "diffstat listed the patched files. Run a linter on those paths only.",
        "bash",
        {"command": "ruff check tests || true; echo lint-end"},
        "All checks passed!\nlint-end",
        "Lint clean. Episode complete.",
    ),
)

bind_import_twin(__name__)
