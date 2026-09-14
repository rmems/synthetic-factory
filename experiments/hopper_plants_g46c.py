"""Second unique hopper wave. Do not clone g46/g46b or intervening search/lrd."""

PREFIX = {
    "rate-limit-backoff-factory": "rlb",
    "queue-backpressure-factory": "qbp",
    "csv-excel-ingest-factory": "cei",
    "websocket-reconnect-factory": "wsr",
    "email-webhook-retry-factory": "ewr",
    "feature-flag-debug-factory": "ffd",
    "search-index-rebuild-factory": "sir",
    "log-redaction-factory": "lrd",
}

START = {
    "rate-limit-backoff-factory": 58,
    "queue-backpressure-factory": 37,
    "csv-excel-ingest-factory": 37,
    "websocket-reconnect-factory": 37,
    "email-webhook-retry-factory": 36,
    "feature-flag-debug-factory": 37,
    "search-index-rebuild-factory": 49,
    "log-redaction-factory": 51,
}

CYCLE = list(PREFIX)


def _p(**kwargs):
    return kwargs


PAIRS = {
    "rate-limit-backoff-factory": [
        (
            _p(
                slug="intercom-app-vs-workspace-rate",
                goal="Honor Intercom per-app X-RateLimit-Remaining, not the workspace bucket.",
                plan="Read app-as-workspace, try share, then key remaining on app id.",
                mod="ic_app",
                test_fn="test_app_not_workspace",
                src_body=(
                    "def bucket(h):\n"
                    "    return 'workspace' if h.get('X-Intercom-App-Id') else 'ok'\n"
                ),
                test_body=(
                    "def test_app_not_workspace():\n"
                    "    assert bucket({'X-Intercom-App-Id': 'a1'}) == 'app'\n"
                ),
                grep_pat="X-Intercom-App-Id|workspace|X-RateLimit-Remaining",
                grep_hit="src/ic_app.py:2: return 'workspace' if h.get('X-Intercom-App-Id') else 'ok'",
                fail_msg="AssertionError: app 429 slept the workspace bucket and stalled other apps",
                first_old="    return 'workspace' if h.get('X-Intercom-App-Id') else 'ok'",
                first_new="    return 'workspace_share' if h.get('X-Intercom-App-Id') else 'ok'",
                first_obs="patched workspace_share (still one bucket)",
                still_msg="AssertionError: per-app remaining must not drain the workspace budget",
                reread_obs="Intercom REST rate is per app id; workspace rate is a second counter",
                plan_change="Key sleep on app remaining. Do not debit workspace for an app 429.",
                fix_new="    return 'app' if h.get('X-Intercom-App-Id') else 'ok'",
                fix_obs="patched app-scoped remaining",
                docs_url="https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting/",
                docs_ok="Intercom has per-app and per-workspace limits as separate counters.",
                docs_url2="https://developers.intercom.com/docs/build-an-integration/learn-more/rest-apis/",
                docs_ok2="An app 429 must not pause other apps. Not Retry-After catalog.",
                outcome="App-scoped remaining unblocked other apps. Workspace unused (success).",
                domain="intercom-app-rate-vs-workspace-rate",
                stack="Intercom REST rate limits",
                seed="intercom-app-vs-workspace-rate",
                residual="Workspace budget is a second counter. Not Coda/ClickUp clones.",
                coverage=86,
            ),
            _p(
                slug="pagerduty-events-plan-handoff",
                goal="Do not retry PagerDuty Events API 429 as REST request-rate.",
                plan="Read events-as-rest, try 2s, then hand off Events plan cap.",
                mod="pd_evt",
                test_fn="test_events_not_rest",
                src_body=(
                    "def classify(host, status):\n"
                    "    return 'rest' if status == 429 else 'ok'\n"
                ),
                test_body=(
                    "def test_events_not_rest():\n"
                    "    assert classify('events.pagerduty.com', 429) != 'rest'\n"
                ),
                grep_pat="events.pagerduty|429|rest",
                grep_hit="src/pd_evt.py:2: return 'rest' if status == 429 else 'ok'",
                fail_msg="AssertionError: Events 429 retried as REST; plan cap is billing",
                first_old="    return 'rest' if status == 429 else 'ok'",
                first_new="    return 'rest_2s' if status == 429 else 'ok'",
                first_obs="patched 2s (still REST-classed)",
                still_msg="AssertionError: Events plan cap is not REST rps; billing owns it",
                reread_obs="events.pagerduty.com 429 is Events API plan, not api.pagerduty.com REST",
                plan_change="Events plan is billing. Handoff PD-EVT-5.",
                fix_new="    return 'handoff_PD-EVT-5' if 'events' in host else 'ok'",
                fix_obs="ticket filed. still rest-classed",
                docs_url="https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTUz-events-api-v2-overview",
                docs_ok="Events API has its own throttle, separate from REST.",
                docs_url2="https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU4-events-api-v2-rate-limiting",
                docs_ok2="Sleep cannot mint Events volume. Handoff PD-EVT-5. Not Retry-After catalog.",
                outcome="Still rest-classed; Events plan is billing — handoff PD-EVT-5.",
                domain="pagerduty-events-plan-vs-rest-rps",
                stack="PagerDuty Events API",
                seed="pagerduty-events-plan-handoff",
                residual="Sleep cannot mint Events volume.",
                ticket="PD-EVT-5",
                ticket_why="Events API plan owned by billing-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="reddit-used-vs-remaining",
                goal="Honor Reddit X-Ratelimit-Remaining; do not treat X-Ratelimit-Used as remaining.",
                plan="Read used-as-remaining, try 600-minus, then Remaining header.",
                mod="rd_rem",
                test_fn="test_used_not_remaining",
                src_body=(
                    "def remaining(h):\n"
                    "    return int(h['X-Ratelimit-Used'])\n"
                ),
                test_body=(
                    "def test_used_not_remaining():\n"
                    "    h = {'X-Ratelimit-Used': '40', 'X-Ratelimit-Remaining': '560',"
                    " 'X-Ratelimit-Reset': '60'}\n"
                    "    assert remaining(h) == 560\n"
                ),
                grep_pat="X-Ratelimit-Used|X-Ratelimit-Remaining",
                grep_hit="src/rd_rem.py:2: return int(h['X-Ratelimit-Used'])",
                fail_msg="AssertionError: 40 == 560; Used is consumed count not remaining",
                first_old="    return int(h['X-Ratelimit-Used'])",
                first_new="    return 600 - int(h['X-Ratelimit-Used'])",
                first_obs="patched 600-minus (hardcoded; Reset unused)",
                still_msg="AssertionError: still wrong when window is 100; do not hardcode 600",
                reread_obs="Used=40 Remaining=560; remaining is the Remaining header",
                plan_change="Use X-Ratelimit-Remaining. Used is not remaining. Not GitLab Observed clone.",
                fix_new="    return int(h['X-Ratelimit-Remaining'])",
                fix_obs="patched Remaining header",
                docs_url="https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki",
                docs_ok="X-Ratelimit-Used is consumed; X-Ratelimit-Remaining is wait budget.",
                docs_url2="https://www.reddit.com/dev/api/",
                docs_ok2="Prefer Remaining. Not GitLab Observed, not Retry-After catalog.",
                outcome="Remaining matched 560. Used unused (success).",
                domain="reddit-ratelimit-used-vs-remaining",
                stack="Reddit OAuth rate headers",
                seed="reddit-used-vs-remaining",
                residual="Used is consumed count. Not GitLab Observed clone.",
                coverage=85,
            ),
            _p(
                slug="mastodon-instance-plan-handoff",
                goal="Do not retry Mastodon 429 as a sleepable per-call rate when the instance is plan-capped.",
                plan="Read instance-as-sleep, try 300s, then hand off instance plan.",
                mod="ms_plan",
                test_fn="test_instance_not_sleep",
                src_body=(
                    "def classify(status, ctx):\n"
                    "    return 'sleep_2s' if status == 429 else 'ok'\n"
                ),
                test_body=(
                    "def test_instance_not_sleep():\n"
                    "    assert classify(429, {'scope': 'instance'}) != 'sleep_2s'\n"
                ),
                grep_pat="instance|429|sleep",
                grep_hit="src/ms_plan.py:2: return 'sleep_2s' if status == 429 else 'ok'",
                fail_msg="AssertionError: instance 429 slept 2s; plan is hosting",
                first_old="    return 'sleep_2s' if status == 429 else 'ok'",
                first_new="    return 'sleep_300' if status == 429 else 'ok'",
                first_obs="patched 300s (still treating plan cap as per-call rate)",
                still_msg="AssertionError: sleep cannot mint a Mastodon instance plan",
                reread_obs="429 X-RateLimit-Limit on /api/v1/statuses is instance plan",
                plan_change="Instance plan is hosting. Handoff MS-PLAN-3.",
                fix_new="    return 'handoff_MS-PLAN-3' if status == 429 else 'ok'",
                fix_obs="ticket filed. still rate-classed",
                docs_url="https://docs.joinmastodon.org/api/rate-limits/",
                docs_ok="Mastodon 429 can be the instance plan, not the per-account window.",
                docs_url2="https://docs.joinmastodon.org/methods/statuses/",
                docs_ok2="Sleep cannot change instance plan. Handoff MS-PLAN-3.",
                outcome="Still rate-classed; instance plan is hosting — handoff MS-PLAN-3.",
                domain="mastodon-instance-plan-vs-sleep",
                stack="Mastodon REST statuses",
                seed="mastodon-instance-plan-handoff",
                residual="Sleep cannot mint an instance plan.",
                ticket="MS-PLAN-3",
                ticket_why="instance plan 429 owned by hosting-plat",
                coverage=85,
            ),
        ),
    ],
    "queue-backpressure-factory": [
        (
            _p(
                slug="taskiq-prefetch-vs-timeout",
                goal="Bound Taskiq max_prefetch; do not raise ack timeout to hide OCR lag.",
                plan="Read prefetch-as-timeout, try 180s, then prefetch=8 plus ack.",
                mod="tq_pre",
                test_fn="test_prefetch_not_timeout",
                src_body=(
                    "def tune(lag):\n"
                    "    return {'ack_timeout_s': 60} if lag else {}\n"
                ),
                test_body=(
                    "def test_prefetch_not_timeout():\n"
                    "    t = tune(True)\n"
                    "    assert t.get('max_prefetch') == 8 and 'ack_timeout_s' not in t\n"
                ),
                grep_pat="ack_timeout_s|max_prefetch|taskiq",
                grep_hit="src/tq_pre.py:2: return {'ack_timeout_s': 60} if lag else {}",
                fail_msg="AssertionError: lag stretched ack timeout; prefetch still unbounded",
                first_old="    return {'ack_timeout_s': 60} if lag else {}",
                first_new="    return {'ack_timeout_s': 180} if lag else {}",
                first_obs="patched 180s (still a timeout integer)",
                still_msg="AssertionError: timeout integer cannot bound max_prefetch",
                reread_obs="Taskiq broker max_prefetch default is unbounded on OCR",
                plan_change="max_prefetch=8 plus ack. Timeout is not a queue bound.",
                fix_new="    return {'max_prefetch': 8, 'ack': True} if lag else {}",
                fix_obs="patched max_prefetch=8",
                docs_url="https://taskiq-python.github.io/guide/architecture.html",
                docs_ok="max_prefetch bounds unacked messages; ack timeout is a clock.",
                docs_url2="https://taskiq-python.github.io/guide/extending-broker.html",
                docs_ok2="Use a finite prefetch, not a longer ack clock. Not Cloud Tasks.",
                outcome="Prefetch 8 plus ack drained lag. Timeout unused (success).",
                domain="taskiq-max-prefetch-vs-ack-timeout",
                stack="Taskiq broker prefetch",
                seed="taskiq-prefetch-vs-timeout",
                residual="Ack timeout is not a queue bound. Not Hatchet/Dapr clones.",
                coverage=86,
            ),
            _p(
                slug="procrastinate-lock-handoff",
                goal="Do not raise Procrastinate retry delay to hide a job lock mismatch.",
                plan="Read lock-as-retry, try 60s, then hand off lock.",
                mod="prc_lk",
                test_fn="test_lock_not_retry",
                src_body=(
                    "def tune(poison):\n"
                    "    return {'retry_delay_s': 10} if poison else {}\n"
                ),
                test_body=(
                    "def test_lock_not_retry():\n"
                    "    assert 'retry_delay_s' not in tune(True)\n"
                ),
                grep_pat="retry_delay_s|lock|procrastinate",
                grep_hit="src/prc_lk.py:2: return {'retry_delay_s': 10} if poison else {}",
                fail_msg="AssertionError: lock mismatch retried; delay cannot mint a lock",
                first_old="    return {'retry_delay_s': 10} if poison else {}",
                first_new="    return {'retry_delay_s': 60} if poison else {}",
                first_obs="patched 60s (still a retry integer)",
                still_msg="AssertionError: retry delay cannot change Procrastinate lock",
                reread_obs="queueing.lock vs job.lock mismatch on OCR invoice jobs",
                plan_change="Lock is platform. Handoff PRC-LK-4.",
                fix_new="    return {'handoff': 'PRC-LK-4'} if poison else {}",
                fix_obs="ticket filed. still retry-classed",
                docs_url="https://procrastinate.readthedocs.io/en/stable/howto/advanced/locks.html",
                docs_ok="Locks are queueing constraints, not retry delays.",
                docs_url2="https://procrastinate.readthedocs.io/en/stable/howto/basics/retry.html",
                docs_ok2="Retry cannot mint a lock. Handoff PRC-LK-4. Not Cloud Tasks.",
                outcome="Still retry-classed; lock is platform — handoff PRC-LK-4.",
                domain="procrastinate-lock-vs-retry-delay",
                stack="Procrastinate locks",
                seed="procrastinate-lock-handoff",
                residual="Retry delay is not a lock.",
                ticket="PRC-LK-4",
                ticket_why="job lock owned by queue-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="camel-seda-size-vs-timeout",
                goal="Bound Apache Camel SEDA queue size; do not raise poll timeout to hide overflow.",
                plan="Read size-as-timeout, try 60s, then size=32 plus blockWhenFull.",
                mod="cml_sd",
                test_fn="test_size_not_poll",
                src_body=(
                    "def tune(overflow):\n"
                    "    return {'poll_timeout_s': 15} if overflow else {}\n"
                ),
                test_body=(
                    "def test_size_not_poll():\n"
                    "    t = tune(True)\n"
                    "    assert t.get('size') == 32 and 'poll_timeout_s' not in t\n"
                ),
                grep_pat="poll_timeout_s|blockWhenFull|seda",
                grep_hit="src/cml_sd.py:2: return {'poll_timeout_s': 15} if overflow else {}",
                fail_msg="AssertionError: overflow slept poll timeout; SEDA still unbounded",
                first_old="    return {'poll_timeout_s': 15} if overflow else {}",
                first_new="    return {'poll_timeout_s': 60} if overflow else {}",
                first_obs="patched 60s (still a timeout integer)",
                still_msg="AssertionError: poll timeout cannot bound seda:?size=",
                reread_obs="seda:ocr?size=Integer.MAX; overflow OOM on OCR",
                plan_change="size=32 plus blockWhenFull. Poll timeout is not a queue bound.",
                fix_new="    return {'size': 32, 'blockWhenFull': True} if overflow else {}",
                fix_obs="patched size=32",
                docs_url="https://camel.apache.org/components/4.8.x/seda-component.html",
                docs_ok="SEDA size bounds memory; poll timeout is a stall clock.",
                docs_url2="https://camel.apache.org/components/4.8.x/eips/durable-seda.html",
                docs_ok2="Use a finite size plus blockWhenFull. Not Cloud Tasks.",
                outcome="Size 32 plus blockWhenFull stopped OOM. Poll unused (success).",
                domain="camel-seda-size-vs-poll-timeout",
                stack="Apache Camel SEDA",
                seed="camel-seda-size-vs-timeout",
                residual="Poll timeout is not a queue bound.",
                coverage=84,
            ),
            _p(
                slug="zeromq-hwm-handoff",
                goal="Do not raise ZeroMQ linger to hide a high-water-mark stall.",
                plan="Read hwm-as-linger, try 30s, then hand off HWM.",
                mod="zmq_hw",
                test_fn="test_hwm_not_linger",
                src_body=(
                    "def tune(blocked):\n"
                    "    return {'linger_s': 10} if blocked else {}\n"
                ),
                test_body=(
                    "def test_hwm_not_linger():\n"
                    "    assert 'linger_s' not in tune(True)\n"
                ),
                grep_pat="linger_s|ZMQ_SNDHWM|hwm",
                grep_hit="src/zmq_hw.py:2: return {'linger_s': 10} if blocked else {}",
                fail_msg="AssertionError: HWM stall slept linger; SNDHWM still 0",
                first_old="    return {'linger_s': 10} if blocked else {}",
                first_new="    return {'linger_s': 30} if blocked else {}",
                first_obs="patched 30s (still a timeout integer)",
                still_msg="AssertionError: linger cannot mint ZMQ_SNDHWM",
                reread_obs="ZMQ_SNDHWM=0 infinite; OCR publisher blocks",
                plan_change="HWM is platform. Handoff ZMQ-HWM-2.",
                fix_new="    return {'handoff': 'ZMQ-HWM-2'} if blocked else {}",
                fix_obs="ticket filed. still linger-classed",
                docs_url="https://zeromq.org/socket-api/#high-water-marks",
                docs_ok="HWM is socket credit, not linger timeout.",
                docs_url2="https://libzmq.readthedocs.io/en/zeromq3-x/zmq_setsockopt.html",
                docs_ok2="Linger cannot mint HWM. Handoff ZMQ-HWM-2. Not Cloud Tasks.",
                outcome="Still linger-classed; HWM is platform — handoff ZMQ-HWM-2.",
                domain="zeromq-sndhwm-vs-linger",
                stack="ZeroMQ HWM",
                seed="zeromq-hwm-handoff",
                residual="Linger is not HWM.",
                ticket="ZMQ-HWM-2",
                ticket_why="ZMQ_SNDHWM owned by messaging-plat",
                coverage=84,
            ),
        ),
    ],
    "csv-excel-ingest-factory": [
        (
            _p(
                slug="xlsx-customxml-invoice-map",
                goal="Read customXml mapped invoice fields, not the empty display cells.",
                plan="Read display-as-map, try shared strings, then customXml item1.",
                mod="xlsx_cx",
                test_fn="test_customxml_not_display",
                src_body=(
                    "def amount(ws):\n"
                    "    return ws.cell('B2').display\n"
                ),
                test_body=(
                    "def test_customxml_not_display():\n"
                    "    assert amount(ws) == '10.00'\n"
                ),
                grep_pat="customXml|display|item1.xml",
                grep_hit="src/xlsx_cx.py:2: return ws.cell('B2').display",
                fail_msg="AssertionError: '' == '10.00'; mapped invoice lives in customXml",
                first_old="    return ws.cell('B2').display",
                first_new="    return ws.cell('B2').sst or ''",
                first_obs="patched sst (still empty display, not customXml)",
                still_msg="AssertionError: sst still misses customXml invoice mapping",
                reread_obs="xl/customXml/item1.xml maps amt=10.00; B2 is a bound empty display",
                plan_change="Read customXml mapped fields. Display cells are not the invoice.",
                fix_new="    return ws.custom_xml_map('amt')",
                fix_obs="patched customXml map",
                docs_url="https://learn.microsoft.com/en-us/office/open-xml/working-with-custom-xml-parts",
                docs_ok="Custom XML parts hold mapped content; display cells can be empty.",
                docs_url2="https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/",
                docs_ok2="Invoice amt lives in item1.xml. Not quoted-newline, not WPS .et.",
                outcome="customXml map recovered 10.00. Display unused (success).",
                domain="xlsx-customxml-mapped-invoice-vs-display-cell",
                stack="OOXML customXml maps",
                seed="xlsx-customxml-invoice-map",
                residual="Not XLOOKUP/ListObject clones. Not Kingsoft .et.",
                coverage=87,
            ),
            _p(
                slug="jmp-binary-handoff",
                goal="Do not parse JMP .jmp as xlsx ZIP.",
                plan="Read jmp-as-xlsx, try zipfile, then hand off jmp reader.",
                mod="jmp_bin",
                test_fn="test_jmp_not_xlsx",
                src_body=(
                    "def load(path):\n"
                    "    import zipfile\n"
                    "    return zipfile.ZipFile(path).namelist()\n"
                ),
                test_body=(
                    "def test_jmp_not_xlsx():\n"
                    "    assert not str(load('invoices.jmp')).startswith('xl/')\n"
                ),
                grep_pat="ZipFile|\\.jmp|jmp",
                grep_hit="src/jmp_bin.py:3: return zipfile.ZipFile(path).namelist()",
                fail_msg="AssertionError: JMP magic opened as ZIP; BadZipFile swallowed",
                first_old="    return zipfile.ZipFile(path).namelist()",
                first_new="    return zipfile.ZipFile(path, mode='r').namelist() or ['xl/worksheets']",
                first_obs="patched default sheet (still ZIP, still not .jmp)",
                still_msg="AssertionError: forcing xl/ paths cannot decode JMP",
                reread_obs="JMP is a SAS Institute binary table; not OOXML",
                plan_change="Binary .jmp is stats-plat. Handoff JMP-BIN-4.",
                fix_new="    return {'handoff': 'JMP-BIN-4'}",
                fix_obs="ticket filed. still zip-classed",
                docs_url="https://www.jmp.com/support/help/en/18.0/#page/jmp/jmp-file-types.shtml",
                docs_ok="JMP data tables are a proprietary binary, not OOXML.",
                docs_url2="https://www.jmp.com/support/help/en/18.0/",
                docs_ok2="Need JMP reader. Handoff JMP-BIN-4. Not Kingsoft .et.",
                outcome="Still zip-classed; .jmp is binary — handoff JMP-BIN-4.",
                domain="jmp-binary-vs-xlsx-zip",
                stack="JMP .jmp",
                seed="jmp-binary-handoff",
                residual="Not SAS7BDAT/SPSS clones.",
                ticket="JMP-BIN-4",
                ticket_why=".jmp binary ingest owned by stats-plat",
                coverage=87,
            ),
        ),
        (
            _p(
                slug="xlsx-querytable-cache",
                goal="Read queryTable cached rows, not the empty worksheet used range.",
                plan="Read used-as-query, try dimension, then queryTable cache.",
                mod="xlsx_qt",
                test_fn="test_querytable_not_used",
                src_body=(
                    "def rows(ws):\n"
                    "    return ws.used_range\n"
                ),
                test_body=(
                    "def test_querytable_not_used():\n"
                    "    assert rows(ws) == 'queryTable1'\n"
                ),
                grep_pat="queryTable|used_range|connection",
                grep_hit="src/xlsx_qt.py:2: return ws.used_range",
                fail_msg="AssertionError: used range empty; invoice rows live in queryTable cache",
                first_old="    return ws.used_range",
                first_new="    return ws.dimension",
                first_obs="patched dimension (still the sheet, not queryTable)",
                still_msg="AssertionError: dimension is still empty; cache is queryTable1",
                reread_obs="xl/queryTables/queryTable1.xml caches the invoice connection rows",
                plan_change="Read queryTable cache. Used range is the empty display.",
                fix_new="    return ws.query_table('queryTable1')",
                fix_obs="patched queryTable cache",
                docs_url="https://learn.microsoft.com/en-us/office/vba/api/excel.querytable",
                docs_ok="QueryTable.ResultRange is the cached connection; UsedRange can be empty.",
                docs_url2="https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/",
                docs_ok2="queryTable1.xml holds invoice rows. Not quoted-newline, not WPS .et.",
                outcome="queryTable cache ingested invoices. Used range unused (success).",
                domain="xlsx-querytable-cache-vs-used-range",
                stack="OOXML queryTable",
                seed="xlsx-querytable-cache",
                residual="Not ListObject clone. Not Kingsoft .et.",
                coverage=85,
            ),
            _p(
                slug="minitab-mtw-handoff",
                goal="Do not parse Minitab .mtw as CSV.",
                plan="Read mtw-as-csv, try latin1, then hand off MTW reader.",
                mod="mtw_bin",
                test_fn="test_mtw_not_csv",
                src_body=(
                    "def load(path):\n"
                    "    return open(path, newline='').read().split(',')\n"
                ),
                test_body=(
                    "def test_mtw_not_csv():\n"
                    "    assert load('invoices.mtw') != open('invoices.mtw').read().split(',')\n"
                ),
                grep_pat="\\.mtw|read\\(\\).*split|minitab",
                grep_hit="src/mtw_bin.py:2: return open(path, newline='').read().split(',')",
                fail_msg="AssertionError: MTW magic parsed as CSV; worksheet header lost",
                first_old="    return open(path, newline='').read().split(',')",
                first_new="    return open(path, encoding='latin1').read().split(',')",
                first_obs="patched latin1 (still text split, still not .mtw)",
                still_msg="AssertionError: latin1 cannot decode Minitab worksheet",
                reread_obs="Minitab .mtw is a binary worksheet; need Minitab reader",
                plan_change="Binary .mtw is stats-plat. Handoff MTW-BIN-3.",
                fix_new="    return {'handoff': 'MTW-BIN-3'}",
                fix_obs="ticket filed. still csv-split",
                docs_url="https://support.minitab.com/en-us/minitab/help-and-how-to/data-import-and-export/",
                docs_ok="Minitab worksheets (.mtw) are binary, not CSV.",
                docs_url2="https://support.minitab.com/en-us/minitab/",
                docs_ok2="Need Minitab reader. Handoff MTW-BIN-3. Not Kingsoft .et.",
                outcome="Still csv-split; .mtw is binary — handoff MTW-BIN-3.",
                domain="minitab-mtw-binary-vs-csv-text",
                stack="Minitab .mtw",
                seed="minitab-mtw-handoff",
                residual="latin1 is not a Minitab reader.",
                ticket="MTW-BIN-3",
                ticket_why=".mtw binary ingest owned by stats-plat",
                coverage=85,
            ),
        ),
    ],
    "websocket-reconnect-factory": [
        (
            _p(
                slug="actioncable-confirm-subscription",
                goal="Wait for Action Cable confirm_subscription before sending; do not reconnect.",
                plan="Read send-before-confirm, try sleep, then wait confirm_subscription.",
                mod="ac_sub",
                test_fn="test_confirm_before_send",
                src_body=(
                    "def on_open():\n"
                    "    return ['send', 'subscribe']\n"
                ),
                test_body=(
                    "def test_confirm_before_send():\n"
                    "    assert on_open()[0] == 'subscribe'\n"
                    "    assert 'confirm' in on_open()\n"
                ),
                grep_pat="confirm_subscription|subscribe|reconnect",
                grep_hit="src/ac_sub.py:2: return ['send', 'subscribe']",
                fail_msg="AssertionError: send before confirm 1006; reconnect looped",
                first_old="    return ['send', 'subscribe']",
                first_new="    return ['sleep', 'send', 'subscribe']",
                first_obs="patched sleep (still send first)",
                still_msg="AssertionError: sleep cannot confirm; send still races subscribe",
                reread_obs="Action Cable requires subscribe then confirm_subscription before speak",
                plan_change="subscribe, wait confirm, then send. Do not reconnect-loop as cookie-replay.",
                fix_new="    return ['subscribe', 'confirm', 'send']",
                fix_obs="patched confirm-then-send",
                docs_url="https://guides.rubyonrails.org/action_cable_overview.html#subscriptions",
                docs_ok="The client must wait for confirm_subscription before speaking.",
                docs_url2="https://guides.rubyonrails.org/action_cable_overview.html#client-server-interactions",
                docs_ok2="Unconfirmed send 1006s. Not cookie-replay. Not Channels accept clone.",
                outcome="confirm-then-send joined invoices. Reconnect unused (success).",
                domain="actioncable-confirm-subscription-vs-reconnect",
                stack="Rails Action Cable",
                seed="actioncable-confirm-subscription",
                residual="Not cookie-replay. Not Django Channels clone.",
                coverage=86,
            ),
            _p(
                slug="partykit-hibernate-handoff",
                goal="Do not treat PartyKit hibernation as a client ping miss.",
                plan="Read hibernate-as-ping, try ping 10s, then hand off hibernation.",
                mod="pk_hib",
                test_fn="test_hibernate_not_ping",
                src_body=(
                    "def tune(drop):\n"
                    "    return {'client_ping_s': 15} if drop else {}\n"
                ),
                test_body=(
                    "def test_hibernate_not_ping():\n"
                    "    assert 'client_ping_s' not in tune(True)\n"
                ),
                grep_pat="hibernate|client_ping_s|partykit",
                grep_hit="src/pk_hib.py:2: return {'client_ping_s': 15} if drop else {}",
                fail_msg="AssertionError: PartyKit hibernate dropped WS; client ping unused",
                first_old="    return {'client_ping_s': 15} if drop else {}",
                first_new="    return {'client_ping_s': 10} if drop else {}",
                first_obs="patched ping 10s (still client, not hibernation)",
                still_msg="AssertionError: client ping cannot keep a hibernated Party awake",
                reread_obs="PartyKit hibernates idle rooms; ping is not wake",
                plan_change="Hibernation is PartyKit. Handoff PK-HIB-3.",
                fix_new="    return {'handoff': 'PK-HIB-3'} if drop else {}",
                fix_obs="ticket filed. still ping-classed",
                docs_url="https://docs.partykit.io/guides/scaling-partykit-servers-with-hibernation/",
                docs_ok="Hibernation parks the isolate; client pings do not prevent it.",
                docs_url2="https://docs.partykit.io/reference/partyserver-api/",
                docs_ok2="Hibernation is edge-plat. Handoff PK-HIB-3. Not cookie-replay. Not CF DO clone.",
                outcome="Still ping-classed; hibernation is PartyKit — handoff PK-HIB-3.",
                domain="partykit-hibernate-vs-client-ping",
                stack="PartyKit hibernation",
                seed="partykit-hibernate-handoff",
                residual="Ping cannot prevent Party hibernation.",
                ticket="PK-HIB-3",
                ticket_why="PartyKit hibernation owned by edge-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="colyseus-reconnection-token",
                goal="Resume Colyseus with reconnectionToken; do not open a second room join.",
                plan="Read join-as-resume, try new session, then reconnectionToken.",
                mod="col_tok",
                test_fn="test_token_not_rejoin",
                src_body=(
                    "def resume(room):\n"
                    "    return {'join': room}\n"
                ),
                test_body=(
                    "def test_token_not_rejoin():\n"
                    "    assert 'reconnectionToken' in resume('inv')\n"
                ),
                grep_pat="reconnectionToken|join|colyseus",
                grep_hit="src/col_tok.py:2: return {'join': room}",
                fail_msg="AssertionError: second join created a new seat; token unused",
                first_old="    return {'join': room}",
                first_new="    return {'join': room, 'sessionId': 'new'}",
                first_obs="patched new session (still a second join)",
                still_msg="AssertionError: new sessionId is not reconnectionToken",
                reread_obs="Colyseus reconnect(reconnectionToken) restores the same seat",
                plan_change="Pass reconnectionToken. A second join is not resume. Not cookie-replay.",
                fix_new="    return {'reconnectionToken': room}",
                fix_obs="patched reconnectionToken",
                docs_url="https://docs.colyseus.io/server/room/#allowreconnection-client-seconds",
                docs_ok="allowReconnection issues a token; join() creates a new seat.",
                docs_url2="https://docs.colyseus.io/client/#reconnect",
                docs_ok2="Use reconnect(token). Not cookie-replay.",
                outcome="reconnectionToken restored the seat. Rejoin unused (success).",
                domain="colyseus-reconnection-token-vs-second-join",
                stack="Colyseus reconnectionToken",
                seed="colyseus-reconnection-token",
                residual="Not cookie-replay.",
                coverage=84,
            ),
            _p(
                slug="janus-admin-timeout-handoff",
                goal="Do not treat Janus Admin API session timeout as a client ping miss.",
                plan="Read admin-as-ping, try ping 5s, then hand off admin timeout.",
                mod="jn_adm",
                test_fn="test_admin_not_ping",
                src_body=(
                    "def tune(drop):\n"
                    "    return {'client_ping_s': 5} if drop else {}\n"
                ),
                test_body=(
                    "def test_admin_not_ping():\n"
                    "    assert 'client_ping_s' not in tune(True)\n"
                ),
                grep_pat="session_timeout|client_ping_s|janus",
                grep_hit="src/jn_adm.py:2: return {'client_ping_s': 5} if drop else {}",
                fail_msg="AssertionError: Janus admin session_timeout dropped WS; ping unused",
                first_old="    return {'client_ping_s': 5} if drop else {}",
                first_new="    return {'client_ping_s': 10} if drop else {}",
                first_obs="patched ping 10s (still client, not admin)",
                still_msg="AssertionError: client ping cannot raise Janus admin session_timeout",
                reread_obs="Janus Admin API session_timeout is server-side; ping is not keep-session",
                plan_change="Admin timeout is Janus. Handoff JN-ADM-2.",
                fix_new="    return {'handoff': 'JN-ADM-2'} if drop else {}",
                fix_obs="ticket filed. still ping-classed",
                docs_url="https://janus.conf.meetecho.com/docs/admin.html",
                docs_ok="Admin session_timeout is server configuration, not a client ping.",
                docs_url2="https://janus.conf.meetecho.com/docs/JS.html",
                docs_ok2="Timeout is media-plat. Handoff JN-ADM-2. Not cookie-replay. Not LiveKit clone.",
                outcome="Still ping-classed; admin timeout is Janus — handoff JN-ADM-2.",
                domain="janus-admin-session-timeout-vs-client-ping",
                stack="Janus Admin API",
                seed="janus-admin-timeout-handoff",
                residual="Ping cannot set admin timeout.",
                ticket="JN-ADM-2",
                ticket_why="session_timeout owned by media-plat",
                coverage=84,
            ),
        ),
    ],
    "email-webhook-retry-factory": [
        (
            _p(
                slug="mailpace-id-plus-event",
                goal="Dedupe MailPace webhooks on (id, event), not email address.",
                plan="Read email-as-pk, try id-only, then (id, event).",
                mod="mp_ev",
                test_fn="test_id_plus_event",
                src_body=(
                    "def upsert(ev):\n"
                    "    return ev['email']\n"
                ),
                test_body=(
                    "def test_id_plus_event():\n"
                    "    a = {'id': 'm1', 'email': 'a@b', 'event': 'delivered'}\n"
                    "    b = {'id': 'm1', 'email': 'a@b', 'event': 'opened'}\n"
                    "    assert upsert(a) != upsert(b)\n"
                ),
                grep_pat="id|event|email",
                grep_hit="src/mp_ev.py:2: return ev['email']",
                fail_msg="AssertionError: delivered+opened collapsed; email is not event pk",
                first_old="    return ev['email']",
                first_new="    return ev['id']",
                first_obs="patched id (collides across delivered vs opened)",
                still_msg="AssertionError: same id delivered+opened still one row",
                reread_obs="MailPace id is the send; event distinguishes activity",
                plan_change="PK (id, event). Email is the recipient, not the event.",
                fix_new="    return (ev['id'], ev['event'])",
                fix_obs="patched (id, event)",
                docs_url="https://docs.mailpace.com/guide/webhooks",
                docs_ok="Webhook payload has id plus event; retries replay the same pair.",
                docs_url2="https://docs.mailpace.com/reference/webhooks",
                docs_ok2="delivered and opened are different events on one id.",
                outcome="(id, event) stored both events. Email unused (success).",
                domain="mailpace-webhook-id-plus-event",
                stack="MailPace webhooks",
                seed="mailpace-id-plus-event",
                residual="Not invoice-row-dup. Not ZeptoMail clone.",
                coverage=86,
            ),
            _p(
                slug="zoho-campaigns-handoff",
                goal="Do not treat Zoho Campaigns campaignkey as a unique email event.",
                plan="Read campaign-as-event, try campaign+email, then hand off activity.",
                mod="zc_ck",
                test_fn="test_campaign_not_event",
                src_body=(
                    "def pk(ev):\n"
                    "    return ev['campaignkey']\n"
                ),
                test_body=(
                    "def test_campaign_not_event():\n"
                    "    assert pk({'campaignkey': 'c1', 'activity_id': 'a9'}) != 'c1'\n"
                ),
                grep_pat="campaignkey|activity_id|Zoho Campaigns",
                grep_hit="src/zc_ck.py:2: return ev['campaignkey']",
                fail_msg="AssertionError: campaignkey collapsed all opens for that campaign",
                first_old="    return ev['campaignkey']",
                first_new="    return ev['campaignkey'] + ':' + ev.get('email', '')",
                first_obs="patched campaign+email (still campaign grain, not event)",
                still_msg="AssertionError: two opens in one campaign still one row",
                reread_obs="campaignkey is the newsletter; activity_id is the open/click",
                plan_change="campaignkey is campaign grain. Handoff ZC-CK-3.",
                fix_new="    return {'handoff': 'ZC-CK-3'}",
                fix_obs="ticket filed. still campaign-grained",
                docs_url="https://www.zoho.com/campaigns/help/developers/campaigns.html",
                docs_ok="campaignkey identifies the campaign, not a send or open.",
                docs_url2="https://www.zoho.com/campaigns/help/developers/webhooks.html",
                docs_ok2="Activity ids are campaign-plat. Handoff ZC-CK-3. Not invoice-row-dup.",
                outcome="Still campaign-grained; campaign key is marketing — handoff ZC-CK-3.",
                domain="zoho-campaigns-campaignkey-vs-activity",
                stack="Zoho Campaigns webhooks",
                seed="zoho-campaigns-handoff",
                residual="campaignkey is not an open. Not GetResponse clone.",
                ticket="ZC-CK-3",
                ticket_why="Zoho Campaigns activity owned by campaign-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="smtpcom-id-plus-event",
                goal="Dedupe SMTP.com webhooks on (message_id, event), not rcpt.",
                plan="Read rcpt-as-pk, try message_id-only, then (message_id, event).",
                mod="smtp_ev",
                test_fn="test_msgid_plus_event",
                src_body=(
                    "def upsert(ev):\n"
                    "    return ev['rcpt']\n"
                ),
                test_body=(
                    "def test_msgid_plus_event():\n"
                    "    a = {'message_id': 'm', 'event': 'delivered', 'rcpt': 'a@b'}\n"
                    "    b = {'message_id': 'm', 'event': 'opened', 'rcpt': 'a@b'}\n"
                    "    assert upsert(a) != upsert(b)\n"
                ),
                grep_pat="message_id|event|rcpt",
                grep_hit="src/smtp_ev.py:2: return ev['rcpt']",
                fail_msg="AssertionError: delivered+opened collapsed on rcpt",
                first_old="    return ev['rcpt']",
                first_new="    return ev['message_id']",
                first_obs="patched message_id (collides across events)",
                still_msg="AssertionError: same message_id delivered+opened still one row",
                reread_obs="SMTP.com message_id is the send; event is the activity",
                plan_change="PK (message_id, event). rcpt is the recipient.",
                fix_new="    return (ev['message_id'], ev['event'])",
                fix_obs="patched (message_id, event)",
                docs_url="https://www.smtp.com/resources/api-documentation/",
                docs_ok="Event webhooks include message_id and event type per activity.",
                docs_url2="https://www.smtp.com/resources/webhooks/",
                docs_ok2="opened after delivered must not overwrite the deliver row.",
                outcome="(message_id, event) kept both rows. rcpt unused (success).",
                domain="smtpcom-message-id-plus-event",
                stack="SMTP.com webhooks",
                seed="smtpcom-id-plus-event",
                residual="Not invoice-row-dup. Not Infobip clone.",
                coverage=84,
            ),
            _p(
                slug="civicrm-mailing-handoff",
                goal="Do not treat CiviCRM mailing_id as a unique email event.",
                plan="Read mailing-as-event, try mailing+contact, then hand off event id.",
                mod="civi_ml",
                test_fn="test_mailing_not_event",
                src_body=(
                    "def pk(ev):\n"
                    "    return ev['mailing_id']\n"
                ),
                test_body=(
                    "def test_mailing_not_event():\n"
                    "    assert pk({'mailing_id': '9', 'event_id': 'e1'}) != '9'\n"
                ),
                grep_pat="mailing_id|event_id|civicrm",
                grep_hit="src/civi_ml.py:2: return ev['mailing_id']",
                fail_msg="AssertionError: mailing_id collapsed 400 opens into one row",
                first_old="    return ev['mailing_id']",
                first_new="    return ev['mailing_id'] + ev.get('contact_id', '')",
                first_obs="patched mailing+contact (still campaign grain, not event)",
                still_msg="AssertionError: mailing+contact still one row per recipient per campaign",
                reread_obs="civicrm_mailing.id is the campaign; civicrm_mailing_event_* is activity",
                plan_change="mailing_id is campaign grain. Handoff CIVI-ML-2.",
                fix_new="    return {'handoff': 'CIVI-ML-2'}",
                fix_obs="ticket filed. still mailing-grained",
                docs_url="https://docs.civicrm.org/dev/en/latest/hooks/hook_civicrm_alterMailParams/",
                docs_ok="mailing_id identifies the mailing; events need event id.",
                docs_url2="https://docs.civicrm.org/user/en/latest/email/what-you-need-to-know/",
                docs_ok2="Campaign grain is marketing-plat. Handoff CIVI-ML-2. Not invoice-row-dup.",
                outcome="Still mailing-grained; campaign id is marketing — handoff CIVI-ML-2.",
                domain="civicrm-mailing-id-vs-event-id",
                stack="CiviCRM mailing events",
                seed="civicrm-mailing-handoff",
                residual="mailing_id is not an event pk. Not Mautic clone.",
                ticket="CIVI-ML-2",
                ticket_why="civicrm_mailing_event owned by marketing-plat",
                coverage=84,
            ),
        ),
    ],
    "feature-flag-debug-factory": [
        (
            _p(
                slug="rollout-gem-user-vs-ip",
                goal="Evaluate the rollout gem for user id, not request IP.",
                plan="Read IP-as-actor, try session, then user id.",
                mod="ro_usr",
                test_fn="test_user_not_ip",
                src_body=(
                    "def actor(req):\n"
                    "    return req['ip']\n"
                ),
                test_body=(
                    "def test_user_not_ip():\n"
                    "    assert actor({'ip': '1.1.1.1', 'user_id': 9}) == 9\n"
                ),
                grep_pat="user_id|request.ip|rollout",
                grep_hit="src/ro_usr.py:2: return req['ip']",
                fail_msg="AssertionError: '1.1.1.1' == 9; invoice flag defined for User",
                first_old="    return req['ip']",
                first_new="    return req.get('session_id') or req['ip']",
                first_obs="patched session (still not the user id)",
                still_msg="AssertionError: session id is not $rollout.active?(:invoice, user)",
                reread_obs="rollout gem InvoiceBeta is activated for User, not Request",
                plan_change="Use user id matching activate_user. IP is not the actor.",
                fix_new="    return req['user_id']",
                fix_obs="patched user_id actor",
                docs_url="https://github.com/fetlife/rollout#usage",
                docs_ok="rollout.active?(:flag, user) uses the user id, not the IP.",
                docs_url2="https://github.com/fetlife/rollout#groups",
                docs_ok2="User is the actor. Not Statsig user vs company. Not Pennant clone.",
                outcome="User id matched InvoiceBeta. IP unused (success).",
                domain="rollout-gem-user-id-vs-request-ip",
                stack="Ruby rollout gem",
                seed="rollout-gem-user-vs-ip",
                residual="Not Statsig customIDs.company. Not Pennant clone.",
                coverage=85,
            ),
            _p(
                slug="convert-experiment-handoff",
                goal="Do not treat a Convert.com experiment as a boolean feature flag.",
                plan="Read experiment-as-flag, try cookie, then hand off experiment.",
                mod="cv_exp",
                test_fn="test_experiment_not_flag",
                src_body=(
                    "def why_on(ctx):\n"
                    "    return 'flag' if ctx.get('experiment_id') else 'off'\n"
                ),
                test_body=(
                    "def test_experiment_not_flag():\n"
                    "    assert why_on({'experiment_id': 'e1'}) != 'flag'\n"
                ),
                grep_pat="experiment_id|Convert|flag",
                grep_hit="src/cv_exp.py:2: return 'flag' if ctx.get('experiment_id') else 'off'",
                fail_msg="AssertionError: Convert experiment labeled feature flag; ops looked at flags",
                first_old="    return 'flag' if ctx.get('experiment_id') else 'off'",
                first_new="    return 'flag_cookie' if ctx.get('experiment_id') else 'off'",
                first_obs="patched cookie (still flag-classed)",
                still_msg="AssertionError: experiment allocation is not a boolean flag",
                reread_obs="Convert.com experiment is A/B; feature flags live elsewhere",
                plan_change="Experiment allocation is experiment-plat. Handoff CV-EXP-2.",
                fix_new="    return 'handoff_CV-EXP-2' if ctx.get('experiment_id') else 'off'",
                fix_obs="ticket filed. still flag-classed",
                docs_url="https://www.convert.com/support/",
                docs_ok="Convert experiments allocate variations; they are not boolean flags.",
                docs_url2="https://www.convert.com/product/ab-testing/",
                docs_ok2="Experiment unit is experiment-plat. Handoff CV-EXP-2. Not Statsig. Not AB Tasty clone.",
                outcome="Still flag-classed; experiment is Convert — handoff CV-EXP-2.",
                domain="convert-experiment-vs-boolean-flag",
                stack="Convert.com experiments",
                seed="convert-experiment-handoff",
                residual="Not Statsig user vs company.",
                ticket="CV-EXP-2",
                ticket_why="experiment allocation owned by experiment-plat",
                coverage=85,
            ),
        ),
        (
            _p(
                slug="featurevisor-segment-vs-pct",
                goal="Honor Featurevisor segments before the percentage rollout.",
                plan="Read pct-first, try salt, then segment then percentage.",
                mod="fv_seg",
                test_fn="test_segment_before_pct",
                src_body=(
                    "def eval_flag(ctx):\n"
                    "    return hash(ctx['key']) % 100 < ctx['pct']\n"
                ),
                test_body=(
                    "def test_segment_before_pct():\n"
                    "    ctx = {'key': 'inv-1', 'pct': 0, 'segments': ['pro'], 'plan': 'pro'}\n"
                    "    assert eval_flag(ctx) is True\n"
                ),
                grep_pat="segments|pct|hash\\(ctx",
                grep_hit="src/fv_seg.py:2: return hash(ctx['key']) % 100 < ctx['pct']",
                fail_msg="AssertionError: pro plan hashed into 0% and missed segment",
                first_old="    return hash(ctx['key']) % 100 < ctx['pct']",
                first_new="    return hash(ctx['key'] + ctx.get('salt', '')) % 100 < ctx['pct']",
                first_obs="patched salt (still percentage-first, segment skipped)",
                still_msg="AssertionError: salt still ignores plan=pro segment",
                reread_obs="Featurevisor evaluates segments first; percentage is the fallthrough",
                plan_change="Match segments before percentage. Salt does not replace segments.",
                fix_new=(
                    "    if ctx.get('plan') in ctx.get('segments', []):\n"
                    "        return True\n"
                    "    return hash(ctx['key']) % 100 < ctx['pct']"
                ),
                fix_obs="patched segment-then-pct",
                docs_url="https://featurevisor.com/docs/segments/",
                docs_ok="Segments run before the default percentage rollout.",
                docs_url2="https://featurevisor.com/docs/features/",
                docs_ok2="0% default still serves segmented users. Not Statsig company. Not FeatBit clone.",
                outcome="plan=pro served via segment at 0%. Salt unused (success).",
                domain="featurevisor-segment-before-percentage",
                stack="Featurevisor segments",
                seed="featurevisor-segment-vs-pct",
                residual="Not Statsig user vs company. Not FeatBit clone.",
                coverage=83,
            ),
            _p(
                slug="sitespect-campaign-handoff",
                goal="Do not treat a SiteSpect campaign as a boolean feature flag.",
                plan="Read campaign-as-flag, try cookie, then hand off campaign.",
                mod="ss_camp",
                test_fn="test_campaign_not_flag",
                src_body=(
                    "def why_on(ctx):\n"
                    "    return 'flag' if ctx.get('campaign_id') else 'off'\n"
                ),
                test_body=(
                    "def test_campaign_not_flag():\n"
                    "    assert why_on({'campaign_id': 'c1'}) != 'flag'\n"
                ),
                grep_pat="campaign_id|SiteSpect|flag",
                grep_hit="src/ss_camp.py:2: return 'flag' if ctx.get('campaign_id') else 'off'",
                fail_msg="AssertionError: SiteSpect campaign labeled feature flag; ops looked at flags",
                first_old="    return 'flag' if ctx.get('campaign_id') else 'off'",
                first_new="    return 'flag_cookie' if ctx.get('campaign_id') else 'off'",
                first_obs="patched cookie (still flag-classed)",
                still_msg="AssertionError: campaign allocation is not a boolean flag",
                reread_obs="SiteSpect campaign is an experiment; feature flags live elsewhere",
                plan_change="Campaign allocation is experiment-plat. Handoff SS-CAMP-4.",
                fix_new="    return 'handoff_SS-CAMP-4' if ctx.get('campaign_id') else 'off'",
                fix_obs="ticket filed. still flag-classed",
                docs_url="https://docs.sitespect.com/",
                docs_ok="SiteSpect campaigns allocate variations; they are not boolean flags.",
                docs_url2="https://www.sitespect.com/platform/ab-testing/",
                docs_ok2="Campaign unit is experiment-plat. Handoff SS-CAMP-4. Not Statsig. Not AB Tasty clone.",
                outcome="Still flag-classed; campaign is SiteSpect — handoff SS-CAMP-4.",
                domain="sitespect-campaign-vs-boolean-flag",
                stack="SiteSpect campaigns",
                seed="sitespect-campaign-handoff",
                residual="Not Statsig user vs company.",
                ticket="SS-CAMP-4",
                ticket_why="campaign allocation owned by experiment-plat",
                coverage=83,
            ),
        ),
    ],
    "search-index-rebuild-factory": [
        (
            _p(
                slug="crate-fts-analyzer-vs-drop",
                goal="Alter CrateDB fulltext analyzer in place; do not DROP TABLE to rebuild.",
                plan="Read drop-as-rebuild, try TRUNCATE, then ALTER analyzer.",
                mod="cr_fts",
                test_fn="test_analyzer_not_drop",
                src_body=(
                    "def rebuild():\n"
                    "    return 'DROP TABLE invoices'\n"
                ),
                test_body=(
                    "def test_analyzer_not_drop():\n"
                    "    sql = rebuild()\n"
                    "    assert 'analyzer' in sql and 'DROP' not in sql\n"
                ),
                grep_pat="DROP TABLE|analyzer|TRUNCATE",
                grep_hit="src/cr_fts.py:2: return 'DROP TABLE invoices'",
                fail_msg="AssertionError: DROP TABLE lost invoices; analyzer never changed",
                first_old="    return 'DROP TABLE invoices'",
                first_new="    return 'TRUNCATE TABLE invoices'",
                first_obs="patched TRUNCATE (banned rebuild)",
                still_msg="AssertionError: TRUNCATE is not an analyzer change; data gone",
                reread_obs="CREATE ANALYZER invoice_stem; ALTER TABLE INDEX using fulltext",
                plan_change="ALTER analyzer in place. Do not DROP/TRUNCATE.",
                fix_new="    return \"ALTER TABLE invoices INDEX body USING FULLTEXT WITH (analyzer='invoice_stem')\"",
                fix_obs="patched analyzer alter",
                docs_url="https://cratedb.com/docs/crate/reference/en/latest/general/ddl/fulltext-indices.html",
                docs_ok="Fulltext analyzers can be applied without dropping the table.",
                docs_url2="https://cratedb.com/docs/crate/reference/en/latest/general/ddl/create-table.html",
                docs_ok2="Not TRUNCATE-then-reindex. Left sir-r26 placeholder. Not RUM/Whoosh clones.",
                outcome="Analyzer alter ranked invoices. DROP unused (success).",
                domain="cratedb-fulltext-analyzer-vs-drop-table",
                stack="CrateDB fulltext analyzer",
                seed="crate-fts-analyzer-vs-drop",
                residual="Not TRUNCATE-then-reindex. Left sir-r26 placeholder in raw.",
                coverage=87,
            ),
            _p(
                slug="marklogic-fields-handoff",
                goal="Do not search MarkLogic before field indexes are reindexed.",
                plan="Read schema-as-live, try sleep, then hand off field reindex.",
                mod="ml_fld",
                test_fn="test_fields_not_live",
                src_body=(
                    "def ready(db):\n"
                    "    return True\n"
                ),
                test_body=(
                    "def test_fields_not_live():\n"
                    "    assert ready('ocr') is not True\n"
                ),
                grep_pat="field-index|reindex|MarkLogic",
                grep_hit="src/ml_fld.py:2: return True",
                fail_msg="AssertionError: search empty; sku field index never reindexed",
                first_old="    return True",
                first_new="    return 'slept'",
                first_obs="patched sleep (still no field reindex)",
                still_msg="AssertionError: sleep cannot reindex MarkLogic field indexes",
                reread_obs="MarkLogic field index sku is reindexing until complete",
                plan_change="Field reindex is ml-plat. Handoff ML-FLD-3. Not TRUNCATE.",
                fix_new="    return {'handoff': 'ML-FLD-3'}",
                fix_obs="ticket filed. still unreindexed",
                docs_url="https://docs.marklogic.com/guide/admin/fields",
                docs_ok="Field indexes must finish reindexing before queries see them.",
                docs_url2="https://docs.marklogic.com/guide/admin/text_index",
                docs_ok2="Reindex is ml-plat. Handoff ML-FLD-3. Not TRUNCATE. Left sir-r26.",
                outcome="Still unreindexed; field indexes are ml-plat — handoff ML-FLD-3.",
                domain="marklogic-field-index-reindex-vs-search",
                stack="MarkLogic field indexes",
                seed="marklogic-fields-handoff",
                residual="Not TRUNCATE-then-reindex. Not CloudSearch clone.",
                ticket="ML-FLD-3",
                ticket_why="field reindex owned by ml-plat",
                coverage=87,
            ),
        ),
        (
            _p(
                slug="zombodb-refresh-vs-truncate",
                goal="REFRESH ZomboDB in place; do not TRUNCATE the heap to rebuild.",
                plan="Read truncate-as-refresh, try DROP INDEX, then zdb.request refresh.",
                mod="zdb_rf",
                test_fn="test_refresh_not_truncate",
                src_body=(
                    "def rebuild():\n"
                    "    return 'TRUNCATE invoices'\n"
                ),
                test_body=(
                    "def test_refresh_not_truncate():\n"
                    "    sql = rebuild()\n"
                    "    assert 'refresh' in sql.lower() and 'TRUNCATE' not in sql\n"
                ),
                grep_pat="TRUNCATE|zdb.request|refresh",
                grep_hit="src/zdb_rf.py:2: return 'TRUNCATE invoices'",
                fail_msg="AssertionError: TRUNCATE lost heap; ZomboDB index never refreshed",
                first_old="    return 'TRUNCATE invoices'",
                first_new="    return 'DROP INDEX invoices_zdb'",
                first_obs="patched DROP INDEX (still a rebuild wipe)",
                still_msg="AssertionError: DROP INDEX is not a refresh; mapping gone",
                reread_obs="SELECT zdb.request('invoices', '_refresh') updates ES without TRUNCATE",
                plan_change="zdb.request _refresh. Do not TRUNCATE or DROP INDEX.",
                fix_new="    return \"SELECT zdb.request('invoices', '_refresh')\"",
                fix_obs="patched zdb refresh",
                docs_url="https://github.com/zombodb/zombodb/blob/master/TUTORIAL.md",
                docs_ok="ZomboDB follows the heap; refresh the ES index, do not TRUNCATE.",
                docs_url2="https://docs.zombodb.com/",
                docs_ok2="Not TRUNCATE-then-reindex. Left sir-r26 placeholder.",
                outcome="zdb refresh updated ES. TRUNCATE unused (success).",
                domain="zombodb-refresh-vs-truncate-heap",
                stack="ZomboDB _refresh",
                seed="zombodb-refresh-vs-truncate",
                residual="Not TRUNCATE-then-reindex. Left sir-r26 placeholder in raw.",
                coverage=85,
            ),
            _p(
                slug="coveo-source-handoff",
                goal="Do not query Coveo before the source rebuild is pushed.",
                plan="Read source-as-live, try sleep, then hand off source push.",
                mod="cv_src",
                test_fn="test_source_not_live",
                src_body=(
                    "def ready(src):\n"
                    "    return True\n"
                ),
                test_body=(
                    "def test_source_not_live():\n"
                    "    assert ready('ocr') is not True\n"
                ),
                grep_pat="source|rebuild|Coveo",
                grep_hit="src/cv_src.py:2: return True",
                fail_msg="AssertionError: search empty; source rebuild never pushed",
                first_old="    return True",
                first_new="    return 'slept'",
                first_obs="patched sleep (still no source push)",
                still_msg="AssertionError: sleep cannot push a Coveo source rebuild",
                reread_obs="Coveo source ocr is REBUILD pending until push",
                plan_change="Source push is coveo-plat. Handoff CV-SRC-2. Not TRUNCATE.",
                fix_new="    return {'handoff': 'CV-SRC-2'}",
                fix_obs="ticket filed. still unpushed",
                docs_url="https://docs.coveo.com/en/56/index-content/rebuild-a-source",
                docs_ok="Source rebuild must complete before queries see documents.",
                docs_url2="https://docs.coveo.com/en/55/index-content/manage-sources",
                docs_ok2="Push is coveo-plat. Handoff CV-SRC-2. Not TRUNCATE. Left sir-r26.",
                outcome="Still unpushed; source rebuild is coveo-plat — handoff CV-SRC-2.",
                domain="coveo-source-rebuild-vs-query",
                stack="Coveo sources",
                seed="coveo-source-handoff",
                residual="Not TRUNCATE-then-reindex.",
                ticket="CV-SRC-2",
                ticket_why="source rebuild owned by coveo-plat",
                coverage=85,
            ),
        ),
    ],
    "log-redaction-factory": [
        (
            _p(
                slug="journald-template-iban",
                goal="Install a journald template that redacts iban; do not drop the unit.",
                plan="Read drop-as-redact, try ForwardToDisk no, then template redact.",
                mod="jd_iban",
                test_fn="test_template_not_drop",
                src_body=(
                    "def configure():\n"
                    "    return {'drop': True}\n"
                ),
                test_body=(
                    "def test_template_not_drop():\n"
                    "    c = configure()\n"
                    "    assert c.get('redact') == ('iban',) and not c.get('drop')\n"
                ),
                grep_pat="iban|journald|drop",
                grep_hit="src/jd_iban.py:2: return {'drop': True}",
                fail_msg="AssertionError: drop swallowed SYSLOG_IDENTIFIER; iban still in MESSAGE",
                first_old="    return {'drop': True}",
                first_new="    return {'ForwardToDisk': 'no'}",
                first_obs="patched ForwardToDisk no (still drop, still not template)",
                still_msg="AssertionError: ForwardToDisk no drops keep-fields; need template redact",
                reread_obs="journald Tmpl can mask iban and keep SYSLOG_IDENTIFIER",
                plan_change="Template redacts iban. Do not drop the unit.",
                fix_new="    return {'redact': ('iban',), 'drop': False}",
                fix_obs="patched template redact",
                docs_url="https://www.freedesktop.org/software/systemd/man/latest/journald.conf.html",
                docs_ok="journald templates rewrite MESSAGE; dropping the unit loses identifier.",
                docs_url2="https://www.freedesktop.org/software/systemd/man/latest/systemd.journal-fields.html",
                docs_ok2="Keep SYSLOG_IDENTIFIER. Not python-json-logger. Not structlog clone.",
                outcome="Template redacted iban. Drop unused (success).",
                domain="journald-template-iban-vs-drop-unit",
                stack="systemd journald templates",
                seed="journald-template-iban",
                residual="Not nxlog rewrite clone.",
                coverage=84,
            ),
            _p(
                slug="mezmo-parse-handoff",
                goal="Do not mute stdout to hide a Mezmo parse that still stores pan.",
                plan="Read mute-as-redact, try drop pipeline, then hand off parse.",
                mod="mz_parse",
                test_fn="test_mute_not_parse",
                src_body=(
                    "def configure():\n"
                    "    return {'mute_stdout': True}\n"
                ),
                test_body=(
                    "def test_mute_not_parse():\n"
                    "    assert 'mute_stdout' not in configure()\n"
                ),
                grep_pat="mezmo|parse|pan",
                grep_hit="src/mz_parse.py:2: return {'mute_stdout': True}",
                fail_msg="AssertionError: mute dropped method; Mezmo still stores pan",
                first_old="    return {'mute_stdout': True}",
                first_new="    return {'drop_pipeline': True}",
                first_obs="patched drop pipeline (still mute-classed)",
                still_msg="AssertionError: drop pipeline still loses method; parse lives in Mezmo",
                reread_obs="Mezmo parsing stores pan server-side; app mute is not redact",
                plan_change="Parse pipeline is mezmo-plat. Handoff MZ-PARSE-3.",
                fix_new="    return {'handoff': 'MZ-PARSE-3'}",
                fix_obs="ticket filed. still mute-classed",
                docs_url="https://docs.mezmo.com/docs/parsing",
                docs_ok="Parsing pipelines run in Mezmo; app mute cannot rewrite stored pan.",
                docs_url2="https://docs.mezmo.com/docs/pipelines",
                docs_ok2="Server-side redact is obs-plat. Handoff MZ-PARSE-3. Not json-logger. Not Coralogix clone.",
                outcome="Still mute-classed; parse is Mezmo — handoff MZ-PARSE-3.",
                domain="mezmo-parse-pipeline-vs-stdout-mute",
                stack="Mezmo parsing",
                seed="mezmo-parse-handoff",
                residual="Mute is not redaction.",
                ticket="MZ-PARSE-3",
                ticket_why="Mezmo parse owned by obs-plat",
                coverage=84,
            ),
        ),
        (
            _p(
                slug="logbook-processor-cvv",
                goal="Install a Logbook processor that redacts cvv; do not disable the logger.",
                plan="Read disable-as-redact, try level=0, then processor redact.",
                mod="lb_cvv",
                test_fn="test_processor_not_disable",
                src_body=(
                    "def configure():\n"
                    "    return {'disabled': True}\n"
                ),
                test_body=(
                    "def test_processor_not_disable():\n"
                    "    c = configure()\n"
                    "    assert c.get('redact') == ('cvv',) and not c.get('disabled')\n"
                ),
                grep_pat="cvv|logbook|disabled",
                grep_hit="src/lb_cvv.py:2: return {'disabled': True}",
                fail_msg="AssertionError: disable swallowed order_id; cvv still in extra",
                first_old="    return {'disabled': True}",
                first_new="    return {'level': 0}",
                first_obs="patched level 0 (still disable, still not processor)",
                still_msg="AssertionError: level 0 drops keep-fields; need processor redact",
                reread_obs="Logbook processors can pop cvv and keep order_id",
                plan_change="Processor redacts cvv. Do not disable the logger.",
                fix_new="    return {'redact': ('cvv',), 'disabled': False}",
                fix_obs="patched processor redact",
                docs_url="https://logbook.readthedocs.io/en/stable/api/processors.html",
                docs_ok="Processors rewrite extra; disabling the logger loses order_id.",
                docs_url2="https://logbook.readthedocs.io/en/stable/",
                docs_ok2="Keep order_id. Not python-json-logger. Not structlog clone.",
                outcome="Processor redacted cvv. Disable unused (success).",
                domain="logbook-processor-cvv-vs-disable",
                stack="Logbook processors",
                seed="logbook-processor-cvv",
                residual="Not log4net clone.",
                coverage=83,
            ),
            _p(
                slug="loggly-token-handoff",
                goal="Do not unset the Loggly token to hide events that still store pan.",
                plan="Read unset-as-redact, try mute, then hand off token filter.",
                mod="lg_tok",
                test_fn="test_unset_not_redact",
                src_body=(
                    "def configure():\n"
                    "    return {'token': None}\n"
                ),
                test_body=(
                    "def test_unset_not_redact():\n"
                    "    assert configure().get('token') is not None\n"
                ),
                grep_pat="LOGGLY|token|pan",
                grep_hit="src/lg_tok.py:2: return {'token': None}",
                fail_msg="AssertionError: unset token dropped operation; Loggly still stores pan",
                first_old="    return {'token': None}",
                first_new="    return {'mute': True}",
                first_obs="patched mute (still drop, still not filter)",
                still_msg="AssertionError: mute drops operation; pan stays server-side",
                reread_obs="Loggly derived fields store pan; unsetting the token is not redact",
                plan_change="Derived-field filter is loggly-plat. Handoff LG-TOK-2.",
                fix_new="    return {'handoff': 'LG-TOK-2'}",
                fix_obs="ticket filed. still mute-classed",
                docs_url="https://documentation.solarwinds.com/en/success_center/loggly/content/admin/derived-fields.htm",
                docs_ok="Loggly derived fields redact pan; unsetting the token drops the event.",
                docs_url2="https://documentation.solarwinds.com/en/success_center/loggly/",
                docs_ok2="Server-side filter is obs-plat. Handoff LG-TOK-2. Not json-logger. Not Rollbar clone.",
                outcome="Still mute-classed; derived fields are Loggly — handoff LG-TOK-2.",
                domain="loggly-derived-field-vs-token-unset",
                stack="Loggly derived fields",
                seed="loggly-token-handoff",
                residual="Unset token is not redaction.",
                ticket="LG-TOK-2",
                ticket_why="Loggly derived fields owned by obs-plat",
                coverage=83,
            ),
        ),
    ],
}
