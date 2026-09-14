"""Unique Q=2 plants for idle hopper factories (post g46). Do not clone BAN lists."""

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
    "rate-limit-backoff-factory": 56,
    "queue-backpressure-factory": 35,
    "csv-excel-ingest-factory": 35,
    "websocket-reconnect-factory": 35,
    "email-webhook-retry-factory": 34,
    "feature-flag-debug-factory": 35,
    "search-index-rebuild-factory": 31,
    "log-redaction-factory": 46,
}

CYCLE = [
    "rate-limit-backoff-factory",
    "queue-backpressure-factory",
    "csv-excel-ingest-factory",
    "websocket-reconnect-factory",
    "email-webhook-retry-factory",
    "feature-flag-debug-factory",
    "search-index-rebuild-factory",
    "log-redaction-factory",
]


def _p(**kwargs):
    return kwargs


PAIRS = {
    "rate-limit-backoff-factory": [
        (
            _p(
                slug="coda-doc-vs-account-rate",
                goal="Honor Coda per-document X-RateLimit-Remaining, not the account bucket.",
                plan="Read doc-as-account, try sleep-account, then key remaining on doc id.",
                mod="coda_doc",
                test_fn="test_doc_not_account",
                src_body=(
                    "def bucket(h):\n"
                    "    return 'account' if h.get('X-Coda-Doc-Id') else 'ok'\n"
                ),
                test_body=(
                    "def test_doc_not_account():\n"
                    "    assert bucket({'X-Coda-Doc-Id': 'd1', 'X-RateLimit-Remaining': '2'}) == 'doc'\n"
                ),
                grep_pat="X-Coda-Doc-Id|account|X-RateLimit-Remaining",
                grep_hit="src/coda_doc.py:2: return 'account' if h.get('X-Coda-Doc-Id') else 'ok'",
                fail_msg="AssertionError: doc 429 slept the account bucket and stalled other docs",
                first_old="    return 'account' if h.get('X-Coda-Doc-Id') else 'ok'",
                first_new="    return 'account_share' if h.get('X-Coda-Doc-Id') else 'ok'",
                first_obs="patched account_share (still one bucket for all docs)",
                still_msg="AssertionError: per-doc remaining must not drain the account budget",
                reread_obs="Coda REST rate is per doc id; account rate is a second counter",
                plan_change="Key sleep on doc_id remaining. Do not debit the account bucket for a doc 429.",
                fix_new="    return 'doc' if h.get('X-Coda-Doc-Id') else 'ok'",
                fix_obs="patched doc-scoped remaining",
                docs_url="https://coda.io/developers/apis/v1#section/Rate-limiting",
                docs_ok="Coda REST has per-document and per-account limits as separate counters.",
                docs_url2="https://coda.io/developers/apis/v1#tag/Docs",
                docs_ok2="A doc 429 must not pause GET /docs on a different id. Not Retry-After catalog.",
                outcome="Doc-scoped remaining unblocked other docs. Account unused (success).",
                domain="coda-rest-doc-rate-vs-account-rate",
                stack="Coda REST rate limits",
                seed="coda-doc-vs-account-rate",
                residual="Account budget is a second counter. Not GitLab Observed/HubSpot/Figma/Zoom.",
                coverage=86,
            ),
            _p(
                slug="notion-workspace-plan-handoff",
                goal="Do not retry Notion 429 rate_limited as a sleepable per-call rate.",
                plan="Read plan-as-sleep, try 60s, then hand off workspace plan.",
                mod="nt_plan",
                test_fn="test_plan_not_sleep",
                src_body=(
                    "def classify(body):\n"
                    "    return 'sleep_2s' if 'rate_limited' in body else 'ok'\n"
                ),
                test_body=(
                    "def test_plan_not_sleep():\n"
                    "    assert classify('rate_limited workspace') != 'sleep_2s'\n"
                ),
                grep_pat="rate_limited|workspace|sleep",
                grep_hit="src/nt_plan.py:2: return 'sleep_2s' if 'rate_limited' in body else 'ok'",
                fail_msg="AssertionError: workspace plan 429 slept 2s; plan is billing",
                first_old="    return 'sleep_2s' if 'rate_limited' in body else 'ok'",
                first_new="    return 'sleep_60s' if 'rate_limited' in body else 'ok'",
                first_obs="patched 60s (still treating plan cap as per-call rate)",
                still_msg="AssertionError: sleep cannot mint a Notion Plus workspace plan",
                reread_obs="429 rate_limited on /v1/pages is workspace plan, not request rate",
                plan_change="Workspace plan cap is billing. Handoff NT-PLAN-6.",
                fix_new="    return 'handoff_NT-PLAN-6' if 'workspace' in body else 'ok'",
                fix_obs="ticket filed. still rate-classed until billing",
                docs_url="https://developers.notion.com/reference/request-limits",
                docs_ok="Notion 429 rate_limited can be the workspace plan, not the 3 rps average.",
                docs_url2="https://developers.notion.com/docs/working-with-page-content",
                docs_ok2="Sleep cannot change workspace plan. Handoff NT-PLAN-6. Not Retry-After catalog.",
                outcome="Still rate-classed; workspace plan is billing — handoff NT-PLAN-6.",
                domain="notion-workspace-plan-cap-vs-sleep",
                stack="Notion REST pages",
                seed="notion-workspace-plan-handoff",
                residual="Sleep cannot mint a workspace plan.",
                ticket="NT-PLAN-6",
                ticket_why="workspace plan 429 owned by billing-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="clickup-team-vs-personal-rate",
                goal="Honor ClickUp team X-RateLimit, not the personal token bucket as the stall.",
                plan="Read team-as-personal, try sleep-token, then team remaining.",
                mod="clk_team",
                test_fn="test_team_not_personal",
                src_body=(
                    "def bucket(h):\n"
                    "    return 'personal' if h.get('X-RateLimit-Scope') == 'team' else 'ok'\n"
                ),
                test_body=(
                    "def test_team_not_personal():\n"
                    "    assert bucket({'X-RateLimit-Scope': 'team'}) == 'team'\n"
                ),
                grep_pat="X-RateLimit-Scope|personal|team",
                grep_hit="src/clk_team.py:2: return 'personal' if h.get('X-RateLimit-Scope') == 'team'",
                fail_msg="AssertionError: team 429 slept the personal token and stalled other teams",
                first_old="    return 'personal' if h.get('X-RateLimit-Scope') == 'team' else 'ok'",
                first_new="    return 'personal_share' if h.get('X-RateLimit-Scope') == 'team' else 'ok'",
                first_obs="patched personal_share (still one token bucket)",
                still_msg="AssertionError: team-scoped 429 must not drain the personal token",
                reread_obs="ClickUp team rate is per team_id; personal token rate is a second counter",
                plan_change="Key sleep on team remaining. Do not debit the personal token for a team 429.",
                fix_new="    return 'team' if h.get('X-RateLimit-Scope') == 'team' else 'ok'",
                fix_obs="patched team-scoped remaining",
                docs_url="https://clickup.com/api/developer-portal/rate-limits/",
                docs_ok="ClickUp has team-level and personal-token limits as separate counters.",
                docs_url2="https://clickup.com/api/clickupreference/operation/GetAuthorizedTeams/",
                docs_ok2="A team 429 must not pause GET /team on a different team. Not Retry-After catalog.",
                outcome="Team-scoped remaining unblocked other teams. Personal unused (success).",
                domain="clickup-team-rate-vs-personal-token",
                stack="ClickUp REST rate limits",
                seed="clickup-team-vs-personal-rate",
                residual="Personal token is a second counter. Not Figma/Zoom clones.",
                coverage=85,
            ),
            _p(
                slug="asana-daily-task-create-handoff",
                goal="Do not retry Asana POST /tasks 429 as per-minute rate.",
                plan="Read create-as-rpm, try 60s, then hand off workspace daily cap.",
                mod="asana_dy",
                test_fn="test_create_not_rpm",
                src_body=(
                    "def classify(path, status):\n"
                    "    return 'rpm' if status == 429 else 'ok'\n"
                ),
                test_body=(
                    "def test_create_not_rpm():\n"
                    "    assert classify('/tasks', 429) != 'rpm'\n"
                ),
                grep_pat="/tasks|429|rpm",
                grep_hit="src/asana_dy.py:2: return 'rpm' if status == 429 else 'ok'",
                fail_msg="AssertionError: POST /tasks 429 retried as rpm; daily create cap",
                first_old="    return 'rpm' if status == 429 else 'ok'",
                first_new="    return 'rpm_60s' if status == 429 else 'ok'",
                first_obs="patched 60s (still rpm)",
                still_msg="AssertionError: daily task-create cap is not rpm; billing owns it",
                reread_obs="POST /tasks 429 Retry-After midnight is workspace daily create, not REST rpm",
                plan_change="Daily task create is a plan cap. Handoff ASANA-DAY-4.",
                fix_new="    return 'handoff_ASANA-DAY-4' if path == '/tasks' else 'ok'",
                fix_obs="ticket filed. still rpm-classed",
                docs_url="https://developers.asana.com/docs/rate-limits",
                docs_ok="Task create has a daily workspace cap separate from the per-minute REST window.",
                docs_url2="https://developers.asana.com/reference/createtask",
                docs_ok2="Sleep cannot mint daily creates. Handoff ASANA-DAY-4. Not Retry-After catalog.",
                outcome="Still rpm-classed; daily create is billing — handoff ASANA-DAY-4.",
                domain="asana-task-create-daily-cap-vs-rest-rpm",
                stack="Asana REST tasks",
                seed="asana-daily-task-create-handoff",
                residual="Sleep cannot mint daily task creates.",
                ticket="ASANA-DAY-4",
                ticket_why="POST /tasks 429 daily create owned by billing-plat",
                coverage=85,
            ),
        ),
    ],
    "queue-backpressure-factory": [
        (
            _p(
                slug="hatchet-slots-vs-timeout",
                goal="Raise Hatchet worker slots; do not stretch job timeout to hide OCR lag.",
                plan="Read timeout-as-slots, try 600s, then slots=8 plus ack-before-next.",
                mod="hat_slot",
                test_fn="test_slots_not_timeout",
                src_body=(
                    "def tune(lag):\n"
                    "    return {'job_timeout_s': 120} if lag else {}\n"
                ),
                test_body=(
                    "def test_slots_not_timeout():\n"
                    "    t = tune(True)\n"
                    "    assert t.get('slots') == 8 and 'job_timeout_s' not in t\n"
                ),
                grep_pat="job_timeout_s|slots|ack",
                grep_hit="src/hat_slot.py:2: return {'job_timeout_s': 120} if lag else {}",
                fail_msg="AssertionError: lag stretched job timeout; worker slots still 1",
                first_old="    return {'job_timeout_s': 120} if lag else {}",
                first_new="    return {'job_timeout_s': 600} if lag else {}",
                first_obs="patched 600s (still a timeout integer)",
                still_msg="AssertionError: timeout integer cannot mint worker slots",
                reread_obs="Hatchet WORKER_SLOTS=1; job timeout is not concurrency",
                plan_change="slots=8 and ack before next pull. Timeout is not credit.",
                fix_new="    return {'slots': 8, 'ack_before_next': True} if lag else {}",
                fix_obs="patched slots=8",
                docs_url="https://docs.hatchet.run/home/concurrency",
                docs_ok="Worker slots bound in-flight OCR jobs; timeout is a separate clock.",
                docs_url2="https://docs.hatchet.run/home/workers",
                docs_ok2="Ack current slot before the next lease. Timeout is not a slot.",
                outcome="Slots 8 plus ack drained lag. Timeout unused (success).",
                domain="hatchet-worker-slots-vs-job-timeout",
                stack="Hatchet worker slots",
                seed="hatchet-slots-vs-timeout",
                residual="Timeout integer is not broker credit. Not Cloud Tasks.",
                coverage=86,
            ),
            _p(
                slug="inngest-account-concurrency-handoff",
                goal="Do not raise Inngest step timeout to hide account concurrency.",
                plan="Read conc-as-timeout, try 300s, then hand off account concurrency.",
                mod="ing_conc",
                test_fn="test_conc_not_timeout",
                src_body=(
                    "def tune(blocked):\n"
                    "    return {'step_timeout_s': 60} if blocked else {}\n"
                ),
                test_body=(
                    "def test_conc_not_timeout():\n"
                    "    assert 'step_timeout_s' not in tune(True)\n"
                ),
                grep_pat="step_timeout_s|account_concurrency|inngest",
                grep_hit="src/ing_conc.py:2: return {'step_timeout_s': 60} if blocked else {}",
                fail_msg="AssertionError: account concurrency slept step timeout; plan is 5",
                first_old="    return {'step_timeout_s': 60} if blocked else {}",
                first_new="    return {'step_timeout_s': 300} if blocked else {}",
                first_obs="patched 300s (still a timeout integer)",
                still_msg="AssertionError: step timeout cannot mint account concurrency",
                reread_obs="Inngest account concurrency=5; OCR holds all five slots",
                plan_change="Account concurrency is plan. Handoff ING-CONC-3.",
                fix_new="    return {'handoff': 'ING-CONC-3'} if blocked else {}",
                fix_obs="ticket filed. still timeout-classed",
                docs_url="https://www.inngest.com/docs/guides/concurrency",
                docs_ok="Account concurrency is a plan limit, not a step timeout.",
                docs_url2="https://www.inngest.com/docs/features/inngest-functions/steps-workflows",
                docs_ok2="Sleep cannot mint plan slots. Handoff ING-CONC-3. Not Cloud Tasks.",
                outcome="Still timeout-classed; account concurrency is plan — handoff ING-CONC-3.",
                domain="inngest-account-concurrency-vs-step-timeout",
                stack="Inngest account concurrency",
                seed="inngest-account-concurrency-handoff",
                residual="Timeout cannot mint plan concurrency.",
                ticket="ING-CONC-3",
                ticket_why="account concurrency owned by inngest-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="dapr-outstanding-vs-ack-timeout",
                goal="Bound Dapr pubsub maxOutstandingMessages; do not raise ack timeout to hide lag.",
                plan="Read outstanding-as-timeout, try 120s, then outstanding=16 plus ack.",
                mod="dapr_out",
                test_fn="test_outstanding_not_ack",
                src_body=(
                    "def tune(lag):\n"
                    "    return {'ack_timeout_s': 30} if lag else {}\n"
                ),
                test_body=(
                    "def test_outstanding_not_ack():\n"
                    "    t = tune(True)\n"
                    "    assert t.get('maxOutstandingMessages') == 16 and 'ack_timeout_s' not in t\n"
                ),
                grep_pat="ack_timeout_s|maxOutstandingMessages|dapr",
                grep_hit="src/dapr_out.py:2: return {'ack_timeout_s': 30} if lag else {}",
                fail_msg="AssertionError: lag stretched ack timeout; outstanding still unbounded",
                first_old="    return {'ack_timeout_s': 30} if lag else {}",
                first_new="    return {'ack_timeout_s': 120} if lag else {}",
                first_obs="patched 120s (still a timeout integer)",
                still_msg="AssertionError: ack timeout cannot bound maxOutstandingMessages",
                reread_obs="Dapr pubsub maxOutstandingMessages default is unbounded on OCR",
                plan_change="maxOutstandingMessages=16 plus ack. Timeout is not a queue bound.",
                fix_new="    return {'maxOutstandingMessages': 16, 'ack': True} if lag else {}",
                fix_obs="patched outstanding=16",
                docs_url="https://docs.dapr.io/developing-applications/building-blocks/pubsub/howto-publish-subscribe/",
                docs_ok="maxOutstandingMessages bounds unacked messages; ack timeout is a clock.",
                docs_url2="https://docs.dapr.io/reference/components-reference/supported-pubsub/",
                docs_ok2="Use a finite outstanding window, not a longer ack clock. Not Cloud Tasks.",
                outcome="Outstanding 16 plus ack drained lag. Timeout unused (success).",
                domain="dapr-pubsub-outstanding-vs-ack-timeout",
                stack="Dapr pubsub",
                seed="dapr-outstanding-vs-ack-timeout",
                residual="Ack timeout is not a queue bound.",
                coverage=84,
            ),
            _p(
                slug="durable-replay-handoff",
                goal="Do not raise Azure Durable Functions idle timeout to hide replay history.",
                plan="Read replay-as-idle, try 30s, then hand off history replay.",
                mod="dur_rpl",
                test_fn="test_replay_not_idle",
                src_body=(
                    "def tune(stuck):\n"
                    "    return {'idle_timeout_s': 10} if stuck else {}\n"
                ),
                test_body=(
                    "def test_replay_not_idle():\n"
                    "    assert 'idle_timeout_s' not in tune(True)\n"
                ),
                grep_pat="idle_timeout_s|ReplaySafe|orchestration",
                grep_hit="src/dur_rpl.py:2: return {'idle_timeout_s': 10} if stuck else {}",
                fail_msg="AssertionError: replay stall slept idle timeout; history never trimmed",
                first_old="    return {'idle_timeout_s': 10} if stuck else {}",
                first_new="    return {'idle_timeout_s': 30} if stuck else {}",
                first_obs="patched 30s (still a timeout integer)",
                still_msg="AssertionError: idle timeout cannot trim Durable replay history",
                reread_obs="Orchestration replays full history; idle timeout is not ContinueAsNew",
                plan_change="Replay history is platform. Handoff DUR-RPL-2.",
                fix_new="    return {'handoff': 'DUR-RPL-2'} if stuck else {}",
                fix_obs="ticket filed. still idle-classed",
                docs_url="https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-orchestrations",
                docs_ok="Replay is deterministic history, not an idle timeout.",
                docs_url2="https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-eternal-orchestrations",
                docs_ok2="ContinueAsNew is platform. Handoff DUR-RPL-2. Not Cloud Tasks.",
                outcome="Still idle-classed; replay history is platform — handoff DUR-RPL-2.",
                domain="azure-durable-replay-vs-idle-timeout",
                stack="Azure Durable Functions",
                seed="durable-replay-handoff",
                residual="Idle timeout is not ContinueAsNew.",
                ticket="DUR-RPL-2",
                ticket_why="orchestration replay owned by functions-plat",
                coverage=84,
            ),
        ),
    ],
    "csv-excel-ingest-factory": [
        (
            _p(
                slug="xlsx-xlfn-xlookup-cached",
                goal="Read _xlfn.XLOOKUP cached <v>, not the formula text in <f>.",
                plan="Read formula-as-value, try t=str, then cached v on the XLOOKUP cell.",
                mod="xlfn_xl",
                test_fn="test_cached_v_not_formula",
                src_body=(
                    "def amount(cell):\n"
                    "    return cell.get('f')\n"
                ),
                test_body=(
                    "def test_cached_v_not_formula():\n"
                    "    cell = {'f': '_xlfn.XLOOKUP(A2,sku,amt)', 'v': '10.00'}\n"
                    "    assert amount(cell) == '10.00'\n"
                ),
                grep_pat="_xlfn.XLOOKUP|cell.get\\('f'\\)|cached",
                grep_hit="src/xlfn_xl.py:2: return cell.get('f')",
                fail_msg="AssertionError: '_xlfn.XLOOKUP(A2,sku,amt)' == '10.00'; cached v ignored",
                first_old="    return cell.get('f')",
                first_new="    return cell.get('t') or cell.get('f')",
                first_obs="patched t=str (still formula text, not cached v)",
                still_msg="AssertionError: t=str still misses the cached numeric v",
                reread_obs="Future function _xlfn.XLOOKUP stores the last calc in <v>",
                plan_change="Read cached <v>. Formula text is not the invoice amount.",
                fix_new="    return cell.get('v')",
                fix_obs="patched cached v",
                docs_url="https://learn.microsoft.com/en-us/office/client-developer/excel/excel-glossary#future-function",
                docs_ok="_xlfn. prefixes future functions; the cached value is in the v node.",
                docs_url2="https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/",
                docs_ok2="Do not ingest formula text as the amount. Not quoted-newline, not WPS .et.",
                outcome="Cached v ingested 10.00. Formula unused (success).",
                domain="xlsx-xlfn-xlookup-cached-v-vs-formula-text",
                stack="OOXML future function XLOOKUP",
                seed="xlsx-xlfn-xlookup-cached",
                residual="Not quoted-newline, not Kingsoft .et.",
                coverage=87,
            ),
            _p(
                slug="sas7bdat-binary-handoff",
                goal="Do not parse SAS7BDAT as CSV text.",
                plan="Read sas-as-csv, try latin1, then hand off binary reader.",
                mod="sas_bin",
                test_fn="test_sas_not_csv",
                src_body=(
                    "def load(path):\n"
                    "    return open(path, newline='').read().split(',')\n"
                ),
                test_body=(
                    "def test_sas_not_csv():\n"
                    "    assert load('invoices.sas7bdat') != open('invoices.sas7bdat').read().split(',')\n"
                ),
                grep_pat="sas7bdat|read\\(\\).*split|pyreadstat",
                grep_hit="src/sas_bin.py:2: return open(path, newline='').read().split(',')",
                fail_msg="AssertionError: SAS HEADER magic parsed as CSV; binary header lost",
                first_old="    return open(path, newline='').read().split(',')",
                first_new="    return open(path, encoding='latin1').read().split(',')",
                first_obs="patched latin1 (still text split, still not sas7bdat)",
                still_msg="AssertionError: latin1 cannot decode SAS7BDAT page header",
                reread_obs="SAS HEADER + PAGE needs pyreadstat.read_sas7bdat, not csv",
                plan_change="Binary .sas7bdat is stats-plat. Handoff SAS-BIN-5.",
                fix_new="    return {'handoff': 'SAS-BIN-5'}",
                fix_obs="ticket filed. still csv-split",
                docs_url="https://support.sas.com/documentation/cdl/en/movefile/59598/HTML/default/viewer.htm#a001002110.htm",
                docs_ok="SAS7BDAT is a binary sequential file, not CSV.",
                docs_url2="https://ofajardo.github.io/pyreadstat_documentation/_build/html/index.html",
                docs_ok2="Need pyreadstat.read_sas7bdat. Handoff SAS-BIN-5. Not Kingsoft .et.",
                outcome="Still csv-split; .sas7bdat is binary — handoff SAS-BIN-5.",
                domain="sas7bdat-binary-header-vs-csv-text",
                stack="SAS7BDAT",
                seed="sas7bdat-binary-handoff",
                residual="latin1 is not a SAS reader.",
                ticket="SAS-BIN-5",
                ticket_why=".sas7bdat binary ingest owned by stats-plat",
                coverage=87,
            ),
        ),
        (
            _p(
                slug="xlsx-listobject-table-ref",
                goal="Read Excel table (ListObject) ref, not worksheet used range.",
                plan="Read used-as-table, try dimension, then table1 ref.",
                mod="xlsx_tbl",
                test_fn="test_table_ref_not_used",
                src_body=(
                    "def rows(ws):\n"
                    "    return ws.used_range\n"
                ),
                test_body=(
                    "def test_table_ref_not_used():\n"
                    "    assert rows(ws) == 'Invoices[#All]'\n"
                ),
                grep_pat="used_range|ListObject|table1",
                grep_hit="src/xlsx_tbl.py:2: return ws.used_range",
                fail_msg="AssertionError: used range A1:Z999 included scratch; table is A1:D40",
                first_old="    return ws.used_range",
                first_new="    return ws.dimension",
                first_obs="patched dimension (still the sheet, not the table)",
                still_msg="AssertionError: dimension is still used range, not table1 ref",
                reread_obs="xl/tables/table1.xml displayName=Invoices ref=A1:D40",
                plan_change="Use table ref / structured reference. Used range is scratch cells.",
                fix_new="    return ws.table_ref('Invoices')",
                fix_obs="patched table ref",
                docs_url="https://learn.microsoft.com/en-us/office/vba/api/excel.listobject",
                docs_ok="ListObject.Range is the table body; UsedRange includes stray cells.",
                docs_url2="https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/3bd3c748-5e54-4da2-9e56-d5e9e7c5c929",
                docs_ok2="table1.xml ref is the invoice grid. Not quoted-newline, not WPS .et.",
                outcome="Table ref ingested A1:D40. Used range unused (success).",
                domain="xlsx-listobject-table-ref-vs-used-range",
                stack="OOXML table1.xml ListObject",
                seed="xlsx-listobject-table-ref",
                residual="Not defined-name clone; not Kingsoft .et.",
                coverage=85,
            ),
            _p(
                slug="matlab-v73-mat-handoff",
                goal="Do not parse MATLAB v7.3 .mat as CSV.",
                plan="Read mat-as-csv, try hdf5, then hand off loadmat.",
                mod="mat_v73",
                test_fn="test_mat_not_csv",
                src_body=(
                    "def load(path):\n"
                    "    return open(path, 'rb').read().split(b',')\n"
                ),
                test_body=(
                    "def test_mat_not_csv():\n"
                    "    assert load('invoices.mat')[:1] != [open('invoices.mat', 'rb').read()]\n"
                ),
                grep_pat="\\.mat|loadmat|MATLAB 7.3",
                grep_hit="src/mat_v73.py:2: return open(path, 'rb').read().split(b',')",
                fail_msg="AssertionError: MATLAB 7.3 HDF5 magic split on comma; datasets lost",
                first_old="    return open(path, 'rb').read().split(b',')",
                first_new="    import h5py\n    return list(h5py.File(path).keys())",
                first_obs="patched h5py keys (still not scipy loadmat / mat73)",
                still_msg="AssertionError: raw HDF5 keys are not invoice columns",
                reread_obs="v7.3 MAT is HDF5 with MATLAB classes; need mat73/scipy",
                plan_change="Binary v7.3 .mat is stats-plat. Handoff MAT-V73-3.",
                fix_new="    return {'handoff': 'MAT-V73-3'}",
                fix_obs="ticket filed. still hdf5-keys",
                docs_url="https://www.mathworks.com/help/matlab/import_export/mat-file-versions.html",
                docs_ok="v7.3 MAT files are HDF5, not CSV. Keys are MATLAB class wrappers.",
                docs_url2="https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.loadmat.html",
                docs_ok2="Need scipy/mat73. Handoff MAT-V73-3. Not Kingsoft .et.",
                outcome="Still hdf5-keys; v7.3 .mat is MATLAB — handoff MAT-V73-3.",
                domain="matlab-v73-hdf5-mat-vs-csv-text",
                stack="MATLAB v7.3 MAT/HDF5",
                seed="matlab-v73-mat-handoff",
                residual="h5py keys are not loadmat.",
                ticket="MAT-V73-3",
                ticket_why="v7.3 .mat ingest owned by stats-plat",
                coverage=85,
            ),
        ),
    ],
    "websocket-reconnect-factory": [
        (
            _p(
                slug="django-channels-accept-before-group",
                goal="Accept the Django Channels socket before group_add; do not reconnect on 1006.",
                plan="Read group-before-accept, try sleep, then accept then group_add.",
                mod="ch_acc",
                test_fn="test_accept_before_group",
                src_body=(
                    "def connect(self):\n"
                    "    return ['group_add', 'invoices']\n"
                ),
                test_body=(
                    "def test_accept_before_group():\n"
                    "    assert connect(None)[0] == 'accept'\n"
                ),
                grep_pat="group_add|accept|1006",
                grep_hit="src/ch_acc.py:2: return ['group_add', 'invoices']",
                fail_msg="AssertionError: group_add before accept closed 1006; reconnect looped",
                first_old="    return ['group_add', 'invoices']",
                first_new="    return ['sleep', 'group_add', 'invoices']",
                first_obs="patched sleep (still group_add first, still 1006)",
                still_msg="AssertionError: sleep cannot accept; group_add still races handshake",
                reread_obs="Channels requires self.accept() before group_add or the socket is half-open",
                plan_change="accept then group_add. Do not reconnect-loop 1006 as cookie-replay.",
                fix_new="    return ['accept', 'group_add', 'invoices']",
                fix_obs="patched accept-then-group",
                docs_url="https://channels.readthedocs.io/en/latest/topics/consumers.html#websocketconsumer",
                docs_ok="Call accept() during connect before joining groups.",
                docs_url2="https://channels.readthedocs.io/en/latest/topics/channel_layers.html#groups",
                docs_ok2="group_add on an unaccepted socket 1006s. Not cookie-replay.",
                outcome="accept-then-group joined invoices. Reconnect unused (success).",
                domain="django-channels-accept-before-group-add",
                stack="Django Channels WebSocketConsumer",
                seed="django-channels-accept-before-group",
                residual="Not cookie-replay.",
                coverage=86,
            ),
            _p(
                slug="cf-do-hibernate-handoff",
                goal="Do not treat Cloudflare Durable Object websocket hibernation as a client ping miss.",
                plan="Read hibernate-as-ping, try ping 10s, then hand off hibernation.",
                mod="cfdo_hib",
                test_fn="test_hibernate_not_ping",
                src_body=(
                    "def tune(drop):\n"
                    "    return {'client_ping_s': 15} if drop else {}\n"
                ),
                test_body=(
                    "def test_hibernate_not_ping():\n"
                    "    assert 'client_ping_s' not in tune(True)\n"
                ),
                grep_pat="hibernate|client_ping_s|setWebSocketAutoResponse",
                grep_hit="src/cfdo_hib.py:2: return {'client_ping_s': 15} if drop else {}",
                fail_msg="AssertionError: DO hibernate dropped WS; client ping unused",
                first_old="    return {'client_ping_s': 15} if drop else {}",
                first_new="    return {'client_ping_s': 10} if drop else {}",
                first_obs="patched ping 10s (still client, not hibernation)",
                still_msg="AssertionError: client ping cannot keep a hibernated Durable Object awake",
                reread_obs="Durable Object hibernates accepted WS; setWebSocketAutoResponse is DO-side",
                plan_change="Hibernation is Cloudflare. Handoff CFDO-HIB-4.",
                fix_new="    return {'handoff': 'CFDO-HIB-4'} if drop else {}",
                fix_obs="ticket filed. still ping-classed",
                docs_url="https://developers.cloudflare.com/durable-objects/best-practices/websockets/",
                docs_ok="Hibernatable WebSockets use setWebSocketAutoResponse, not client pings.",
                docs_url2="https://developers.cloudflare.com/durable-objects/api/state/#accepthibernatablewebsocket",
                docs_ok2="Hibernation is edge-plat. Handoff CFDO-HIB-4. Not cookie-replay.",
                outcome="Still ping-classed; hibernation is Cloudflare — handoff CFDO-HIB-4.",
                domain="cloudflare-do-websocket-hibernate-vs-client-ping",
                stack="Cloudflare Durable Object hibernation",
                seed="cf-do-hibernate-handoff",
                residual="Ping cannot prevent DO hibernation.",
                ticket="CFDO-HIB-4",
                ticket_why="setWebSocketAutoResponse owned by edge-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="wamp-goodbye-vs-1006",
                goal="Treat WAMP GOODBYE as a clean session end, not RFC6455 1006 reconnect.",
                plan="Read goodbye-as-1006, try 1000, then honor GOODBYE details.",
                mod="wamp_gb",
                test_fn="test_goodbye_not_reconnect",
                src_body=(
                    "def on_msg(msg):\n"
                    "    return 'reconnect' if msg.get('type') == 'GOODBYE' else 'ok'\n"
                ),
                test_body=(
                    "def test_goodbye_not_reconnect():\n"
                    "    assert on_msg({'type': 'GOODBYE'}) == 'close_session'\n"
                ),
                grep_pat="GOODBYE|1006|wamp",
                grep_hit="src/wamp_gb.py:2: return 'reconnect' if msg.get('type') == 'GOODBYE' else 'ok'",
                fail_msg="AssertionError: GOODBYE reconnect-looped; realm already closed",
                first_old="    return 'reconnect' if msg.get('type') == 'GOODBYE' else 'ok'",
                first_new="    return 'reconnect_1000' if msg.get('type') == 'GOODBYE' else 'ok'",
                first_obs="patched 1000 reconnect (still a reconnect loop)",
                still_msg="AssertionError: RFC6455 1000 still resubscribes a closed WAMP realm",
                reread_obs="WAMP GOODBYE is application session end; 1006 is abnormal TCP close",
                plan_change="Close the session on GOODBYE. Do not reconnect-loop as 1006.",
                fix_new="    return 'close_session' if msg.get('type') == 'GOODBYE' else 'ok'",
                fix_obs="patched GOODBYE close",
                docs_url="https://wamp-proto.org/wamp_latest_ietf.html#name-goodbye-0x06",
                docs_ok="GOODBYE ends the WAMP session; it is not an abnormal WebSocket close.",
                docs_url2="https://wamp-proto.org/_static/gen/wamp_latest.html#goodbye-0",
                docs_ok2="Reconnect only after a new HELLO. Not cookie-replay.",
                outcome="GOODBYE closed the realm. Reconnect unused (success).",
                domain="wamp-goodbye-vs-rfc6455-1006-reconnect",
                stack="WAMP GOODBYE",
                seed="wamp-goodbye-vs-1006",
                residual="Not cookie-replay.",
                coverage=84,
            ),
            _p(
                slug="livekit-signal-timeout-handoff",
                goal="Do not treat LiveKit signal WebSocket timeout as a client ping miss.",
                plan="Read signal-as-ping, try ping 5s, then hand off signal timeout.",
                mod="lk_sig",
                test_fn="test_signal_not_ping",
                src_body=(
                    "def tune(drop):\n"
                    "    return {'client_ping_s': 5} if drop else {}\n"
                ),
                test_body=(
                    "def test_signal_not_ping():\n"
                    "    assert 'client_ping_s' not in tune(True)\n"
                ),
                grep_pat="signal_timeout|client_ping_s|livekit",
                grep_hit="src/lk_sig.py:2: return {'client_ping_s': 5} if drop else {}",
                fail_msg="AssertionError: LiveKit signal timeout dropped WS; ping unused",
                first_old="    return {'client_ping_s': 5} if drop else {}",
                first_new="    return {'client_ping_s': 10} if drop else {}",
                first_obs="patched ping 10s (still client, not signal)",
                still_msg="AssertionError: client ping cannot raise LiveKit signal timeout",
                reread_obs="LiveKit signal WS times out independently of media; ping is not signal",
                plan_change="Signal timeout is LiveKit. Handoff LK-SIG-3.",
                fix_new="    return {'handoff': 'LK-SIG-3'} if drop else {}",
                fix_obs="ticket filed. still ping-classed",
                docs_url="https://docs.livekit.io/home/client/connect/",
                docs_ok="Signal connection timeout is server-side, not a client ping interval.",
                docs_url2="https://docs.livekit.io/home/client/events/",
                docs_ok2="Signal timeout is realtime-plat. Handoff LK-SIG-3. Not cookie-replay.",
                outcome="Still ping-classed; signal timeout is LiveKit — handoff LK-SIG-3.",
                domain="livekit-signal-timeout-vs-client-ping",
                stack="LiveKit signal WebSocket",
                seed="livekit-signal-timeout-handoff",
                residual="Ping cannot set signal timeout.",
                ticket="LK-SIG-3",
                ticket_why="signal timeout owned by realtime-plat",
                coverage=84,
            ),
        ),
    ],
    "email-webhook-retry-factory": [
        (
            _p(
                slug="zeptomail-request-plus-event",
                goal="Dedupe Zoho ZeptoMail webhooks on (request_id, event), not email address.",
                plan="Read email-as-pk, try request_id-only, then (request_id, event).",
                mod="zpto_ev",
                test_fn="test_request_plus_event",
                src_body=(
                    "def upsert(ev):\n"
                    "    return ev['email']\n"
                ),
                test_body=(
                    "def test_request_plus_event():\n"
                    "    a = {'request_id': 'r1', 'email': 'a@b', 'event': 'delivered'}\n"
                    "    b = {'request_id': 'r1', 'email': 'a@b', 'event': 'opened'}\n"
                    "    assert upsert(a) != upsert(b)\n"
                ),
                grep_pat="request_id|event|email",
                grep_hit="src/zpto_ev.py:2: return ev['email']",
                fail_msg="AssertionError: delivered+opened collapsed; email is not event pk",
                first_old="    return ev['email']",
                first_new="    return ev['request_id']",
                first_obs="patched request_id (collides across delivered vs opened)",
                still_msg="AssertionError: same request_id delivered+opened still one row",
                reread_obs="ZeptoMail request_id is the send; event distinguishes activity",
                plan_change="PK (request_id, event). Email is the recipient, not the event.",
                fix_new="    return (ev['request_id'], ev['event'])",
                fix_obs="patched (request_id, event)",
                docs_url="https://www.zoho.com/zeptomail/help/api/webhook.html",
                docs_ok="Webhook payload has request_id plus event; retries replay the same pair.",
                docs_url2="https://www.zoho.com/zeptomail/help/webhooks.html",
                docs_ok2="delivered and opened are different events on one request_id.",
                outcome="(request_id, event) stored both events. Email unused (success).",
                domain="zeptomail-webhook-request-id-plus-event",
                stack="Zoho ZeptoMail webhooks",
                seed="zeptomail-request-plus-event",
                residual="Not invoice-row-dup.",
                coverage=86,
            ),
            _p(
                slug="mautic-email-id-handoff",
                goal="Do not treat Mautic email_id as a unique webhook event.",
                plan="Read email-as-event, try email_id+contact, then hand off stat id.",
                mod="mau_em",
                test_fn="test_email_not_event",
                src_body=(
                    "def pk(ev):\n"
                    "    return ev['email_id']\n"
                ),
                test_body=(
                    "def test_email_not_event():\n"
                    "    assert pk({'email_id': '9', 'stat_id': 's1'}) != '9'\n"
                ),
                grep_pat="email_id|stat_id|mautic",
                grep_hit="src/mau_em.py:2: return ev['email_id']",
                fail_msg="AssertionError: campaign email_id collapsed 400 opens into one row",
                first_old="    return ev['email_id']",
                first_new="    return ev['email_id'] + ev.get('contact_id', '')",
                first_obs="patched email+contact (still campaign grain, not event)",
                still_msg="AssertionError: email+contact still one row per recipient per campaign",
                reread_obs="Mautic email_id is the campaign asset; email_stats.id is the activity",
                plan_change="email_id is campaign grain. Handoff MAU-EM-5.",
                fix_new="    return {'handoff': 'MAU-EM-5'}",
                fix_obs="ticket filed. still email-grained",
                docs_url="https://docs.mautic.org/en/contacts/manage-webhooks",
                docs_ok="email_id identifies the campaign email; events need stat id.",
                docs_url2="https://devdocs.mautic.org/#tag/Webhooks",
                docs_ok2="Campaign grain is marketing-plat. Handoff MAU-EM-5. Not invoice-row-dup.",
                outcome="Still email-grained; campaign id is marketing — handoff MAU-EM-5.",
                domain="mautic-email-id-vs-stat-id",
                stack="Mautic email_stats",
                seed="mautic-email-id-handoff",
                residual="email_id is not an event pk.",
                ticket="MAU-EM-5",
                ticket_why="email_stats.id owned by marketing-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="infobip-msgid-plus-event",
                goal="Dedupe Infobip email webhooks on (messageId, event), not destination.",
                plan="Read dest-as-pk, try messageId-only, then (messageId, event).",
                mod="info_ev",
                test_fn="test_msgid_plus_event",
                src_body=(
                    "def upsert(ev):\n"
                    "    return ev['destination']\n"
                ),
                test_body=(
                    "def test_msgid_plus_event():\n"
                    "    a = {'messageId': 'm', 'event': 'DELIVERED', 'destination': 'a@b'}\n"
                    "    b = {'messageId': 'm', 'event': 'OPENED', 'destination': 'a@b'}\n"
                    "    assert upsert(a) != upsert(b)\n"
                ),
                grep_pat="messageId|event|destination",
                grep_hit="src/info_ev.py:2: return ev['destination']",
                fail_msg="AssertionError: DELIVERED+OPENED collapsed on destination",
                first_old="    return ev['destination']",
                first_new="    return ev['messageId']",
                first_obs="patched messageId (collides across events)",
                still_msg="AssertionError: same messageId DELIVERED+OPENED still one row",
                reread_obs="Infobip messageId is the send; event is the activity",
                plan_change="PK (messageId, event). Destination is the recipient.",
                fix_new="    return (ev['messageId'], ev['event'])",
                fix_obs="patched (messageId, event)",
                docs_url="https://www.infobip.com/docs/email/send-emails-over-api",
                docs_ok="Email reports include messageId and event type per activity.",
                docs_url2="https://www.infobip.com/docs/api/channels/email",
                docs_ok2="OPENED after DELIVERED must not overwrite the deliver row.",
                outcome="(messageId, event) kept both rows. Destination unused (success).",
                domain="infobip-email-messageid-plus-event",
                stack="Infobip email reports",
                seed="infobip-msgid-plus-event",
                residual="Not invoice-row-dup.",
                coverage=84,
            ),
            _p(
                slug="getresponse-campaign-handoff",
                goal="Do not treat GetResponse campaignId as a unique email event.",
                plan="Read campaign-as-event, try campaign+email, then hand off activity id.",
                mod="getr_c",
                test_fn="test_campaign_not_event",
                src_body=(
                    "def pk(ev):\n"
                    "    return ev['campaignId']\n"
                ),
                test_body=(
                    "def test_campaign_not_event():\n"
                    "    assert pk({'campaignId': 'c1', 'activityId': 'a9'}) != 'c1'\n"
                ),
                grep_pat="campaignId|activityId|GetResponse",
                grep_hit="src/getr_c.py:2: return ev['campaignId']",
                fail_msg="AssertionError: campaignId collapsed all opens for that campaign",
                first_old="    return ev['campaignId']",
                first_new="    return ev['campaignId'] + ':' + ev.get('email', '')",
                first_obs="patched campaign+email (still campaign grain, not event)",
                still_msg="AssertionError: two opens in one campaign still one row",
                reread_obs="campaignId is the newsletter; activityId is the open/click",
                plan_change="campaignId is campaign grain. Handoff GETR-C-2.",
                fix_new="    return {'handoff': 'GETR-C-2'}",
                fix_obs="ticket filed. still campaign-grained",
                docs_url="https://apidocs.getresponse.com/v3/resources/webhooks",
                docs_ok="campaignId identifies the newsletter, not a send or open.",
                docs_url2="https://www.getresponse.com/help/webhooks.html",
                docs_ok2="Activity ids are campaign-plat. Handoff GETR-C-2. Not invoice-row-dup.",
                outcome="Still campaign-grained; campaign id is marketing — handoff GETR-C-2.",
                domain="getresponse-campaignid-vs-activityid",
                stack="GetResponse webhooks",
                seed="getresponse-campaign-handoff",
                residual="campaignId is not an open.",
                ticket="GETR-C-2",
                ticket_why="GetResponse activityId owned by campaign-plat",
                coverage=84,
            ),
        ),
    ],
    "feature-flag-debug-factory": [
        (
            _p(
                slug="featurehub-sse-vs-poll",
                goal="Honor FeatureHub SSE flag updates; do not keep a stale 5-minute poll.",
                plan="Read poll-as-live, try shorter poll, then SSE listener.",
                mod="fh_sse",
                test_fn="test_sse_not_poll",
                src_body=(
                    "def source():\n"
                    "    return {'poll_s': 300}\n"
                ),
                test_body=(
                    "def test_sse_not_poll():\n"
                    "    assert source().get('mode') == 'sse'\n"
                ),
                grep_pat="poll_s|sse|FeatureHub",
                grep_hit="src/fh_sse.py:2: return {'poll_s': 300}",
                fail_msg="AssertionError: invoice flag flipped 4m ago; poll still stale",
                first_old="    return {'poll_s': 300}",
                first_new="    return {'poll_s': 30}",
                first_obs="patched 30s poll (still poll, still stale between ticks)",
                still_msg="AssertionError: shorter poll is not FeatureHub SSE",
                reread_obs="FeatureHub Edge /features/{key} SSE pushes updates; poll is fallback",
                plan_change="Subscribe SSE. Poll interval is not live targeting.",
                fix_new="    return {'mode': 'sse'}",
                fix_obs="patched SSE",
                docs_url="https://docs.featurehub.io/featurehub/latest/sdks-development.html#_server_sent_events",
                docs_ok="FeatureHub SDKs prefer SSE from Edge; poll is a degraded fallback.",
                docs_url2="https://docs.featurehub.io/featurehub/latest/sdks.html",
                docs_ok2="SSE carries targeting changes. Not Statsig user vs company.",
                outcome="SSE served the flipped flag. Poll unused (success).",
                domain="featurehub-sse-vs-stale-poll",
                stack="FeatureHub Edge SSE",
                seed="featurehub-sse-vs-poll",
                residual="Not Statsig user vs company.",
                coverage=85,
            ),
            _p(
                slug="flagr-variant-handoff",
                goal="Do not treat Flagr variant distribution as a boolean gate.",
                plan="Read variant-as-bool, try percentage, then hand off variant.",
                mod="flg_var",
                test_fn="test_variant_not_bool",
                src_body=(
                    "def eval_flag(resp):\n"
                    "    return bool(resp.get('enabled'))\n"
                ),
                test_body=(
                    "def test_variant_not_bool():\n"
                    "    assert eval_flag({'enabled': True, 'variantID': 2}) != True\n"
                ),
                grep_pat="variantID|enabled|Flagr",
                grep_hit="src/flg_var.py:2: return bool(resp.get('enabled'))",
                fail_msg="AssertionError: variantID 2 treated as boolean on; payload unused",
                first_old="    return bool(resp.get('enabled'))",
                first_new="    return resp.get('enabled') and resp.get('percent', 0) > 0",
                first_obs="patched percent (still boolean, still not variant)",
                still_msg="AssertionError: percentage is not Flagr variant distribution",
                reread_obs="Flagr evaluation returns variantID/variantKey; enabled only means attached",
                plan_change="Variant distribution is flag-plat. Handoff FLG-VAR-4.",
                fix_new="    return {'handoff': 'FLG-VAR-4'}",
                fix_obs="ticket filed. still bool-classed",
                docs_url="https://checkr.github.io/flagr/#/flagr/evaluation",
                docs_ok="Flagr eval returns a variant, not just enabled.",
                docs_url2="https://github.com/openflagr/flagr",
                docs_ok2="Variant weights are flag-plat. Handoff FLG-VAR-4. Not Statsig company.",
                outcome="Still bool-classed; variant is flag-plat — handoff FLG-VAR-4.",
                domain="flagr-variant-distribution-vs-boolean-gate",
                stack="OpenFlagr evaluation",
                seed="flagr-variant-handoff",
                residual="Not Statsig user vs company.",
                ticket="FLG-VAR-4",
                ticket_why="variant distribution owned by flag-plat",
                coverage=85,
            ),
        ),
        (
            _p(
                slug="django-flags-condition-vs-cookie",
                goal="Honor django-flags conditions (user.is_staff), not a cookie override.",
                plan="Read cookie-as-flag, try session, then condition callback.",
                mod="djf_cond",
                test_fn="test_condition_not_cookie",
                src_body=(
                    "def enabled(req):\n"
                    "    return req.get('cookie_flag') == '1'\n"
                ),
                test_body=(
                    "def test_condition_not_cookie():\n"
                    "    assert enabled({'cookie_flag': '1', 'is_staff': False}) is False\n"
                ),
                grep_pat="cookie_flag|is_staff|django-flags",
                grep_hit="src/djf_cond.py:2: return req.get('cookie_flag') == '1'",
                fail_msg="AssertionError: cookie forced invoice flag on for anonymous",
                first_old="    return req.get('cookie_flag') == '1'",
                first_new="    return req.get('session_flag') == '1'",
                first_obs="patched session (still not the condition)",
                still_msg="AssertionError: session is not user.is_staff condition",
                reread_obs="FLAG_INVOICE_BETA conditions=[('boolean', True), ('user', 'is_staff')]",
                plan_change="Evaluate registered conditions. Cookie is not the actor.",
                fix_new="    return bool(req.get('is_staff'))",
                fix_obs="patched is_staff condition",
                docs_url="https://cfpb.github.io/django-flags/conditions/",
                docs_ok="django-flags evaluates registered conditions, not ad-hoc cookies.",
                docs_url2="https://cfpb.github.io/django-flags/usage/",
                docs_ok2="user.is_staff is the condition. Not Statsig user vs company.",
                outcome="is_staff condition hid the flag. Cookie unused (success).",
                domain="django-flags-condition-vs-cookie-override",
                stack="django-flags conditions",
                seed="django-flags-condition-vs-cookie",
                residual="Not waffle clone; not Statsig company.",
                coverage=83,
            ),
            _p(
                slug="abtasty-campaign-handoff",
                goal="Do not treat an AB Tasty campaign as a boolean feature flag.",
                plan="Read campaign-as-flag, try cookie, then hand off campaign.",
                mod="abt_camp",
                test_fn="test_campaign_not_flag",
                src_body=(
                    "def why_on(ctx):\n"
                    "    return 'flag' if ctx.get('campaign_id') else 'off'\n"
                ),
                test_body=(
                    "def test_campaign_not_flag():\n"
                    "    assert why_on({'campaign_id': 'c1'}) != 'flag'\n"
                ),
                grep_pat="campaign_id|AB Tasty|flag",
                grep_hit="src/abt_camp.py:2: return 'flag' if ctx.get('campaign_id') else 'off'",
                fail_msg="AssertionError: AB Tasty campaign labeled feature flag; ops looked at flags",
                first_old="    return 'flag' if ctx.get('campaign_id') else 'off'",
                first_new="    return 'flag_cookie' if ctx.get('campaign_id') else 'off'",
                first_obs="patched cookie (still flag-classed)",
                still_msg="AssertionError: campaign allocation is not a boolean flag",
                reread_obs="AB Tasty campaign is an experiment; feature flags live elsewhere",
                plan_change="Campaign allocation is experiment-plat. Handoff ABT-CAMP-3.",
                fix_new="    return 'handoff_ABT-CAMP-3' if ctx.get('campaign_id') else 'off'",
                fix_obs="ticket filed. still flag-classed",
                docs_url="https://developers.abtasty.com/docs",
                docs_ok="AB Tasty campaigns allocate variations; they are not boolean flags.",
                docs_url2="https://support.abtasty.com/hc/en-us/articles/360014768317",
                docs_ok2="Campaign unit is experiment-plat. Handoff ABT-CAMP-3. Not Statsig.",
                outcome="Still flag-classed; campaign is experiment — handoff ABT-CAMP-3.",
                domain="abtasty-campaign-vs-boolean-flag",
                stack="AB Tasty campaigns",
                seed="abtasty-campaign-handoff",
                residual="Not Statsig user vs company.",
                ticket="ABT-CAMP-3",
                ticket_why="campaign allocation owned by experiment-plat",
                coverage=83,
            ),
        ),
    ],
    "search-index-rebuild-factory": [
        (
            _p(
                slug="pg-rum-weight-vs-gin",
                goal="Weight Postgres RUM posting lists in place; do not rebuild via TRUNCATE.",
                plan="Read unweighted-rum, try DROP INDEX, then rum_tsvector addweight.",
                mod="pg_rum",
                test_fn="test_rum_weight_not_truncate",
                src_body=(
                    "def tsv(title, body):\n"
                    "    return \"to_tsvector('simple', body)\"\n"
                ),
                test_body=(
                    "def test_rum_weight_not_truncate():\n"
                    "    sql = tsv('SKU-9', 'invoice body')\n"
                    "    assert 'addweight' in sql and 'TRUNCATE' not in sql\n"
                ),
                grep_pat="addweight|rum|TRUNCATE",
                grep_hit="src/pg_rum.py:2: return \"to_tsvector('simple', body)\"",
                fail_msg="AssertionError: title SKU-9 not in RUM posting; body-only simple",
                first_old="    return \"to_tsvector('simple', body)\"",
                first_new="    return 'TRUNCATE invoices; to_tsvector(body)'",
                first_obs="patched TRUNCATE (banned rebuild)",
                still_msg="AssertionError: TRUNCATE is not RUM addweight; data gone",
                reread_obs="CREATE INDEX USING rum (tsv rum_tsvector_ops); UPDATE addweight title A",
                plan_change="In-place UPDATE addweight. Do not TRUNCATE or DROP INDEX.",
                fix_new=(
                    "    return \"setweight(to_tsvector(title),'A') || setweight(to_tsvector(body),'D')"
                    " /* rum addweight */\""
                ),
                fix_obs="patched rum addweight A||D",
                docs_url="https://github.com/postgrespro/rum",
                docs_ok="RUM stores posting lists with addweight; UPDATE the column, do not TRUNCATE.",
                docs_url2="https://postgrespro.com/docs/enterprise/current/rum",
                docs_ok2="RUM is not GIN rebuild. Not TRUNCATE-then-reindex. Left sir-r26 placeholder.",
                outcome="Title weight A ranked SKU-9 first. TRUNCATE unused (success).",
                domain="postgres-rum-addweight-vs-truncate",
                stack="PostgreSQL RUM tsvector",
                seed="pg-rum-weight-vs-gin",
                residual="Not TRUNCATE-then-reindex. Left sir-r26 placeholder in raw.",
                coverage=87,
            ),
            _p(
                slug="cloudsearch-fields-handoff",
                goal="Do not search Amazon CloudSearch before index fields are deployed.",
                plan="Read schema-as-live, try sleep, then hand off index field deploy.",
                mod="amz_cs",
                test_fn="test_fields_not_live",
                src_body=(
                    "def ready(domain):\n"
                    "    return True\n"
                ),
                test_body=(
                    "def test_fields_not_live():\n"
                    "    assert ready('ocr') is not True\n"
                ),
                grep_pat="IndexField|cs-configure|deploy",
                grep_hit="src/amz_cs.py:2: return True",
                fail_msg="AssertionError: search empty; sku IndexField never deployed",
                first_old="    return True",
                first_new="    return 'slept'",
                first_obs="patched sleep (still no field deploy)",
                still_msg="AssertionError: sleep cannot deploy CloudSearch index fields",
                reread_obs="CloudSearch IndexField sku is RequiresIndexDocuments until deploy",
                plan_change="Index field deploy is aws-plat. Handoff AMZ-CS-2. Not TRUNCATE.",
                fix_new="    return {'handoff': 'AMZ-CS-2'}",
                fix_obs="ticket filed. still undeployed",
                docs_url="https://docs.aws.amazon.com/cloudsearch/latest/developerguide/configuring-index-fields.html",
                docs_ok="Index fields must be deployed before documents are searchable.",
                docs_url2="https://docs.aws.amazon.com/cloudsearch/latest/developerguide/indexing.html",
                docs_ok2="Deploy is aws-plat. Handoff AMZ-CS-2. Not TRUNCATE-reindex.",
                outcome="Still undeployed; index fields are aws-plat — handoff AMZ-CS-2.",
                domain="amazon-cloudsearch-indexfield-deploy-vs-search",
                stack="Amazon CloudSearch IndexField",
                seed="cloudsearch-fields-handoff",
                residual="Not TRUNCATE-then-reindex.",
                ticket="AMZ-CS-2",
                ticket_why="IndexField deploy owned by aws-plat",
                coverage=87,
            ),
        ),
        (
            _p(
                slug="whoosh-stem-vs-wildcard",
                goal="Use Whoosh stemming on invoice tokens; do not leading-wildcard the query.",
                plan="Read wildcard-as-stem, try DROP TABLE, then StemmingAnalyzer.",
                mod="whoosh_st",
                test_fn="test_stem_not_wildcard",
                src_body=(
                    "def q(term):\n"
                    "    return f'*{term}*'\n"
                ),
                test_body=(
                    "def test_stem_not_wildcard():\n"
                    "    assert 'invoic' in q('invoices') and '*' not in q('invoices')\n"
                ),
                grep_pat="StemmingAnalyzer|\\*|TRUNCATE",
                grep_hit="src/whoosh_st.py:2: return f'*{term}*'",
                fail_msg="AssertionError: leading wildcard missed stem invoic; seq scan",
                first_old="    return f'*{term}*'",
                first_new="    return 'TRUNCATE invoices; *' + term + '*'",
                first_obs="patched TRUNCATE (banned rebuild)",
                still_msg="AssertionError: TRUNCATE is not a stemmer; data gone",
                reread_obs="Whoosh StemmingAnalyzer reduces invoices->invoic at index time",
                plan_change="Index with StemmingAnalyzer. Do not TRUNCATE. Wildcard is not stem.",
                fix_new="    return 'invoic'",
                fix_obs="patched stem invoic",
                docs_url="https://whoosh.readthedocs.io/en/latest/stemming.html",
                docs_ok="StemmingAnalyzer stores stems; leading wildcards cannot use the term index.",
                docs_url2="https://whoosh.readthedocs.io/en/latest/analysis.html",
                docs_ok2="Rebuild is create index, not TRUNCATE. Left sir-r26 placeholder.",
                outcome="Stem invoic hit invoices. Wildcard unused (success).",
                domain="whoosh-stemminganalyzer-vs-leading-wildcard",
                stack="Whoosh StemmingAnalyzer",
                seed="whoosh-stem-vs-wildcard",
                residual="Not TRUNCATE-then-reindex. Left sir-r26 placeholder in raw.",
                coverage=85,
            ),
            _p(
                slug="azure-search-synonym-handoff",
                goal="Do not search Azure AI Search before the synonym map is attached.",
                plan="Read map-as-live, try sleep, then hand off synonym attach.",
                mod="az_syn",
                test_fn="test_synonym_not_live",
                src_body=(
                    "def ready(index):\n"
                    "    return True\n"
                ),
                test_body=(
                    "def test_synonym_not_live():\n"
                    "    assert ready('ocr') is not True\n"
                ),
                grep_pat="synonymMaps|create_synonym_map|attach",
                grep_hit="src/az_syn.py:2: return True",
                fail_msg="AssertionError: sku~item missed; synonym map never attached",
                first_old="    return True",
                first_new="    return 'slept'",
                first_obs="patched sleep (still no synonym attach)",
                still_msg="AssertionError: sleep cannot attach synonymMaps on the sku field",
                reread_obs="Azure AI Search synonym map must be created then referenced on the field",
                plan_change="Synonym attach is azure-plat. Handoff AZ-SYN-4. Not TRUNCATE.",
                fix_new="    return {'handoff': 'AZ-SYN-4'}",
                fix_obs="ticket filed. still unattached",
                docs_url="https://learn.microsoft.com/en-us/azure/search/search-synonyms",
                docs_ok="Synonym maps are attached per field; creating the map is not enough.",
                docs_url2="https://learn.microsoft.com/en-us/rest/api/searchservice/create-synonym-map",
                docs_ok2="Attach is azure-plat. Handoff AZ-SYN-4. Not TRUNCATE. Left sir-r26.",
                outcome="Still unattached; synonym map is azure-plat — handoff AZ-SYN-4.",
                domain="azure-ai-search-synonym-map-attach-vs-query",
                stack="Azure AI Search synonymMaps",
                seed="azure-search-synonym-handoff",
                residual="Not TRUNCATE-then-reindex.",
                ticket="AZ-SYN-4",
                ticket_why="synonymMaps attach owned by azure-plat",
                coverage=85,
            ),
        ),
    ],
    "log-redaction-factory": [
        (
            _p(
                slug="structlog-processor-refresh-token",
                goal="Install a structlog processor that redacts refresh_token; do not drop the logger.",
                plan="Read drop-as-redact, try NullHandler, then processor redact.",
                mod="sl_rtok",
                test_fn="test_processor_not_drop",
                src_body=(
                    "def configure():\n"
                    "    return {'drop': True}\n"
                ),
                test_body=(
                    "def test_processor_not_drop():\n"
                    "    c = configure()\n"
                    "    assert c.get('redact') == ('refresh_token',) and not c.get('drop')\n"
                ),
                grep_pat="refresh_token|NullHandler|structlog",
                grep_hit="src/sl_rtok.py:2: return {'drop': True}",
                fail_msg="AssertionError: drop swallowed request_id; refresh_token still in event_dict",
                first_old="    return {'drop': True}",
                first_new="    return {'handlers': []}",
                first_obs="patched empty handlers (still drop, still not processor)",
                still_msg="AssertionError: empty handlers drop keep-fields; need processor redact",
                reread_obs="structlog processors can pop refresh_token and keep request_id",
                plan_change="Processor redacts refresh_token. Do not drop the logger.",
                fix_new="    return {'redact': ('refresh_token',), 'drop': False}",
                fix_obs="patched processor redact",
                docs_url="https://www.structlog.org/en/stable/processors.html",
                docs_ok="Processors rewrite event_dict; dropping the logger loses request_id.",
                docs_url2="https://www.structlog.org/en/stable/standard-library.html",
                docs_ok2="Keep request_id. Not python-json-logger clone.",
                outcome="Processor redacted refresh_token. Drop unused (success).",
                domain="structlog-processor-refresh-token-vs-drop",
                stack="structlog processors",
                seed="structlog-processor-refresh-token",
                residual="Authorization header dump still unused. Not python-json-logger.",
                coverage=84,
            ),
            _p(
                slug="rollbar-payload-handoff",
                goal="Do not mute the process to hide a Rollbar payload that still stores pan.",
                plan="Read mute-as-redact, try unset token, then hand off payload filter.",
                mod="rb_pan",
                test_fn="test_mute_not_redact",
                src_body=(
                    "def configure():\n"
                    "    return {'mute': True}\n"
                ),
                test_body=(
                    "def test_mute_not_redact():\n"
                    "    assert 'mute' not in configure()\n"
                ),
                grep_pat="ROLLBAR|payload|pan",
                grep_hit="src/rb_pan.py:2: return {'mute': True}",
                fail_msg="AssertionError: mute dropped operation; Rollbar still stores pan",
                first_old="    return {'mute': True}",
                first_new="    return {'access_token': None}",
                first_obs="patched unset token (still mute, still not payload filter)",
                still_msg="AssertionError: unsetting the token drops operation; pan stays server-side",
                reread_obs="Rollbar payload filter must scrub pan; mute is not redaction",
                plan_change="Payload filter is rollbar-plat. Handoff RB-PAN-3.",
                fix_new="    return {'handoff': 'RB-PAN-3'}",
                fix_obs="ticket filed. still mute-classed",
                docs_url="https://docs.rollbar.com/docs/python#scrubbing-items",
                docs_ok="Rollbar scrub_fields / payload filter redacts pan; mute drops the event.",
                docs_url2="https://docs.rollbar.com/docs/python",
                docs_ok2="Server-side payload is rollbar-plat. Handoff RB-PAN-3. Not json-logger.",
                outcome="Still mute-classed; payload filter is Rollbar — handoff RB-PAN-3.",
                domain="rollbar-payload-filter-vs-process-mute",
                stack="Rollbar payload scrub",
                seed="rollbar-payload-handoff",
                residual="Mute is not redaction.",
                ticket="RB-PAN-3",
                ticket_why="Rollbar payload filter owned by obs-plat",
                coverage=84,
            ),
        ),
        (
            _p(
                slug="fluentbit-modify-session",
                goal="Land a fluent-bit modify filter that redacts session_id; do not drop the record.",
                plan="Read drop-as-redact, try Match drop, then modify Remove_key.",
                mod="fb_sess",
                test_fn="test_modify_not_drop",
                src_body=(
                    "def filter_conf():\n"
                    "    return {'Match': '*', 'drop': True}\n"
                ),
                test_body=(
                    "def test_modify_not_drop():\n"
                    "    c = filter_conf()\n"
                    "    assert c.get('Remove_key') == 'session_id' and not c.get('drop')\n"
                ),
                grep_pat="session_id|Remove_key|fluent-bit",
                grep_hit="src/fb_sess.py:2: return {'Match': '*', 'drop': True}",
                fail_msg="AssertionError: drop swallowed method; session_id still in record",
                first_old="    return {'Match': '*', 'drop': True}",
                first_new="    return {'Match': '*', 'Alias': 'drop'}",
                first_obs="patched alias drop (still drop, still not modify)",
                still_msg="AssertionError: alias drop still loses method; need modify Remove_key",
                reread_obs="fluent-bit Filter modify Remove_key session_id keeps method",
                plan_change="modify Remove_key session_id. Do not drop the record.",
                fix_new="    return {'Remove_key': 'session_id', 'drop': False}",
                fix_obs="patched modify Remove_key",
                docs_url="https://docs.fluentbit.io/manual/pipeline/filters/modify",
                docs_ok="modify can Remove_key session_id while keeping method.",
                docs_url2="https://docs.fluentbit.io/manual/pipeline/filters",
                docs_ok2="Drop is not redaction. Not fluentd clone, not python-json-logger.",
                outcome="modify removed session_id. Drop unused (success).",
                domain="fluentbit-modify-session-id-vs-drop",
                stack="fluent-bit modify filter",
                seed="fluentbit-modify-session",
                residual="Not fluentd record_transformer clone.",
                coverage=83,
            ),
            _p(
                slug="coralogix-parse-handoff",
                goal="Do not mute stdout to hide a Coralogix parse that still stores pan.",
                plan="Read mute-as-redact, try drop rule, then hand off parse.",
                mod="cx_parse",
                test_fn="test_mute_not_parse",
                src_body=(
                    "def configure():\n"
                    "    return {'mute_stdout': True}\n"
                ),
                test_body=(
                    "def test_mute_not_parse():\n"
                    "    assert 'mute_stdout' not in configure()\n"
                ),
                grep_pat="coralogix|parse|pan",
                grep_hit="src/cx_parse.py:2: return {'mute_stdout': True}",
                fail_msg="AssertionError: mute dropped method; Coralogix still stores pan",
                first_old="    return {'mute_stdout': True}",
                first_new="    return {'drop_rule': True}",
                first_obs="patched drop rule (still mute-classed)",
                still_msg="AssertionError: drop rule still loses method; parse lives in Coralogix",
                reread_obs="Coralogix parsing rules store pan server-side; app mute is not redact",
                plan_change="Parse rule is coralogix-plat. Handoff CX-PARSE-2.",
                fix_new="    return {'handoff': 'CX-PARSE-2'}",
                fix_obs="ticket filed. still mute-classed",
                docs_url="https://coralogix.com/docs/developer-portal/ingest-data/",
                docs_ok="Parsing rules run in Coralogix; app mute cannot rewrite stored pan.",
                docs_url2="https://coralogix.com/docs/user-guides/account-management/data-usage/data-redaction/",
                docs_ok2="Server-side redact is obs-plat. Handoff CX-PARSE-2. Not json-logger.",
                outcome="Still mute-classed; parse is Coralogix — handoff CX-PARSE-2.",
                domain="coralogix-parse-rule-vs-stdout-mute",
                stack="Coralogix parsing",
                seed="coralogix-parse-handoff",
                residual="Mute is not redaction.",
                ticket="CX-PARSE-2",
                ticket_why="Coralogix parse owned by obs-plat",
                coverage=83,
            ),
        ),
    ],
}
