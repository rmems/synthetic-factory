"""Unique Q=2 plants for idle hopper factories. Do not clone BAN lists."""

# Each factory list is consumed in order against live frontier rounds.
# Pair = (success_plant, handoff_plant).

PREFIX = {
    "rate-limit-backoff-factory": "rlb",
    "queue-backpressure-factory": "qbp",
    "csv-excel-ingest-factory": "cei",
    "websocket-reconnect-factory": "wsr",
    "email-webhook-retry-factory": "ewr",
    "feature-flag-debug-factory": "ffd",
    "ssl-cert-rotation-factory": "ssl",
    "search-index-rebuild-factory": "sir",
}

START = {
    "rate-limit-backoff-factory": 53,
    "queue-backpressure-factory": 32,
    "csv-excel-ingest-factory": 32,
    "websocket-reconnect-factory": 32,
    "email-webhook-retry-factory": 31,
    "feature-flag-debug-factory": 32,
    "ssl-cert-rotation-factory": 27,
    "search-index-rebuild-factory": 28,
}

CYCLE = [
    "rate-limit-backoff-factory",
    "queue-backpressure-factory",
    "csv-excel-ingest-factory",
    "websocket-reconnect-factory",
    "email-webhook-retry-factory",
    "feature-flag-debug-factory",
    "ssl-cert-rotation-factory",
    "search-index-rebuild-factory",
]


def _p(**kwargs):
    return kwargs


PAIRS = {
    "rate-limit-backoff-factory": [
        (
            _p(
                slug="gitlab-observed-as-remaining",
                goal="Honor GitLab RateLimit-Observed as used count, not remaining.",
                plan="Read Observed-as-remaining, try 100-minus, then Limit-Observed.",
                mod="gl_obs",
                test_fn="test_observed_is_used_count",
                src_body=(
                    "def remaining(h):\n"
                    "    return int(h['RateLimit-Observed'])\n"
                ),
                test_body=(
                    "def test_observed_is_used_count():\n"
                    "    h = {'RateLimit-Limit': '100', 'RateLimit-Observed': '40',"
                    " 'RateLimit-Remaining': '60'}\n"
                    "    assert remaining(h) == 60\n"
                ),
                grep_pat="RateLimit-Observed|RateLimit-Remaining|RateLimit-Limit",
                grep_hit="src/gl_obs.py:2: return int(h['RateLimit-Observed'])",
                fail_msg="AssertionError: 40 == 60; Observed is used count not remaining",
                first_old="    return int(h['RateLimit-Observed'])",
                first_new="    return 100 - int(h['RateLimit-Observed'])",
                first_obs="patched 100-minus (hardcoded limit; Limit header unused)",
                still_msg="AssertionError: still wrong when Limit is 300; do not hardcode 100",
                reread_obs="Observed=40 Limit=100 Remaining=60; remaining is Limit-Observed",
                plan_change="Use Limit minus Observed (or Remaining). Observed is not remaining.",
                fix_new=(
                    "    return int(h['RateLimit-Limit']) - int(h['RateLimit-Observed'])"
                ),
                fix_obs="patched Limit-Observed",
                docs_url="https://docs.gitlab.com/ee/user/gitlab_com/#gitlabcom-specific-rate-limits",
                docs_ok="RateLimit-Observed is requests already used in the window.",
                docs_url2="https://docs.gitlab.com/ee/administration/settings/rate_limit_on_users.html",
                docs_ok2="Prefer RateLimit-Remaining; Observed is the used counter.",
                outcome="Limit-Observed matched Remaining. Lunch search unblocked (success).",
                domain="gitlab-ratelimit-observed-used-count-vs-remaining",
                stack="GitLab REST rate-limit headers",
                seed="gitlab-observed-as-remaining",
                residual="Observed is used count; Remaining/Limit-Observed is wait budget.",
                coverage=84,
            ),
            _p(
                slug="bitbucket-hourly-plan-handoff",
                goal="Do not treat Bitbucket Cloud 429 as a sleepable per-call rate.",
                plan="Read hourly-as-sleep, try 3600s, then hand off workspace plan.",
                mod="bb_hr",
                test_fn="test_hourly_not_sleep",
                src_body=(
                    "def classify(status, ctx):\n"
                    "    return 'sleep_2s' if status == 429 else 'ok'\n"
                ),
                test_body=(
                    "def test_hourly_not_sleep():\n"
                    "    assert classify(429, {'scope': 'hourly_user'}) != 'sleep_2s'\n"
                ),
                grep_pat="hourly_user|429|workspace",
                grep_hit="src/bb_hr.py:2: return 'sleep_2s' if status == 429 else 'ok'",
                fail_msg="AssertionError: hourly user 429 slept 2s; workspace plan is billing",
                first_old="    return 'sleep_2s' if status == 429 else 'ok'",
                first_new="    return 'sleep_3600' if status == 429 else 'ok'",
                first_obs="patched 3600s (still treating plan cap as per-call rate)",
                still_msg="AssertionError: sleep cannot mint a Standard workspace plan",
                reread_obs="429 x-rate-limit-near-limit on /2.0/repositories is hourly user cap",
                plan_change="Hourly user quota is a workspace plan. Handoff BB-PLAN-4.",
                fix_new="    return 'handoff_BB-PLAN-4' if status == 429 else 'ok'",
                fix_obs="ticket filed. still rate-classed until billing",
                docs_url="https://developer.atlassian.com/cloud/bitbucket/rest/intro/#rate-limits",
                docs_ok="Bitbucket Cloud 429 is per-user hourly; plan upgrades are billing.",
                docs_url2="https://support.atlassian.com/bitbucket-cloud/docs/rate-limits/",
                docs_ok2="Sleep cannot change workspace plan. Handoff BB-PLAN-4.",
                outcome="Still rate-classed; workspace plan is billing — handoff BB-PLAN-4.",
                domain="bitbucket-cloud-hourly-user-quota-vs-sleep",
                stack="Bitbucket Cloud REST",
                seed="bitbucket-hourly-plan-handoff",
                residual="Sleep cannot mint a workspace plan.",
                ticket="BB-PLAN-4",
                ticket_why="hourly user 429 owned by billing-plat workspace plan",
                coverage=84,
            ),
        ),
        (
            _p(
                slug="hubspot-search-10s-vs-daily",
                goal="Honor HubSpot CRM Search 4-per-10s, not the daily 10k as the stall.",
                plan="Read 10s-as-daily, try sleep-until-midnight, then wait the 10s window.",
                mod="hs_srch",
                test_fn="test_search_10s_window",
                src_body=(
                    "def wait_for(err):\n"
                    "    return {'until': 'midnight'} if err == '429 SEARCH' else {}\n"
                ),
                test_body=(
                    "def test_search_10s_window():\n"
                    "    w = wait_for('429 SEARCH')\n"
                    "    assert w.get('window_s') == 10 and 'midnight' not in w.values()\n"
                ),
                grep_pat="midnight|429 SEARCH|window_s",
                grep_hit="src/hs_srch.py:2: return {'until': 'midnight'} if err == '429 SEARCH'",
                fail_msg="AssertionError: SEARCH 429 waited until midnight; window is 10s",
                first_old="    return {'until': 'midnight'} if err == '429 SEARCH' else {}",
                first_new="    return {'until': 'plus_3600'} if err == '429 SEARCH' else {}",
                first_obs="patched +1h (still a daily/hourly budget, not 10s)",
                still_msg="AssertionError: 3600s still ignores the 4-per-10s SEARCH window",
                reread_obs="CRM Search secondarily limited to 4 requests per 10 seconds",
                plan_change="Wait the 10-second SEARCH window; daily 10k is a different budget.",
                fix_new="    return {'window_s': 10} if err == '429 SEARCH' else {}",
                fix_obs="patched 10s SEARCH window",
                docs_url="https://developers.hubspot.com/docs/api/usage-details",
                docs_ok="CRM Search is 4 requests / 10 seconds, separate from daily 10k.",
                docs_url2="https://developers.hubspot.com/docs/api/crm/search",
                docs_ok2="Burst 429 on /crm/v3/objects/contacts/search is the 10s window.",
                outcome="10s SEARCH window unblocked lunch ingest. Daily unused (success).",
                domain="hubspot-crm-search-10s-window-vs-daily-10k",
                stack="HubSpot CRM Search API",
                seed="hubspot-search-10s-vs-daily",
                residual="Daily 10k is not the SEARCH stall.",
                coverage=85,
            ),
            _p(
                slug="zendesk-incremental-cursor-handoff",
                goal="Do not retry Zendesk incremental-export 429 as request-rate.",
                plan="Read cursor-as-429, try 2s sleep, then hand off export cursor.",
                mod="zd_inc",
                test_fn="test_incremental_not_rate",
                src_body=(
                    "def classify(body):\n"
                    "    return 'rate' if '429' in body else 'ok'\n"
                ),
                test_body=(
                    "def test_incremental_not_rate():\n"
                    "    assert classify('429 missing start_time') != 'rate'\n"
                ),
                grep_pat="start_time|incremental|429",
                grep_hit="src/zd_inc.py:2: return 'rate' if '429' in body else 'ok'",
                fail_msg="AssertionError: missing start_time retried as rate; cursor is export-plat",
                first_old="    return 'rate' if '429' in body else 'ok'",
                first_new="    return 'rate_2s' if '429' in body else 'ok'",
                first_obs="patched 2s (still rate-classed)",
                still_msg="AssertionError: still rate on missing start_time; cursor is export-plat",
                reread_obs="incremental tickets.json 429 with missing start_time is a cursor stall",
                plan_change="Cursor stall is not rate. Handoff ZD-INC-5.",
                fix_new="    return 'handoff_ZD-INC-5' if 'start_time' in body else 'ok'",
                fix_obs="ticket filed. still rate-classed",
                docs_url="https://developer.zendesk.com/api-reference/ticketing/ticket-management/incremental_exports/",
                docs_ok="Incremental export needs start_time/cursor; 429 here is not per-call rate.",
                docs_url2="https://developer.zendesk.com/documentation/ticketing/managing-tickets/using-the-incremental-export-api/",
                docs_ok2="export-plat owns the cursor. Handoff ZD-INC-5.",
                outcome="Still rate-classed; cursor is export-plat — handoff ZD-INC-5.",
                domain="zendesk-incremental-export-cursor-vs-http-429",
                stack="Zendesk incremental export API",
                seed="zendesk-incremental-cursor-handoff",
                residual="Sleep cannot mint start_time.",
                ticket="ZD-INC-5",
                ticket_why="incremental 429 missing start_time owned by export-plat",
                coverage=85,
            ),
        ),
        (
            _p(
                slug="figma-file-vs-team-rate",
                goal="Honor Figma per-file 429 separately from the team-level budget.",
                plan="Read file-as-team, try team sleep, then file-scoped remaining.",
                mod="fg_file",
                test_fn="test_file_rate_not_team",
                src_body=(
                    "def bucket(h):\n"
                    "    return 'team' if h.get('X-RateLimit-Type') == 'file' else 'ok'\n"
                ),
                test_body=(
                    "def test_file_rate_not_team():\n"
                    "    assert bucket({'X-RateLimit-Type': 'file'}) == 'file'\n"
                ),
                grep_pat="X-RateLimit-Type|team|file",
                grep_hit="src/fg_file.py:2: return 'team' if h.get('X-RateLimit-Type') == 'file'",
                fail_msg="AssertionError: file 429 slept the team bucket and stalled other files",
                first_old="    return 'team' if h.get('X-RateLimit-Type') == 'file' else 'ok'",
                first_new="    return 'team_share' if h.get('X-RateLimit-Type') == 'file' else 'ok'",
                first_obs="patched team_share (still one bucket for all files)",
                still_msg="AssertionError: file-scoped 429 must not drain the team budget",
                reread_obs="Figma file rate is per file key; team rate is a second counter",
                plan_change="Key sleep on file_key; do not debit the team bucket for a file 429.",
                fix_new="    return 'file' if h.get('X-RateLimit-Type') == 'file' else 'ok'",
                fix_obs="patched file-scoped bucket",
                docs_url="https://developers.figma.com/docs/rest-api/rate-limits/",
                docs_ok="Figma REST has per-file and per-team limits as separate counters.",
                docs_url2="https://developers.figma.com/docs/rest-api/files/",
                docs_ok2="A file 429 must not pause GET /v1/files on a different key.",
                outcome="File-scoped remaining unblocked other files. Team unused (success).",
                domain="figma-rest-file-rate-vs-team-rate",
                stack="Figma REST rate limits",
                seed="figma-file-vs-team-rate",
                residual="Team budget is a second counter.",
                coverage=83,
            ),
            _p(
                slug="zoom-meeting-create-daily-handoff",
                goal="Do not retry Zoom meeting-create 429 as per-second rate.",
                plan="Read create-as-rps, try 1s sleep, then hand off account daily cap.",
                mod="zm_mtg",
                test_fn="test_create_not_rps",
                src_body=(
                    "def classify(path, status):\n"
                    "    return 'rps' if status == 429 else 'ok'\n"
                ),
                test_body=(
                    "def test_create_not_rps():\n"
                    "    assert classify('/meetings', 429) != 'rps'\n"
                ),
                grep_pat="meetings|429|rps",
                grep_hit="src/zm_mtg.py:2: return 'rps' if status == 429 else 'ok'",
                fail_msg="AssertionError: POST /meetings 429 retried as rps; daily create cap",
                first_old="    return 'rps' if status == 429 else 'ok'",
                first_new="    return 'rps_1s' if status == 429 else 'ok'",
                first_obs="patched 1s (still rps)",
                still_msg="AssertionError: daily meeting-create cap is not rps; billing owns it",
                reread_obs="POST /users/{id}/meetings 429 is account daily create, not REST rps",
                plan_change="Daily meeting create is a plan cap. Handoff ZM-DAY-3.",
                fix_new="    return 'handoff_ZM-DAY-3' if path == '/meetings' else 'ok'",
                fix_obs="ticket filed. still rps-classed",
                docs_url="https://developers.zoom.us/docs/api/rest/rate-limits/",
                docs_ok="Meeting create has a daily account cap separate from Light-rate REST.",
                docs_url2="https://developers.zoom.us/docs/api/rest/reference/zoom-api/methods/#operation/meetingCreate",
                docs_ok2="Sleep cannot mint daily creates. Handoff ZM-DAY-3.",
                outcome="Still rps-classed; daily create is billing — handoff ZM-DAY-3.",
                domain="zoom-meeting-create-daily-cap-vs-rest-rps",
                stack="Zoom REST meetings",
                seed="zoom-meeting-create-daily-handoff",
                residual="Sleep cannot mint daily meeting creates.",
                ticket="ZM-DAY-3",
                ticket_why="POST /meetings 429 daily create owned by billing-plat",
                coverage=83,
            ),
        ),
    ],
    "queue-backpressure-factory": [
        (
            _p(
                slug="rocketmq-pull-batch-vs-ack",
                goal="Shrink RocketMQ pull batch; do not raise consume timeout to hide lag.",
                plan="Read batch-as-timeout, try 300s, then batch=32 plus ack-before-pull.",
                mod="rmq_pull",
                test_fn="test_batch_not_timeout",
                src_body=(
                    "def tune(lag_ms):\n"
                    "    return {'consume_timeout_s': 120} if lag_ms > 5000 else {}\n"
                ),
                test_body=(
                    "def test_batch_not_timeout():\n"
                    "    t = tune(8000)\n"
                    "    assert t.get('pull_batch') == 32 and 'consume_timeout_s' not in t\n"
                ),
                grep_pat="consume_timeout_s|pull_batch|ack",
                grep_hit="src/rmq_pull.py:2: return {'consume_timeout_s': 120} if lag_ms > 5000",
                fail_msg="AssertionError: lag treated as timeout; pull batch 1024 held unacked",
                first_old="    return {'consume_timeout_s': 120} if lag_ms > 5000 else {}",
                first_new="    return {'consume_timeout_s': 300} if lag_ms > 5000 else {}",
                first_obs="patched 300s (still a timeout integer)",
                still_msg="AssertionError: timeout integer cannot shrink the unacked window",
                reread_obs="Default pull batch 1024; consumer lag is unacked, not timeout",
                plan_change="Pull 32 then ack before next pull. Timeout is not credit.",
                fix_new="    return {'pull_batch': 32, 'ack_before_next': True} if lag_ms > 5000 else {}",
                fix_obs="patched pull_batch=32",
                docs_url="https://rocketmq.apache.org/docs/sdk/02pull",
                docs_ok="Pull consumer batch size bounds unacked messages; timeout is separate.",
                docs_url2="https://rocketmq.apache.org/docs/bestPractice/01bestpractice",
                docs_ok2="Ack current batch before the next pull when OCR is slow.",
                outcome="Batch 32 plus ack drained lag. Timeout unused (success).",
                domain="rocketmq-pull-batch-unacked-vs-consume-timeout",
                stack="Apache RocketMQ pull consumer",
                seed="rocketmq-pull-batch-vs-ack",
                residual="Timeout integer is not broker credit.",
                coverage=86,
            ),
            _p(
                slug="solace-unacked-credit-handoff",
                goal="Do not raise Solace ACK timer to hide max-delivered-unacked credit.",
                plan="Read credit-as-timeout, try 60s ACK, then hand off broker credit.",
                mod="sol_crd",
                test_fn="test_credit_not_ack_timer",
                src_body=(
                    "def tune(blocked):\n"
                    "    return {'ack_timer_s': 30} if blocked else {}\n"
                ),
                test_body=(
                    "def test_credit_not_ack_timer():\n"
                    "    assert 'ack_timer_s' not in tune(True)\n"
                ),
                grep_pat="ack_timer_s|max-delivered-unacked|credit",
                grep_hit="src/sol_crd.py:2: return {'ack_timer_s': 30} if blocked else {}",
                fail_msg="AssertionError: credit stall slept ACK timer; flow is 1 unacked",
                first_old="    return {'ack_timer_s': 30} if blocked else {}",
                first_new="    return {'ack_timer_s': 60} if blocked else {}",
                first_obs="patched 60s (still a timeout integer)",
                still_msg="AssertionError: ACK timer cannot mint max-delivered-unacked-msgs-per-flow",
                reread_obs="max-delivered-unacked-msgs-per-flow=1; OCR holds the only credit",
                plan_change="Broker credit is not a timer. Handoff SOL-CRD-3.",
                fix_new="    return {'handoff': 'SOL-CRD-3'} if blocked else {}",
                fix_obs="ticket filed. still timer-classed",
                docs_url="https://docs.solace.com/Messaging/Guaranteed-Msg/Message-Delivery-Modes.htm",
                docs_ok="max-delivered-unacked-msgs-per-flow is broker credit, not ACK timeout.",
                docs_url2="https://docs.solace.com/API/API-Developer-Guide/Acknowledging-Messages.htm",
                docs_ok2="Sleep cannot mint flow credit. Handoff SOL-CRD-3.",
                outcome="Still timer-classed; flow credit is broker — handoff SOL-CRD-3.",
                domain="solace-max-delivered-unacked-credit-vs-ack-timer",
                stack="Solace SMF guaranteed flow",
                seed="solace-unacked-credit-handoff",
                residual="Timeout cannot mint broker credit.",
                ticket="SOL-CRD-3",
                ticket_why="unacked flow credit owned by solace-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="quartz-misfire-vs-threadcount",
                goal="Raise Quartz threadCount; do not stretch misfireThreshold to hide OCR lag.",
                plan="Read misfire-as-workers, try 600s, then threadCount=8 FIRE_NOW.",
                mod="qz_mf",
                test_fn="test_threadcount_not_misfire",
                src_body=(
                    "def tune(lag):\n"
                    "    return {'misfireThreshold': 600000} if lag else {}\n"
                ),
                test_body=(
                    "def test_threadcount_not_misfire():\n"
                    "    t = tune(True)\n"
                    "    assert t.get('threadCount') == 8 and 'misfireThreshold' not in t\n"
                ),
                grep_pat="misfireThreshold|threadCount|FIRE_NOW",
                grep_hit="src/qz_mf.py:2: return {'misfireThreshold': 600000} if lag else {}",
                fail_msg="AssertionError: lag stretched misfireThreshold; workers still 1",
                first_old="    return {'misfireThreshold': 600000} if lag else {}",
                first_new="    return {'misfireThreshold': 3600000} if lag else {}",
                first_obs="patched 3600s (still a timeout integer)",
                still_msg="AssertionError: threshold is not worker slots; OCR jobs still serialize",
                reread_obs="org.quartz.threadPool.threadCount=1; misfireThreshold is not concurrency",
                plan_change="threadCount=8 and misfire instruction FIRE_NOW. Threshold is not slots.",
                fix_new="    return {'threadCount': 8, 'misfire': 'FIRE_NOW'} if lag else {}",
                fix_obs="patched threadCount=8",
                docs_url="https://www.quartz-scheduler.org/documentation/quartz-2.3.0/configuration/ConfigThreadPool.html",
                docs_ok="threadCount is worker slots; misfireThreshold is how late is still on-time.",
                docs_url2="https://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/tutorial-lesson-04.html",
                docs_ok2="FIRE_NOW runs overdue OCR jobs; stretching threshold hides them.",
                outcome="threadCount=8 drained the misfire pile. Threshold unused (success).",
                domain="quartz-threadcount-vs-misfire-threshold-ms",
                stack="Quartz JDBC job store",
                seed="quartz-misfire-vs-threadcount",
                residual="misfireThreshold is not concurrency.",
                coverage=84,
            ),
            _p(
                slug="nservicebus-tx-recoverability-handoff",
                goal="Do not raise NServiceBus immediate retries to hide a transaction mode mismatch.",
                plan="Read retries-as-tx, try 10 immediate, then hand off transport tx.",
                mod="nsb_tx",
                test_fn="test_retries_not_tx_mode",
                src_body=(
                    "def tune(poison):\n"
                    "    return {'immediate_retries': 5} if poison else {}\n"
                ),
                test_body=(
                    "def test_retries_not_tx_mode():\n"
                    "    assert 'immediate_retries' not in tune(True)\n"
                ),
                grep_pat="immediate_retries|SendsAtomicWithReceive|Recoverability",
                grep_hit="src/nsb_tx.py:2: return {'immediate_retries': 5} if poison else {}",
                fail_msg="AssertionError: tx mismatch retried; Recoverability cannot mint atomic send",
                first_old="    return {'immediate_retries': 5} if poison else {}",
                first_new="    return {'immediate_retries': 10} if poison else {}",
                first_obs="patched 10 (still a retry integer)",
                still_msg="AssertionError: immediate retries cannot change TransportTransactionMode",
                reread_obs="SQL transport ReceiveOnly vs SendsAtomicWithReceive mismatch on OCR outbox",
                plan_change="Transaction mode is platform. Handoff NSB-TX-4.",
                fix_new="    return {'handoff': 'NSB-TX-4'} if poison else {}",
                fix_obs="ticket filed. still retry-classed",
                docs_url="https://docs.particular.net/nservicebus/transports/transactions",
                docs_ok="SendsAtomicWithReceive is transport transaction mode, not recoverability.",
                docs_url2="https://docs.particular.net/nservicebus/recoverability/",
                docs_ok2="Immediate retries cannot mint a transaction mode. Handoff NSB-TX-4.",
                outcome="Still retry-classed; tx mode is platform — handoff NSB-TX-4.",
                domain="nservicebus-transport-tx-mode-vs-immediate-retries",
                stack="NServiceBus SQL transport",
                seed="nservicebus-tx-recoverability-handoff",
                residual="Retry count is not transaction mode.",
                ticket="NSB-TX-4",
                ticket_why="ReceiveOnly vs SendsAtomicWithReceive owned by nsb-plat",
                coverage=84,
            ),
        ),
        (
            _p(
                slug="akka-streams-overflow-buffer",
                goal="Bound Akka Streams buffer; do not raise idle timeout to hide overflow.",
                plan="Read overflow-as-timeout, try 60s idle, then buffer=16 plus backpressure.",
                mod="akka_ov",
                test_fn="test_buffer_not_idle",
                src_body=(
                    "def tune(overflow):\n"
                    "    return {'idle_timeout_s': 30} if overflow else {}\n"
                ),
                test_body=(
                    "def test_buffer_not_idle():\n"
                    "    t = tune(True)\n"
                    "    assert t.get('buffer') == 16 and 'idle_timeout_s' not in t\n"
                ),
                grep_pat="idle_timeout_s|OverflowStrategy|buffer",
                grep_hit="src/akka_ov.py:2: return {'idle_timeout_s': 30} if overflow else {}",
                fail_msg="AssertionError: overflow slept idle timeout; buffer still unbounded",
                first_old="    return {'idle_timeout_s': 30} if overflow else {}",
                first_new="    return {'idle_timeout_s': 60} if overflow else {}",
                first_obs="patched 60s (still a timeout integer)",
                still_msg="AssertionError: idle timeout cannot bound OverflowStrategy.fail",
                reread_obs="source.buffer(Int.MaxValue, OverflowStrategy.fail) OOM on OCR",
                plan_change="buffer(16, backpressure). Idle timeout is not a queue bound.",
                fix_new="    return {'buffer': 16, 'overflow': 'backpressure'} if overflow else {}",
                fix_obs="patched buffer=16 backpressure",
                docs_url="https://doc.akka.io/docs/akka/current/stream/stream-rate.html",
                docs_ok="OverflowStrategy.backpressure bounds memory; idle timeout is a stall clock.",
                docs_url2="https://doc.akka.io/docs/akka/current/stream/operators/Source-or-Flow/buffer.html",
                docs_ok2="Use a finite buffer plus backpressure, not a longer idle clock.",
                outcome="Buffer 16 plus backpressure stopped OOM. Idle unused (success).",
                domain="akka-streams-buffer-backpressure-vs-idle-timeout",
                stack="Akka Streams OverflowStrategy",
                seed="akka-streams-overflow-buffer",
                residual="Idle timeout is not a queue bound.",
                coverage=82,
            ),
            _p(
                slug="spring-kafka-ack-mode-handoff",
                goal="Do not raise Spring Kafka idle-between-polls to hide MANUAL ack mode.",
                plan="Read ack-as-idle, try 30s, then hand off container ack mode.",
                mod="sk_ack",
                test_fn="test_ackmode_not_idle",
                src_body=(
                    "def tune(lag):\n"
                    "    return {'idleBetweenPolls': 10000} if lag else {}\n"
                ),
                test_body=(
                    "def test_ackmode_not_idle():\n"
                    "    assert 'idleBetweenPolls' not in tune(True)\n"
                ),
                grep_pat="idleBetweenPolls|AckMode.MANUAL|ContainerProperties",
                grep_hit="src/sk_ack.py:2: return {'idleBetweenPolls': 10000} if lag else {}",
                fail_msg="AssertionError: MANUAL ack lag slept idleBetweenPolls; ack never called",
                first_old="    return {'idleBetweenPolls': 10000} if lag else {}",
                first_new="    return {'idleBetweenPolls': 30000} if lag else {}",
                first_obs="patched 30s (still a timeout integer)",
                still_msg="AssertionError: idleBetweenPolls cannot ack MANUAL records",
                reread_obs="AckMode.MANUAL requires acknowledgment.acknowledge(); poll idle is not ack",
                plan_change="MANUAL ack is an application contract. Handoff SK-ACK-2.",
                fix_new="    return {'handoff': 'SK-ACK-2'} if lag else {}",
                fix_obs="ticket filed. still idle-classed",
                docs_url="https://docs.spring.io/spring-kafka/reference/kafka/receiving-messages/listener-ack.html",
                docs_ok="AckMode.MANUAL needs explicit ack; idleBetweenPolls is not that.",
                docs_url2="https://docs.spring.io/spring-kafka/reference/kafka/receiving-messages/message-listener-container.html",
                docs_ok2="Container ack mode is platform. Handoff SK-ACK-2.",
                outcome="Still idle-classed; MANUAL ack is platform — handoff SK-ACK-2.",
                domain="spring-kafka-manual-ack-vs-idle-between-polls",
                stack="Spring Kafka listener container",
                seed="spring-kafka-ack-mode-handoff",
                residual="Idle poll is not MANUAL ack.",
                ticket="SK-ACK-2",
                ticket_why="AckMode.MANUAL owned by kafka-plat",
                coverage=82,
            ),
        ),
    ],
    "csv-excel-ingest-factory": [
        (
            _p(
                slug="csv-us-rs-separators",
                goal="Parse ASCII US/RS (0x1F/0x1E) invoice files; do not split on comma/newline.",
                plan="Read US-as-comma, try pipe, then delimiter=0x1F lineterminator=0x1E.",
                mod="csv_usrs",
                test_fn="test_us_rs_dialect",
                src_body=(
                    "def parse(raw):\n"
                    "    return [row.split(',') for row in raw.split('\\n')]\n"
                ),
                test_body=(
                    "def test_us_rs_dialect():\n"
                    "    raw = 'inv\\x1famt\\x1eA1\\x1f10.00\\x1e'\n"
                    "    rows = parse(raw)\n"
                    "    assert rows == [['inv', 'amt'], ['A1', '10.00']]\n"
                ),
                grep_pat="split\\(','|0x1f|lineterminator",
                grep_hit="src/csv_usrs.py:2: return [row.split(',') for row in raw.split('\\\\n')]",
                fail_msg="AssertionError: US/RS file parsed as one comma-row; fields glued",
                first_old="    return [row.split(',') for row in raw.split('\\n')]",
                first_new="    return [row.split('|') for row in raw.split('\\n')]",
                first_obs="patched pipe (still ASCII-line CSV, not US/RS)",
                still_msg="AssertionError: pipe still ignores 0x1F fields and 0x1E records",
                reread_obs="EDI dump uses UNIT SEPARATOR 0x1F and RECORD SEPARATOR 0x1E",
                plan_change="csv.reader delimiter='\\x1f' lineterminator='\\x1e'. Not comma/newline.",
                fix_new=(
                    "    import csv, io\n"
                    "    return list(csv.reader(io.StringIO(raw), delimiter='\\x1f',"
                    " lineterminator='\\x1e'))"
                ),
                fix_obs="patched US/RS dialect",
                docs_url="https://datatracker.ietf.org/doc/html/rfc4180",
                docs_ok="RFC4180 is comma/CRLF. This dump is US/RS (ASCII 31/30), not quoted-newline.",
                docs_url2="https://www.unicode.org/charts/PDF/U0000.pdf",
                docs_ok2="U+001F UNIT SEPARATOR, U+001E RECORD SEPARATOR are the dialect.",
                outcome="US/RS dialect split invoice fields. Comma unused (success).",
                domain="csv-ascii-unit-record-separator-vs-comma-newline",
                stack="Python csv US/RS dialect",
                seed="csv-us-rs-separators",
                residual="Not RFC4180 quoted-newline.",
                coverage=87,
            ),
            _p(
                slug="stata-dta-binary-handoff",
                goal="Do not parse Stata .dta as CSV text.",
                plan="Read dta-as-csv, try latin1, then hand off binary reader.",
                mod="dta_bin",
                test_fn="test_dta_not_csv",
                src_body=(
                    "def load(path):\n"
                    "    return open(path, newline='').read().split(',')\n"
                ),
                test_body=(
                    "def test_dta_not_csv():\n"
                    "    assert load('invoices.dta') != open('invoices.dta').read().split(',')\n"
                ),
                grep_pat="\\.dta|read\\(\\).*split|stata",
                grep_hit="src/dta_bin.py:2: return open(path, newline='').read().split(',')",
                fail_msg="AssertionError: <stata_dta> magic parsed as CSV; binary header lost",
                first_old="    return open(path, newline='').read().split(',')",
                first_new="    return open(path, encoding='latin1').read().split(',')",
                first_obs="patched latin1 (still text split, still not .dta)",
                still_msg="AssertionError: latin1 cannot decode Stata 117 binary header",
                reread_obs="<stata_dta><header><release>117 needs pd.read_stata, not csv",
                plan_change="Binary .dta is pandas-stata. Handoff STATA-DTA-2.",
                fix_new="    return {'handoff': 'STATA-DTA-2'}",
                fix_obs="ticket filed. still csv-split",
                docs_url="https://www.stata.com/help.cgi?dta",
                docs_ok="Stata .dta is a binary format with a typed header, not CSV.",
                docs_url2="https://pandas.pydata.org/docs/reference/api/pandas.read_stata.html",
                docs_ok2="Need pandas.read_stata. Handoff STATA-DTA-2.",
                outcome="Still csv-split; .dta is binary — handoff STATA-DTA-2.",
                domain="stata-dta-binary-header-vs-csv-text",
                stack="Stata 117 .dta",
                seed="stata-dta-binary-handoff",
                residual="latin1 is not a Stata reader.",
                ticket="STATA-DTA-2",
                ticket_why=".dta binary ingest owned by stats-plat",
                coverage=87,
            ),
        ),
        (
            _p(
                slug="xlsx-cse-array-vs-cached",
                goal="Read Excel CSE array-formula spill, not only the cached formula cell.",
                plan="Read cache-as-spill, try t=str, then calcChain spilled range.",
                mod="xlsx_cse",
                test_fn="test_array_spill_range",
                src_body=(
                    "def amounts(ws):\n"
                    "    return [c.cached for c in ws.formula_cells()]\n"
                ),
                test_body=(
                    "def test_array_spill_range():\n"
                    "    assert amounts(ws) == [10, 20, 30]\n"
                ),
                grep_pat="cached|array_formula|spill",
                grep_hit="src/xlsx_cse.py:2: return [c.cached for c in ws.formula_cells()]",
                fail_msg="AssertionError: [10] == [10, 20, 30]; CSE spill below B2 ignored",
                first_old="    return [c.cached for c in ws.formula_cells()]",
                first_new="    return [c.cached or c.t_str for c in ws.formula_cells()]",
                first_obs="patched t=str cache (still one cell, not the spill)",
                still_msg="AssertionError: t=str still misses B3:B4 of the CSE array",
                reread_obs="f=\"=B2:B4*1\" t=array; spilled values live in calcChain, not one cached",
                plan_change="Walk the CSE spilled range via calcChain. Cached formula cell is not the spill.",
                fix_new="    return list(ws.cse_spill_values('B2:B4'))",
                fix_obs="patched CSE spill range",
                docs_url="https://learn.microsoft.com/en-us/office/client-developer/excel/excel-glossary#array-formula",
                docs_ok="Legacy CSE array formulas occupy a range; cache on the top-left is incomplete.",
                docs_url2="https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/",
                docs_ok2="calcChain lists each spilled cell. Do not ingest only the formula cache.",
                outcome="CSE spill B2:B4 ingested 3 amounts. Cache unused (success).",
                domain="xlsx-cse-array-formula-spill-vs-cached-cell",
                stack="OOXML worksheet+calcChain",
                seed="xlsx-cse-array-vs-cached",
                residual="Not Kingsoft .et, not quoted-newline.",
                coverage=85,
            ),
            _p(
                slug="spss-sav-binary-handoff",
                goal="Do not parse SPSS .sav as xlsx ZIP.",
                plan="Read sav-as-xlsx, try zipfile, then hand off sav reader.",
                mod="sav_bin",
                test_fn="test_sav_not_xlsx",
                src_body=(
                    "def load(path):\n"
                    "    import zipfile\n"
                    "    return zipfile.ZipFile(path).namelist()\n"
                ),
                test_body=(
                    "def test_sav_not_xlsx():\n"
                    "    assert not str(load('invoices.sav')).startswith('xl/')\n"
                ),
                grep_pat="ZipFile|\\.sav|pyreadstat",
                grep_hit="src/sav_bin.py:3: return zipfile.ZipFile(path).namelist()",
                fail_msg="AssertionError: $FL2 SPSS magic opened as ZIP; BadZipFile swallowed",
                first_old="    return zipfile.ZipFile(path).namelist()",
                first_new="    return zipfile.ZipFile(path, mode='r').namelist() or ['xl/worksheets']",
                first_obs="patched default sheet (still ZIP, still not .sav)",
                still_msg="AssertionError: forcing xl/ paths cannot decode SPSS sav",
                reread_obs="$FL2 header is SPSS portable; need pyreadstat.read_sav",
                plan_change="Binary .sav is stats-plat. Handoff SPSS-SAV-3.",
                fix_new="    return {'handoff': 'SPSS-SAV-3'}",
                fix_obs="ticket filed. still zip-classed",
                docs_url="https://www.ibm.com/docs/en/spss-statistics/29.0.0?topic=files-saving-data-file",
                docs_ok="SPSS .sav is a binary system file, not OOXML.",
                docs_url2="https://ofajardo.github.io/pyreadstat_documentation/_build/html/index.html",
                docs_ok2="Need pyreadstat.read_sav. Handoff SPSS-SAV-3. Not Kingsoft .et.",
                outcome="Still zip-classed; .sav is binary — handoff SPSS-SAV-3.",
                domain="spss-sav-binary-vs-xlsx-zip",
                stack="SPSS .sav $FL2",
                seed="spss-sav-binary-handoff",
                residual="Not Kingsoft WPS .et.",
                ticket="SPSS-SAV-3",
                ticket_why=".sav binary ingest owned by stats-plat",
                coverage=85,
            ),
        ),
        (
            _p(
                slug="xlsx-alternatecontent-choice",
                goal="Read mc:AlternateContent Choice cell values, not the empty Fallback.",
                plan="Read Fallback-as-value, try Requires=x14, then Choice a:t text.",
                mod="xlsx_ac",
                test_fn="test_choice_not_fallback",
                src_body=(
                    "def cell_text(el):\n"
                    "    fb = el.find('.//{mc}Fallback')\n"
                    "    return fb.text if fb is not None else ''\n"
                ),
                test_body=(
                    "def test_choice_not_fallback():\n"
                    "    assert cell_text(el) == 'INV-9'\n"
                ),
                grep_pat="AlternateContent|Fallback|Choice",
                grep_hit="src/xlsx_ac.py:2: fb = el.find('.//{mc}Fallback')",
                fail_msg="AssertionError: '' == 'INV-9'; Fallback empty, Choice holds a:t",
                first_old="    return fb.text if fb is not None else ''",
                first_new="    return fb.get('Requires') or ''",
                first_obs="patched Requires attr (still Fallback, still empty)",
                still_msg="AssertionError: Requires=x14 is a namespace hint, not the invoice id",
                reread_obs="mc:Choice Requires=x14 contains a:t INV-9; Fallback is empty for Excel 2007",
                plan_change="Prefer mc:Choice text. Fallback is the compatibility empty node.",
                fix_new=(
                    "    ch = el.find('.//{mc}Choice//{a}t')\n"
                    "    return ch.text if ch is not None else ''"
                ),
                fix_obs="patched Choice a:t",
                docs_url="https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.markupcompatibility.alternatecontent",
                docs_ok="AlternateContent Choice is the real markup; Fallback is for old clients.",
                docs_url2="https://learn.microsoft.com/en-us/office/open-xml/spreadsheets",
                docs_ok2="Invoice id lives in Choice a:t, not the empty Fallback.",
                outcome="Choice a:t recovered INV-9. Fallback unused (success).",
                domain="xlsx-markup-compatibility-choice-vs-fallback",
                stack="OOXML mc:AlternateContent",
                seed="xlsx-alternatecontent-choice",
                residual="Not quoted-newline, not WPS .et.",
                coverage=83,
            ),
            _p(
                slug="rds-serialize-handoff",
                goal="Do not parse R .rds as CSV.",
                plan="Read rds-as-csv, try gzip, then hand off readRDS.",
                mod="rds_bin",
                test_fn="test_rds_not_csv",
                src_body=(
                    "def load(path):\n"
                    "    return open(path, 'rb').read().split(b',')\n"
                ),
                test_body=(
                    "def test_rds_not_csv():\n"
                    "    assert load('invoices.rds')[:1] != [open('invoices.rds','rb').read()]\n"
                ),
                grep_pat="\\.rds|readRDS|X\\n",
                grep_hit="src/rds_bin.py:2: return open(path, 'rb').read().split(b',')",
                fail_msg="AssertionError: X\\n RDS magic split on comma; SEXP lost",
                first_old="    return open(path, 'rb').read().split(b',')",
                first_new="    import gzip\n    return gzip.open(path).read().split(b',')",
                first_obs="patched gzip (still comma split, still not readRDS)",
                still_msg="AssertionError: gzip+comma cannot decode RDS SEXP",
                reread_obs="RDS starts with X\\n or gzip SEXP; need rpy2/pyreadr",
                plan_change="Binary .rds is stats-plat. Handoff RDS-SER-2.",
                fix_new="    return {'handoff': 'RDS-SER-2'}",
                fix_obs="ticket filed. still csv-split",
                docs_url="https://cran.r-project.org/doc/manuals/r-release/R-data.html#XDR-and-binary-serialization",
                docs_ok="RDS is R serialization, not CSV. gzip wrapping does not make it text.",
                docs_url2="https://www.rdocumentation.org/packages/base/versions/3.6.2/topics/readRDS",
                docs_ok2="Need readRDS. Handoff RDS-SER-2.",
                outcome="Still csv-split; .rds is SEXP — handoff RDS-SER-2.",
                domain="r-rds-serialize-vs-csv-text",
                stack="R RDS serialization",
                seed="rds-serialize-handoff",
                residual="gzip is not readRDS.",
                ticket="RDS-SER-2",
                ticket_why=".rds SEXP ingest owned by stats-plat",
                coverage=83,
            ),
        ),
    ],
    "websocket-reconnect-factory": [
        (
            _p(
                slug="ws-1007-utf8-vs-1006",
                goal="Treat WebSocket 1007 invalid UTF-8 as protocol, not 1006 reconnect.",
                plan="Read 1007-as-1006, try binary opcode, then transcode payload.",
                mod="ws_1007",
                test_fn="test_1007_not_reconnect",
                src_body=(
                    "def on_close(code, payload):\n"
                    "    return 'reconnect' if code in (1006, 1007) else 'ok'\n"
                ),
                test_body=(
                    "def test_1007_not_reconnect():\n"
                    "    assert on_close(1007, b'\\xff') == 'transcode'\n"
                ),
                grep_pat="1007|1006|invalid UTF-8",
                grep_hit="src/ws_1007.py:2: return 'reconnect' if code in (1006, 1007) else 'ok'",
                fail_msg="AssertionError: 1007 invalid UTF-8 reconnect-looped the same bytes",
                first_old="    return 'reconnect' if code in (1006, 1007) else 'ok'",
                first_new="    return 'reconnect_binary' if code == 1007 else 'ok'",
                first_obs="patched binary reconnect (still a reconnect loop)",
                still_msg="AssertionError: binary opcode still resends invalid UTF-8 text frames",
                reread_obs="RFC6455 1007 is invalid payload data; 1006 is abnormal close",
                plan_change="Transcode payload to UTF-8. Do not reconnect-loop 1007 as 1006.",
                fix_new="    return 'transcode' if code == 1007 else ('reconnect' if code == 1006 else 'ok')",
                fix_obs="patched 1007 transcode",
                docs_url="https://datatracker.ietf.org/doc/html/rfc6455#section-7.4.1",
                docs_ok="1007 invalid frame payload data; 1006 reserved abnormal closure.",
                docs_url2="https://www.rfc-editor.org/rfc/rfc6455.html#section-8.1",
                docs_ok2="Text frames must be UTF-8. Transcode; do not reconnect the same bytes.",
                outcome="1007 transcoded invoice text. Reconnect unused (success).",
                domain="websocket-1007-invalid-utf8-vs-1006-abnormal",
                stack="RFC6455 close codes",
                seed="ws-1007-utf8-vs-1006",
                residual="Not cookie-replay.",
                coverage=86,
            ),
            _p(
                slug="caddy-flush-interval-handoff",
                goal="Do not treat Caddy reverse_proxy websocket flush_interval as ping.",
                plan="Read flush-as-ping, try ping 10s, then hand off proxy flush.",
                mod="caddy_fl",
                test_fn="test_flush_not_ping",
                src_body=(
                    "def tune(stall):\n"
                    "    return {'ping_s': 15} if stall else {}\n"
                ),
                test_body=(
                    "def test_flush_not_ping():\n"
                    "    assert 'ping_s' not in tune(True)\n"
                ),
                grep_pat="flush_interval|ping_s|reverse_proxy",
                grep_hit="src/caddy_fl.py:2: return {'ping_s': 15} if stall else {}",
                fail_msg="AssertionError: proxy flush stall slept ping; flush_interval still 0",
                first_old="    return {'ping_s': 15} if stall else {}",
                first_new="    return {'ping_s': 10} if stall else {}",
                first_obs="patched ping 10s (still client ping, not proxy flush)",
                still_msg="AssertionError: ping cannot set reverse_proxy flush_interval -1",
                reread_obs="Caddy buffers WS frames until flush_interval; 0 means block on buffer",
                plan_change="flush_interval is Caddy proxy. Handoff CADDY-FLUSH-2.",
                fix_new="    return {'handoff': 'CADDY-FLUSH-2'} if stall else {}",
                fix_obs="ticket filed. still ping-classed",
                docs_url="https://caddyserver.com/docs/caddyfile/directives/reverse_proxy",
                docs_ok="flush_interval -1 flushes immediately; 0 buffers. Not a WebSocket ping.",
                docs_url2="https://caddyserver.com/docs/caddyfile/directives/reverse_proxy#streaming",
                docs_ok2="Proxy buffering is platform. Handoff CADDY-FLUSH-2. Not cookie-replay.",
                outcome="Still ping-classed; flush_interval is Caddy — handoff CADDY-FLUSH-2.",
                domain="caddy-reverse-proxy-flush-interval-vs-ws-ping",
                stack="Caddy reverse_proxy websocket",
                seed="caddy-flush-interval-handoff",
                residual="Ping cannot set proxy flush.",
                ticket="CADDY-FLUSH-2",
                ticket_why="flush_interval owned by edge-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="signalr-negotiate-vs-direct-ws",
                goal="POST SignalR /negotiate before WebSocket; do not connect the hub URL directly.",
                plan="Read skip-negotiate, try /websocket suffix, then connectionToken transport.",
                mod="sig_neg",
                test_fn="test_negotiate_before_ws",
                src_body=(
                    "def connect(hub):\n"
                    "    return {'url': hub.replace('http', 'ws')}\n"
                ),
                test_body=(
                    "def test_negotiate_before_ws():\n"
                    "    c = connect('http://inv/hub')\n"
                    "    assert c.get('token') and c['url'].endswith('?id=') or 'connectionToken' in str(c)\n"
                ),
                grep_pat="negotiate|connectionToken|skipNegotiate",
                grep_hit="src/sig_neg.py:2: return {'url': hub.replace('http', 'ws')}",
                fail_msg="AssertionError: direct ws://inv/hub 404; negotiate never called",
                first_old="    return {'url': hub.replace('http', 'ws')}",
                first_new="    return {'url': hub.replace('http', 'ws') + '/websocket'}",
                first_obs="patched /websocket suffix (still skipNegotiate)",
                still_msg="AssertionError: /websocket still 404 without negotiate connectionToken",
                reread_obs="ASP.NET SignalR requires POST /negotiate for connectionToken + transport",
                plan_change="POST /negotiate, then WS with connectionToken. Direct hub WS is not a transport.",
                fix_new=(
                    "    n = post_negotiate(hub)\n"
                    "    return {'url': n['url'], 'token': n['connectionToken']}"
                ),
                fix_obs="patched negotiate+token",
                docs_url="https://learn.microsoft.com/en-us/aspnet/signalr/overview/guide-to-the-api/hubs-api-guide-javascript-client",
                docs_ok="The JS client negotiates first; skipNegotiate is only for Azure SignalR.",
                docs_url2="https://learn.microsoft.com/en-us/aspnet/core/signalr/javascript-client",
                docs_ok2="connectionToken comes from negotiate. Direct WS 404s the hub.",
                outcome="Negotiate token connected the hub. Direct WS unused (success).",
                domain="signalr-negotiate-connectiontoken-vs-direct-websocket",
                stack="ASP.NET SignalR negotiate",
                seed="signalr-negotiate-vs-direct-ws",
                residual="Not cookie-replay.",
                coverage=85,
            ),
            _p(
                slug="soketi-pusher-ping-handoff",
                goal="Do not treat Soketi pusher pingInterval as nginx read timeout.",
                plan="Read ping-as-nginx, try ping 20s, then hand off pusher protocol.",
                mod="sok_ping",
                test_fn="test_pusher_ping_not_nginx",
                src_body=(
                    "def tune(drop):\n"
                    "    return {'nginx_read_s': 60} if drop else {}\n"
                ),
                test_body=(
                    "def test_pusher_ping_not_nginx():\n"
                    "    assert 'nginx_read_s' not in tune(True)\n"
                ),
                grep_pat="pingInterval|nginx_read_s|pusher",
                grep_hit="src/sok_ping.py:2: return {'nginx_read_s': 60} if drop else {}",
                fail_msg="AssertionError: Soketi pingInterval 25s dropped; nginx read is not pusher",
                first_old="    return {'nginx_read_s': 60} if drop else {}",
                first_new="    return {'nginx_read_s': 120} if drop else {}",
                first_obs="patched nginx 120s (still the proxy clock)",
                still_msg="AssertionError: nginx cannot emit pusher protocol pings",
                reread_obs="Soketi uses pusher pingInterval 25s; client must pong; nginx idle is separate",
                plan_change="Pusher ping is app protocol. Handoff SOK-PING-3.",
                fix_new="    return {'handoff': 'SOK-PING-3'} if drop else {}",
                fix_obs="ticket filed. still nginx-classed",
                docs_url="https://docs.soketi.app/getting-started/configuration",
                docs_ok="Soketi pingInterval/pongTimeout are pusher protocol, not nginx.",
                docs_url2="https://pusher.com/docs/channels/library_auth_reference/pusher-websockets-protocol/",
                docs_ok2="Client must answer pusher pings. Handoff SOK-PING-3. Not cookie-replay.",
                outcome="Still nginx-classed; pusher ping is app — handoff SOK-PING-3.",
                domain="soketi-pusher-pinginterval-vs-nginx-read-timeout",
                stack="Soketi pusher protocol",
                seed="soketi-pusher-ping-handoff",
                residual="nginx idle is not pusher ping.",
                ticket="SOK-PING-3",
                ticket_why="pusher pingInterval owned by realtime-plat",
                coverage=85,
            ),
        ),
        (
            _p(
                slug="graphql-transport-ws-pong",
                goal="Answer graphql-transport-ws ping with pong; do not reuse graphql-ws ka.",
                plan="Read ka-as-pong, try sending ka, then pong type on ping.",
                mod="gtws_p",
                test_fn="test_pong_not_ka",
                src_body=(
                    "def on_msg(msg):\n"
                    "    return {'type': 'ka'} if msg.get('type') == 'ping' else None\n"
                ),
                test_body=(
                    "def test_pong_not_ka():\n"
                    "    assert on_msg({'type': 'ping'}) == {'type': 'pong'}\n"
                ),
                grep_pat="graphql-transport-ws|pong|type.: .ka",
                grep_hit="src/gtws_p.py:2: return {'type': 'ka'} if msg.get('type') == 'ping'",
                fail_msg="AssertionError: {'type': 'ka'} == {'type': 'pong'}; server closed 4401",
                first_old="    return {'type': 'ka'} if msg.get('type') == 'ping' else None",
                first_new="    return {'type': 'keep_alive'} if msg.get('type') == 'ping' else None",
                first_obs="patched keep_alive string (still graphql-ws, not pong)",
                still_msg="AssertionError: graphql-ws ka is not graphql-transport-ws pong",
                reread_obs="graphql-transport-ws (subscriptions-transport successor) uses ping/pong",
                plan_change="On type=ping reply type=pong. graphql-ws ka is a different protocol.",
                fix_new="    return {'type': 'pong'} if msg.get('type') == 'ping' else None",
                fix_obs="patched pong",
                docs_url="https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md",
                docs_ok="graphql-transport-ws ping must be answered with pong or the socket dies.",
                docs_url2="https://github.com/apollographql/subscriptions-transport-ws/blob/master/PROTOCOL.md",
                docs_ok2="Old graphql-ws ka is not valid on graphql-transport-ws.",
                outcome="pong answered ping. ka unused (success).",
                domain="graphql-transport-ws-pong-vs-graphql-ws-ka",
                stack="graphql-transport-ws PROTOCOL",
                seed="graphql-transport-ws-pong",
                residual="Not cookie-replay; not graphql-ws init clone.",
                coverage=84,
            ),
            _p(
                slug="fastly-compute-ws-handoff",
                goal="Do not treat Fastly Compute WebSocket backend timeout as client ping.",
                plan="Read backend-as-ping, try ping 5s, then hand off Compute timeout.",
                mod="fly_ws",
                test_fn="test_backend_not_ping",
                src_body=(
                    "def tune(drop):\n"
                    "    return {'client_ping_s': 5} if drop else {}\n"
                ),
                test_body=(
                    "def test_backend_not_ping():\n"
                    "    assert 'client_ping_s' not in tune(True)\n"
                ),
                grep_pat="first_byte_timeout|client_ping_s|compute",
                grep_hit="src/fly_ws.py:2: return {'client_ping_s': 5} if drop else {}",
                fail_msg="AssertionError: Compute first_byte_timeout 15s dropped WS; ping unused",
                first_old="    return {'client_ping_s': 5} if drop else {}",
                first_new="    return {'client_ping_s': 10} if drop else {}",
                first_obs="patched ping 10s (still client, not backend timeout)",
                still_msg="AssertionError: client ping cannot raise Compute first_byte_timeout",
                reread_obs="Fastly Compute WebSocket backend first_byte_timeout 15s kills idle OCR",
                plan_change="Backend timeout is Fastly. Handoff FLY-WS-4.",
                fix_new="    return {'handoff': 'FLY-WS-4'} if drop else {}",
                fix_obs="ticket filed. still ping-classed",
                docs_url="https://www.fastly.com/documentation/guides/concepts/compute-edge-timeouts/",
                docs_ok="Compute backend first_byte_timeout applies to WebSocket upgrades.",
                docs_url2="https://www.fastly.com/documentation/guides/full-site-delivery/websockets/",
                docs_ok2="Client ping cannot change Compute timeouts. Handoff FLY-WS-4.",
                outcome="Still ping-classed; Compute timeout is Fastly — handoff FLY-WS-4.",
                domain="fastly-compute-websocket-backend-timeout-vs-client-ping",
                stack="Fastly Compute WebSocket",
                seed="fastly-compute-ws-handoff",
                residual="Not cookie-replay.",
                ticket="FLY-WS-4",
                ticket_why="first_byte_timeout owned by edge-plat",
                coverage=84,
            ),
        ),
    ],
    "email-webhook-retry-factory": [
        (
            _p(
                slug="mailersend-id-plus-type",
                goal="Dedupe MailerSend webhooks on (data.id, type), not email address.",
                plan="Read email-as-pk, try message_id-only, then (data.id, type).",
                mod="ms_id",
                test_fn="test_id_plus_type",
                src_body=(
                    "def upsert(ev):\n"
                    "    return ev['data']['email']\n"
                ),
                test_body=(
                    "def test_id_plus_type():\n"
                    "    a = {'data': {'id': 'm1', 'email': 'a@b'}, 'type': 'delivered'}\n"
                    "    b = {'data': {'id': 'm1', 'email': 'a@b'}, 'type': 'opened'}\n"
                    "    assert upsert(a) != upsert(b)\n"
                ),
                grep_pat="data.id|type|email",
                grep_hit="src/ms_id.py:2: return ev['data']['email']",
                fail_msg="AssertionError: delivered+opened collapsed; email is not event pk",
                first_old="    return ev['data']['email']",
                first_new="    return ev['data']['id']",
                first_obs="patched message id (collides across delivered vs opened)",
                still_msg="AssertionError: same data.id delivered+opened still one row",
                reread_obs="MailerSend activity.sent vs opened share data.id; type distinguishes",
                plan_change="PK (data.id, type). Email is the recipient, not the event.",
                fix_new="    return (ev['data']['id'], ev['type'])",
                fix_obs="patched (id, type)",
                docs_url="https://developers.mailersend.com/api/v1/webhooks.html",
                docs_ok="Webhook payload has data.id plus type; retries replay the same pair.",
                docs_url2="https://www.mailersend.com/help/email-activity-webhooks",
                docs_ok2="delivered and opened are different types on one message id.",
                outcome="(id, type) stored both events. Email unused (success).",
                domain="mailersend-webhook-data-id-plus-type",
                stack="MailerSend activity webhooks",
                seed="mailersend-id-plus-type",
                residual="Not invoice-row-dup.",
                coverage=86,
            ),
            _p(
                slug="acoustic-mailing-id-handoff",
                goal="Do not treat Acoustic mailingId as a unique webhook event.",
                plan="Read mailing-as-event, try mailingId+email, then hand off campaign id.",
                mod="aco_ml",
                test_fn="test_mailing_not_event",
                src_body=(
                    "def pk(ev):\n"
                    "    return ev['mailingId']\n"
                ),
                test_body=(
                    "def test_mailing_not_event():\n"
                    "    assert pk({'mailingId': '9', 'eventId': 'e1'}) != '9'\n"
                ),
                grep_pat="mailingId|eventId|Silverpop",
                grep_hit="src/aco_ml.py:2: return ev['mailingId']",
                fail_msg="AssertionError: campaign mailingId collapsed 400 opens into one row",
                first_old="    return ev['mailingId']",
                first_new="    return ev['mailingId'] + ev.get('email', '')",
                first_obs="patched mailing+email (still campaign grain, not event)",
                still_msg="AssertionError: mailing+email still one row per recipient per campaign",
                reread_obs="Acoustic/Silverpop mailingId is the campaign; eventId is the activity",
                plan_change="mailingId is campaign grain. Handoff ACO-MAIL-4.",
                fix_new="    return {'handoff': 'ACO-MAIL-4'}",
                fix_obs="ticket filed. still mailing-grained",
                docs_url="https://developer.goacoustic.com/acoustic-campaign/reference/webhooks",
                docs_ok="mailingId identifies the campaign; events need eventId.",
                docs_url2="https://help.goacoustic.com/hc/en-us/articles/360043879771",
                docs_ok2="Campaign grain is marketing-plat. Handoff ACO-MAIL-4. Not invoice-row-dup.",
                outcome="Still mailing-grained; campaign id is marketing — handoff ACO-MAIL-4.",
                domain="acoustic-campaign-mailingid-vs-eventid",
                stack="Acoustic Campaign webhooks",
                seed="acoustic-mailing-id-handoff",
                residual="mailingId is not an event pk.",
                ticket="ACO-MAIL-4",
                ticket_why="mailingId campaign grain owned by marketing-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="mailerlite-event-plus-email-id",
                goal="Dedupe MailerLite webhooks on (event, email.id), not subscriber_id.",
                plan="Read subscriber-as-pk, try campaign_id, then (event, email.id).",
                mod="ml_ev",
                test_fn="test_event_plus_email_id",
                src_body=(
                    "def upsert(ev):\n"
                    "    return ev['subscriber']['id']\n"
                ),
                test_body=(
                    "def test_event_plus_email_id():\n"
                    "    a = {'event': 'clicked', 'email': {'id': 'e1'}, 'subscriber': {'id': 's'}}\n"
                    "    b = {'event': 'opened', 'email': {'id': 'e1'}, 'subscriber': {'id': 's'}}\n"
                    "    assert upsert(a) != upsert(b)\n"
                ),
                grep_pat="subscriber.id|email.id|event",
                grep_hit="src/ml_ev.py:2: return ev['subscriber']['id']",
                fail_msg="AssertionError: clicked+opened collapsed on subscriber_id",
                first_old="    return ev['subscriber']['id']",
                first_new="    return ev.get('campaign_id') or ev['subscriber']['id']",
                first_obs="patched campaign_id (still one row per send, not per event)",
                still_msg="AssertionError: campaign_id still collapses clicked vs opened",
                reread_obs="MailerLite webhook event plus email.id is the activity; subscriber is the person",
                plan_change="PK (event, email.id). Subscriber is the person, not the activity.",
                fix_new="    return (ev['event'], ev['email']['id'])",
                fix_obs="patched (event, email.id)",
                docs_url="https://developers.mailerlite.com/docs/#webhooks",
                docs_ok="Webhooks include event name and email object id; retries replay the pair.",
                docs_url2="https://www.mailerlite.com/help/webhooks",
                docs_ok2="clicked and opened share a subscriber and can share an email.id.",
                outcome="(event, email.id) stored both activities. Subscriber unused (success).",
                domain="mailerlite-webhook-event-plus-email-id",
                stack="MailerLite webhooks",
                seed="mailerlite-event-plus-email-id",
                residual="Not invoice-row-dup.",
                coverage=84,
            ),
            _p(
                slug="adobe-campaign-broadlog-handoff",
                goal="Do not treat Adobe Campaign broadLogId as a tracking event.",
                plan="Read broadlog-as-track, try broadLog+delivery, then hand off tracking log.",
                mod="ac_bl",
                test_fn="test_broadlog_not_tracking",
                src_body=(
                    "def pk(ev):\n"
                    "    return ev['broadLogId']\n"
                ),
                test_body=(
                    "def test_broadlog_not_tracking():\n"
                    "    assert pk({'broadLogId': 'b1', 'trackingLogId': 't1'}) != 'b1'\n"
                ),
                grep_pat="broadLogId|trackingLogId|nmsBroadLog",
                grep_hit="src/ac_bl.py:2: return ev['broadLogId']",
                fail_msg="AssertionError: opens collapsed on broadLogId; trackingLogId unused",
                first_old="    return ev['broadLogId']",
                first_new="    return ev['broadLogId'] + ':' + ev.get('deliveryId', '')",
                first_obs="patched broadLog+delivery (still send grain, not tracking)",
                still_msg="AssertionError: delivery grain still one row per send",
                reread_obs="nmsBroadLog is the send; nmsTrackingLogRcp is the open/click",
                plan_change="broadLog is send grain. Handoff ADOBE-BL-3.",
                fix_new="    return {'handoff': 'ADOBE-BL-3'}",
                fix_obs="ticket filed. still broadlog-grained",
                docs_url="https://experienceleague.adobe.com/en/docs/campaign-classic/using/sending-messages/tracking-messages/about-message-tracking",
                docs_ok="broadLog is the delivery occurrence; tracking logs are separate rows.",
                docs_url2="https://experienceleague.adobe.com/en/docs/campaign-classic/using/configuring-campaign-classic/schema-reference/database-mapping",
                docs_ok2="trackingLog is campaign-plat. Handoff ADOBE-BL-3. Not invoice-row-dup.",
                outcome="Still broadlog-grained; tracking is campaign — handoff ADOBE-BL-3.",
                domain="adobe-campaign-broadlog-vs-trackinglog",
                stack="Adobe Campaign Classic nmsBroadLog",
                seed="adobe-campaign-broadlog-handoff",
                residual="broadLogId is not a click.",
                ticket="ADOBE-BL-3",
                ticket_why="nmsTrackingLogRcp owned by campaign-plat",
                coverage=84,
            ),
        ),
        (
            _p(
                slug="scaleway-tem-id-plus-event",
                goal="Dedupe Scaleway Transactional Email webhooks on (message_id, event_type).",
                plan="Read message-as-pk, try event_type-only, then (message_id, event_type).",
                mod="scw_tem",
                test_fn="test_id_plus_event",
                src_body=(
                    "def upsert(ev):\n"
                    "    return ev['message_id']\n"
                ),
                test_body=(
                    "def test_id_plus_event():\n"
                    "    a = {'message_id': 'm', 'event_type': 'delivered'}\n"
                    "    b = {'message_id': 'm', 'event_type': 'bounced'}\n"
                    "    assert upsert(a) != upsert(b)\n"
                ),
                grep_pat="message_id|event_type|tem",
                grep_hit="src/scw_tem.py:2: return ev['message_id']",
                fail_msg="AssertionError: delivered then bounced collapsed on message_id",
                first_old="    return ev['message_id']",
                first_new="    return ev['event_type']",
                first_obs="patched event_type only (collides across messages)",
                still_msg="AssertionError: event_type-only collapses two invoices that both bounced",
                reread_obs="Scaleway TEM webhook has message_id plus event_type; retries replay both",
                plan_change="PK (message_id, event_type). Neither field alone is unique.",
                fix_new="    return (ev['message_id'], ev['event_type'])",
                fix_obs="patched (message_id, event_type)",
                docs_url="https://www.scaleway.com/en/developers/api/transactional-email/",
                docs_ok="TEM webhooks include message_id and event_type for each activity.",
                docs_url2="https://www.scaleway.com/en/docs/managed-services/transactional-email/api-cli/using-webhook-notifications/",
                docs_ok2="A bounce after deliver must not overwrite the deliver row.",
                outcome="(message_id, event_type) kept both rows. Single-field unused (success).",
                domain="scaleway-tem-message-id-plus-event-type",
                stack="Scaleway Transactional Email",
                seed="scaleway-tem-id-plus-event",
                residual="Not invoice-row-dup.",
                coverage=83,
            ),
            _p(
                slug="responsys-riid-handoff",
                goal="Do not treat Oracle Responsys riid as a unique email event.",
                plan="Read riid-as-event, try riid+campaign, then hand off eventId.",
                mod="rsp_ri",
                test_fn="test_riid_not_event",
                src_body=(
                    "def pk(ev):\n"
                    "    return ev['riid']\n"
                ),
                test_body=(
                    "def test_riid_not_event():\n"
                    "    assert pk({'riid': 'r1', 'eventId': 'e9'}) != 'r1'\n"
                ),
                grep_pat="riid|eventId|Responsys",
                grep_hit="src/rsp_ri.py:2: return ev['riid']",
                fail_msg="AssertionError: recipient riid collapsed all opens for that person",
                first_old="    return ev['riid']",
                first_new="    return ev['riid'] + ':' + ev.get('campaignName', '')",
                first_obs="patched riid+campaign (still person+campaign, not event)",
                still_msg="AssertionError: two opens in one campaign still one row",
                reread_obs="riid is the recipient in the Profile List; eventId is the activity",
                plan_change="riid is profile grain. Handoff RSP-RI-3.",
                fix_new="    return {'handoff': 'RSP-RI-3'}",
                fix_obs="ticket filed. still riid-grained",
                docs_url="https://docs.oracle.com/en/cloud/saas/marketing/responsys-rest-api/",
                docs_ok="riid identifies the profile record, not a send or open.",
                docs_url2="https://docs.oracle.com/en/cloud/saas/marketing/responsys-user/",
                docs_ok2="Event ids are campaign-plat. Handoff RSP-RI-3. Not invoice-row-dup.",
                outcome="Still riid-grained; profile id is campaign — handoff RSP-RI-3.",
                domain="oracle-responsys-riid-vs-eventid",
                stack="Oracle Responsys Profile List",
                seed="responsys-riid-handoff",
                residual="riid is not an open.",
                ticket="RSP-RI-3",
                ticket_why="Responsys eventId owned by campaign-plat",
                coverage=83,
            ),
        ),
    ],
    "feature-flag-debug-factory": [
        (
            _p(
                slug="pennant-user-vs-request",
                goal="Evaluate Laravel Pennant flags for the User scope, not request IP.",
                plan="Read IP-as-actor, try session id, then Feature::for($user).",
                mod="penn_u",
                test_fn="test_user_scope_not_ip",
                src_body=(
                    "def actor(req):\n"
                    "    return req['ip']\n"
                ),
                test_body=(
                    "def test_user_scope_not_ip():\n"
                    "    assert actor({'ip': '1.1.1.1', 'user_id': 9}) == 9\n"
                ),
                grep_pat="Feature::for|request\\(\\)->ip|user_id",
                grep_hit="src/penn_u.py:2: return req['ip']",
                fail_msg="AssertionError: '1.1.1.1' == 9; invoice flag defined for User",
                first_old="    return req['ip']",
                first_new="    return req.get('session_id') or req['ip']",
                first_obs="patched session (still not the User model scope)",
                still_msg="AssertionError: session id is not Feature::for($user)",
                reread_obs="Pennant feature InvoiceBeta uses define scope User, not Request",
                plan_change="Feature::for($user) matching the define() scope. IP is not the actor.",
                fix_new="    return req['user_id']",
                fix_obs="patched user_id actor",
                docs_url="https://laravel.com/docs/11.x/pennant#defining-features",
                docs_ok="Pennant scopes follow the define() type; User features must not use IP.",
                docs_url2="https://laravel.com/docs/11.x/pennant#checking-features",
                docs_ok2="Feature::for($user) is the actor. Not Statsig user vs company.",
                outcome="User scope matched InvoiceBeta. IP unused (success).",
                domain="laravel-pennant-user-scope-vs-request-ip",
                stack="Laravel Pennant",
                seed="pennant-user-vs-request",
                residual="Not Statsig customIDs.company.",
                coverage=85,
            ),
            _p(
                slug="azure-appconfig-targeting-handoff",
                goal="Do not treat Azure App Configuration TimeWindow filter as Targeting.",
                plan="Read time-as-target, try clock skew, then hand off TargetingFilter.",
                mod="aac_tf",
                test_fn="test_timewindow_not_targeting",
                src_body=(
                    "def why_off(filters):\n"
                    "    return 'targeting' if 'TimeWindow' in filters else 'ok'\n"
                ),
                test_body=(
                    "def test_timewindow_not_targeting():\n"
                    "    assert why_off(['TimeWindow']) != 'targeting'\n"
                ),
                grep_pat="TimeWindow|TargetingFilter|Microsoft.Targeting",
                grep_hit="src/aac_tf.py:2: return 'targeting' if 'TimeWindow' in filters else 'ok'",
                fail_msg="AssertionError: TimeWindow off labeled targeting; users never evaluated",
                first_old="    return 'targeting' if 'TimeWindow' in filters else 'ok'",
                first_new="    return 'targeting_skew' if 'TimeWindow' in filters else 'ok'",
                first_obs="patched clock skew (still targeting-classed)",
                still_msg="AssertionError: TimeWindow is a schedule filter, not TargetingFilter",
                reread_obs="Invoice flag uses Microsoft.TimeWindow; TargetingFilter is unset",
                plan_change="TimeWindow vs Targeting is platform config. Handoff AAC-TF-2.",
                fix_new="    return 'handoff_AAC-TF-2' if 'TimeWindow' in filters else 'ok'",
                fix_obs="ticket filed. still targeting-classed",
                docs_url="https://learn.microsoft.com/en-us/azure/azure-app-configuration/howto-feature-filters-aspnet-core",
                docs_ok="TimeWindow and Targeting are different feature filters.",
                docs_url2="https://learn.microsoft.com/en-us/azure/azure-app-configuration/howto-targetingfilter-aspnet-core",
                docs_ok2="TargetingFilter is appconfig-plat. Handoff AAC-TF-2. Not Statsig.",
                outcome="Still targeting-classed; TimeWindow is schedule — handoff AAC-TF-2.",
                domain="azure-appconfig-timewindow-vs-targeting-filter",
                stack="Azure App Configuration feature manager",
                seed="azure-appconfig-targeting-handoff",
                residual="Not Statsig user vs company.",
                ticket="AAC-TF-2",
                ticket_why="TargetingFilter owned by appconfig-plat",
                coverage=85,
            ),
        ),
        (
            _p(
                slug="unleash-dependent-parent",
                goal="Skip Unleash child flags when the parent feature is disabled.",
                plan="Read child-alone, try cache TTL, then parent constraint.",
                mod="ul_dep",
                test_fn="test_parent_must_be_on",
                src_body=(
                    "def eval_child(flags):\n"
                    "    return flags['child']\n"
                ),
                test_body=(
                    "def test_parent_must_be_on():\n"
                    "    assert eval_child({'parent': False, 'child': True}) is False\n"
                ),
                grep_pat="dependent|parentFlag|child",
                grep_hit="src/ul_dep.py:2: return flags['child']",
                fail_msg="AssertionError: child True while parent disabled; invoices saw beta",
                first_old="    return flags['child']",
                first_new="    return flags['child'] if flags.get('cache_fresh') else False",
                first_obs="patched cache TTL (still ignores parent)",
                still_msg="AssertionError: cache freshness is not a parent constraint",
                reread_obs="Unleash dependent feature invoice-child requires parent invoice-rollout",
                plan_change="AND the parent enabled constraint. Child strategy alone is not enough.",
                fix_new="    return bool(flags.get('parent')) and bool(flags.get('child'))",
                fix_obs="patched parent AND child",
                docs_url="https://docs.getunleash.io/reference/dependent-features",
                docs_ok="Dependent features evaluate only when the parent is enabled.",
                docs_url2="https://docs.getunleash.io/reference/feature-toggles",
                docs_ok2="Parent off must force child off. Not stickiness, not Statsig company.",
                outcome="Parent-off hid the child. Cache unused (success).",
                domain="unleash-dependent-feature-parent-constraint",
                stack="Unleash dependent features",
                seed="unleash-dependent-parent",
                residual="Not Statsig user vs company, not stickiness.",
                coverage=84,
            ),
            _p(
                slug="bucketeer-segment-handoff",
                goal="Do not treat Bucketeer user-id rollout as a segment rule.",
                plan="Read userid-as-segment, try percentage, then hand off segment.",
                mod="bkt_seg",
                test_fn="test_userid_not_segment",
                src_body=(
                    "def why_on(ctx):\n"
                    "    return 'segment' if ctx.get('user_id') else 'off'\n"
                ),
                test_body=(
                    "def test_userid_not_segment():\n"
                    "    assert why_on({'user_id': 'u1'}) != 'segment'\n"
                ),
                grep_pat="segment|user_id|Bucketeer",
                grep_hit="src/bkt_seg.py:2: return 'segment' if ctx.get('user_id') else 'off'",
                fail_msg="AssertionError: individual user rollout labeled segment; ops looked at rules",
                first_old="    return 'segment' if ctx.get('user_id') else 'off'",
                first_new="    return 'segment_pct' if ctx.get('user_id') else 'off'",
                first_obs="patched percentage (still segment-classed)",
                still_msg="AssertionError: user-id allowlist is not a segment clause",
                reread_obs="Bucketeer individual targeting user_id vs segment rule invoice-eu",
                plan_change="Segment rules are platform. Handoff BKT-SEG-3.",
                fix_new="    return 'handoff_BKT-SEG-3' if ctx.get('user_id') else 'off'",
                fix_obs="ticket filed. still segment-classed",
                docs_url="https://docs.bucketeer.io/feature-flags/creating-feature-flags/targeting",
                docs_ok="Individual user targeting is not a segment. Segments are lists/clauses.",
                docs_url2="https://docs.bucketeer.io/feature-flags/creating-feature-flags/segments",
                docs_ok2="Segment membership is flag-plat. Handoff BKT-SEG-3. Not Statsig company.",
                outcome="Still segment-classed; user allowlist is not a segment — handoff BKT-SEG-3.",
                domain="bucketeer-individual-userid-vs-segment-rule",
                stack="Bucketeer targeting",
                seed="bucketeer-segment-handoff",
                residual="Not Statsig user vs company.",
                ticket="BKT-SEG-3",
                ticket_why="segment clause owned by flag-plat",
                coverage=84,
            ),
        ),
        (
            _p(
                slug="featbit-targeting-vs-pct",
                goal="Honor FeatBit targeting rules before the percentage rollout.",
                plan="Read pct-first, try salt, then targeting then percentage.",
                mod="fb_tgt",
                test_fn="test_targeting_before_pct",
                src_body=(
                    "def eval_flag(ctx):\n"
                    "    return hash(ctx['key']) % 100 < ctx['pct']\n"
                ),
                test_body=(
                    "def test_targeting_before_pct():\n"
                    "    ctx = {'key': 'inv-1', 'pct': 0, 'rules': [{'attr': 'plan', 'eq': 'pro'}],"
                    " 'plan': 'pro'}\n"
                    "    assert eval_flag(ctx) is True\n"
                ),
                grep_pat="targeting|pct|hash\\(ctx",
                grep_hit="src/fb_tgt.py:2: return hash(ctx['key']) % 100 < ctx['pct']",
                fail_msg="AssertionError: pro plan hashed into 0% and missed targeting rule",
                first_old="    return hash(ctx['key']) % 100 < ctx['pct']",
                first_new="    return hash(ctx['key'] + ctx.get('salt', '')) % 100 < ctx['pct']",
                first_obs="patched salt (still percentage-first, targeting skipped)",
                still_msg="AssertionError: salt still ignores plan=pro targeting",
                reread_obs="FeatBit evaluates targeting rules first; percentage is the fallthrough",
                plan_change="Match targeting rules before percentage. Salt does not replace targeting.",
                fix_new=(
                    "    if any(ctx.get(r['attr']) == r['eq'] for r in ctx.get('rules', [])):\n"
                    "        return True\n"
                    "    return hash(ctx['key']) % 100 < ctx['pct']"
                ),
                fix_obs="patched targeting-then-pct",
                docs_url="https://docs.featbit.co/feature-flags/targeting",
                docs_ok="Targeting rules run before the default percentage rollout.",
                docs_url2="https://docs.featbit.co/feature-flags/rollout",
                docs_ok2="0% default still serves targeted users. Not Statsig company.",
                outcome="plan=pro served via targeting at 0%. Salt unused (success).",
                domain="featbit-targeting-rules-before-percentage",
                stack="FeatBit targeting",
                seed="featbit-targeting-vs-pct",
                residual="Not Statsig user vs company.",
                coverage=82,
            ),
            _p(
                slug="varioqub-device-handoff",
                goal="Do not treat Yandex Varioqub device-id split as user-id.",
                plan="Read device-as-user, try cookie, then hand off device unit.",
                mod="vq_dev",
                test_fn="test_device_not_user",
                src_body=(
                    "def unit(ctx):\n"
                    "    return ctx.get('user_id') or ctx['device_id']\n"
                ),
                test_body=(
                    "def test_device_not_user():\n"
                    "    assert unit({'device_id': 'd1', 'user_id': 'u1'}) != 'u1'\n"
                ),
                grep_pat="device_id|user_id|Varioqub",
                grep_hit="src/vq_dev.py:2: return ctx.get('user_id') or ctx['device_id']",
                fail_msg="AssertionError: experiment unit flipped to user_id; device split broke",
                first_old="    return ctx.get('user_id') or ctx['device_id']",
                first_new="    return ctx.get('cookie_id') or ctx.get('user_id') or ctx['device_id']",
                first_obs="patched cookie (still not the device unit)",
                still_msg="AssertionError: cookie is not the Varioqub device testid unit",
                reread_obs="Varioqub A/B uses testid device; logged-in user_id is a different experiment",
                plan_change="Device unit is experiment-plat. Handoff VQ-DEV-2.",
                fix_new="    return {'handoff': 'VQ-DEV-2'}",
                fix_obs="ticket filed. still user-classed",
                docs_url="https://yandex.com/dev/varioqub/doc/intro.html",
                docs_ok="Varioqub testid is typically device; user id is a separate experiment.",
                docs_url2="https://yandex.com/dev/varioqub/doc/concepts/flags.html",
                docs_ok2="Unit type is experiment-plat. Handoff VQ-DEV-2. Not Statsig company.",
                outcome="Still user-classed; device unit is experiment — handoff VQ-DEV-2.",
                domain="yandex-varioqub-device-testid-vs-user-id",
                stack="Yandex Varioqub",
                seed="varioqub-device-handoff",
                residual="Not Statsig user vs company.",
                ticket="VQ-DEV-2",
                ticket_why="device testid owned by experiment-plat",
                coverage=82,
            ),
        ),
    ],
    "ssl-cert-rotation-factory": [
        (
            _p(
                slug="stunnel-sighup-cafile",
                goal="SIGHUP stunnel to reload cert+CAfile; do not restart and drop OCR.",
                plan="Read restart-as-reload, try SIGKILL, then SIGHUP.",
                mod="st_hup",
                test_fn="test_hup_not_restart",
                src_body=(
                    "def rotate():\n"
                    "    return 'systemctl restart stunnel'\n"
                ),
                test_body=(
                    "def test_hup_not_restart():\n"
                    "    assert 'restart' not in rotate() and 'HUP' in rotate()\n"
                ),
                grep_pat="SIGHUP|restart stunnel|CAfile",
                grep_hit="src/st_hup.py:2: return 'systemctl restart stunnel'",
                fail_msg="AssertionError: restart dropped 40 OCR tunnels; CAfile already on disk",
                first_old="    return 'systemctl restart stunnel'",
                first_new="    return 'kill -9 $(pidof stunnel); stunnel /etc/stunnel/ocr.conf'",
                first_obs="patched SIGKILL+start (still a drop, still not HUP)",
                still_msg="AssertionError: SIGKILL still drops connections; HUP reloads CAfile",
                reread_obs="stunnel reloads cert and CAfile on SIGHUP without delete-create",
                plan_change="kill -HUP after writing pem+CAfile. Do not restart, do not delete the secret.",
                fix_new="    return 'kill -HUP $(pidof stunnel)'",
                fix_obs="patched SIGHUP",
                docs_url="https://www.stunnel.org/static/stunnel.html",
                docs_ok="SIGHUP reloads configuration including cert and CAfile.",
                docs_url2="https://www.stunnel.org/faq.html",
                docs_ok2="Restart drops accepted sockets. HUP keeps them. Not delete-then-create.",
                outcome="SIGHUP reloaded CAfile. Restart unused (success).",
                domain="stunnel-sighup-cafile-reload-vs-restart",
                stack="stunnel TLS proxy",
                seed="stunnel-sighup-cafile",
                residual="Not k8s delete-then-create secret.",
                coverage=86,
            ),
            _p(
                slug="f5-clientssl-pair-handoff",
                goal="Do not replace an F5 clientssl cert without the matching key in one tmsh.",
                plan="Read cert-only, try key-only, then hand off certkey pair.",
                mod="f5_css",
                test_fn="test_certkey_pair",
                src_body=(
                    "def rotate():\n"
                    "    return ['tmsh install sys crypto cert ocr.crt from-local-file ocr.crt']\n"
                ),
                test_body=(
                    "def test_certkey_pair():\n"
                    "    cmds = rotate()\n"
                    "    assert any('certkey' in c or 'key' in c for c in cmds)\n"
                ),
                grep_pat="clientssl|sys crypto cert|certkey",
                grep_hit="src/f5_css.py:2: return ['tmsh install sys crypto cert ocr.crt ...']",
                fail_msg="AssertionError: cert installed, key leftover; handshake 'key mismatch'",
                first_old="    return ['tmsh install sys crypto cert ocr.crt from-local-file ocr.crt']",
                first_new="    return ['tmsh install sys crypto key ocr.key from-local-file ocr.key']",
                first_obs="patched key-only (other half missing)",
                still_msg="AssertionError: key-only still mismatches the installed cert",
                reread_obs="clientssl profile binds a cert/key pair; tmsh must update both",
                plan_change="Pair rotate is F5 plat. Handoff F5-CSS-4. Not delete-then-create secret.",
                fix_new="    return ['handoff F5-CSS-4']",
                fix_obs="ticket filed. still half-rotated",
                docs_url="https://my.f5.com/manage/s/article/K14758",
                docs_ok="Client SSL profiles require matching cert and key objects.",
                docs_url2="https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/ltm/ltm_profile_client-ssl.html",
                docs_ok2="tmsh pair update is f5-plat. Handoff F5-CSS-4. Not delete-create.",
                outcome="Still half-rotated; certkey pair is F5 — handoff F5-CSS-4.",
                domain="f5-clientssl-cert-key-pair-vs-cert-only",
                stack="F5 BIG-IP clientssl",
                seed="f5-clientssl-pair-handoff",
                residual="Not delete-then-create k8s secret.",
                ticket="F5-CSS-4",
                ticket_why="clientssl certkey pair owned by f5-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="openresty-ssl-cert-by-lua",
                goal="Refresh OpenResty ssl_certificate_by_lua shm; nginx -s reload keeps old PEM.",
                plan="Read reload-as-lua, try reopen, then update shm.",
                mod="or_lua",
                test_fn="test_shm_not_reload",
                src_body=(
                    "def rotate():\n"
                    "    return 'nginx -s reload'\n"
                ),
                test_body=(
                    "def test_shm_not_reload():\n"
                    "    assert rotate() == 'ngx.shared.certs:set'\n"
                ),
                grep_pat="ssl_certificate_by_lua|ngx.shared|reload",
                grep_hit="src/or_lua.py:2: return 'nginx -s reload'",
                fail_msg="AssertionError: reload still served old PEM; lua cosocket cache held leaf",
                first_old="    return 'nginx -s reload'",
                first_new="    return 'nginx -s reopen'",
                first_obs="patched reopen (still worker files, not lua shm)",
                still_msg="AssertionError: reopen does not refresh ssl_certificate_by_lua shm",
                reread_obs="ssl_certificate_by_lua_block reads ngx.shared.certs each handshake",
                plan_change="ngx.shared.certs:set the new PEM. reload/reopen do not touch shm.",
                fix_new="    return 'ngx.shared.certs:set'",
                fix_obs="patched shm set",
                docs_url="https://github.com/openresty/lua-resty-core/blob/master/lib/ngx/ssl.md",
                docs_ok="ssl_certificate_by_lua can load certs from shm per handshake.",
                docs_url2="https://github.com/openresty/lua-nginx-module#ssl_certificate_by_lua_block",
                docs_ok2="Reload does not clear ngx.shared. Not delete-then-create secret.",
                outcome="shm set served the new leaf. Reload unused (success).",
                domain="openresty-ssl-certificate-by-lua-shm-vs-reload",
                stack="OpenResty lua-nginx-module ssl",
                seed="openresty-ssl-cert-by-lua",
                residual="Not delete-then-create secret.",
                coverage=85,
            ),
            _p(
                slug="akamai-cps-enrollment-handoff",
                goal="Do not treat Akamai CPS enrollment as a deployed certificate.",
                plan="Read enroll-as-deploy, try wait 5m, then hand off CPS deploy.",
                mod="ak_cps",
                test_fn="test_enrollment_not_deploy",
                src_body=(
                    "def status(enroll):\n"
                    "    return 'live' if enroll.get('id') else 'missing'\n"
                ),
                test_body=(
                    "def test_enrollment_not_deploy():\n"
                    "    assert status({'id': 'e1', 'deployed': False}) != 'live'\n"
                ),
                grep_pat="enrollment|deployed|CPS",
                grep_hit="src/ak_cps.py:2: return 'live' if enroll.get('id') else 'missing'",
                fail_msg="AssertionError: enrollment id treated live; property still old leaf",
                first_old="    return 'live' if enroll.get('id') else 'missing'",
                first_new="    return 'live' if enroll.get('id') and enroll.get('waited') else 'missing'",
                first_obs="patched wait flag (still enrollment, not deployment)",
                still_msg="AssertionError: waiting on enrollment does not deploy to the property",
                reread_obs="CPS enrollment is the order; deployment pushes to the network",
                plan_change="CPS deploy is akamai-plat. Handoff AKAMAI-CPS-3.",
                fix_new="    return 'handoff_AKAMAI-CPS-3'",
                fix_obs="ticket filed. still enrollment-live",
                docs_url="https://techdocs.akamai.com/cps/docs",
                docs_ok="Certificate Provisioning System enrollment != network deployment.",
                docs_url2="https://techdocs.akamai.com/cps/reference",
                docs_ok2="Deploy is akamai-plat. Handoff AKAMAI-CPS-3. Not delete-create secret.",
                outcome="Still enrollment-live; deploy is Akamai — handoff AKAMAI-CPS-3.",
                domain="akamai-cps-enrollment-vs-network-deployment",
                stack="Akamai CPS",
                seed="akamai-cps-enrollment-handoff",
                residual="Not delete-then-create secret.",
                ticket="AKAMAI-CPS-3",
                ticket_why="CPS deploy owned by akamai-plat",
                coverage=85,
            ),
        ),
        (
            _p(
                slug="ats-ssl-multicert-reload",
                goal="traffic_ctl config reload after ATS ssl_multicert; restart drops OCR.",
                plan="Read restart-as-reload, try stop/start, then traffic_ctl reload.",
                mod="ats_mc",
                test_fn="test_ctl_reload_not_restart",
                src_body=(
                    "def rotate():\n"
                    "    return 'systemctl restart trafficserver'\n"
                ),
                test_body=(
                    "def test_ctl_reload_not_restart():\n"
                    "    assert rotate() == 'traffic_ctl config reload'\n"
                ),
                grep_pat="ssl_multicert|traffic_ctl|restart trafficserver",
                grep_hit="src/ats_mc.py:2: return 'systemctl restart trafficserver'",
                fail_msg="AssertionError: restart dropped keep-alives; ssl_multicert already written",
                first_old="    return 'systemctl restart trafficserver'",
                first_new="    return 'trafficserver stop && trafficserver start'",
                first_obs="patched stop/start (still a drop)",
                still_msg="AssertionError: stop/start still drops; config reload is enough",
                reread_obs="ssl_multicert.config + traffic_ctl config reload picks up the new pem",
                plan_change="traffic_ctl config reload. Do not restart, do not delete the secret.",
                fix_new="    return 'traffic_ctl config reload'",
                fix_obs="patched traffic_ctl reload",
                docs_url="https://docs.trafficserver.apache.org/en/latest/admin-guide/files/ssl_multicert.config.en.html",
                docs_ok="ssl_multicert.config maps dest_ip to ssl_cert_name; reload applies it.",
                docs_url2="https://docs.trafficserver.apache.org/en/latest/admin-guide/tools/traffic_ctl.en.html",
                docs_ok2="config reload does not drop accepted connections. Not delete-create.",
                outcome="traffic_ctl reload served the new leaf. Restart unused (success).",
                domain="apache-trafficserver-ssl-multicert-reload-vs-restart",
                stack="Apache Traffic Server ssl_multicert",
                seed="ats-ssl-multicert-reload",
                residual="Not delete-then-create secret.",
                coverage=83,
            ),
            _p(
                slug="citrix-adc-ssl-certkey-handoff",
                goal="Do not update a Citrix ADC cert without rebinding ssl certkey to the vserver.",
                plan="Read update-as-bound, try sleep, then hand off certkey bind.",
                mod="ctx_ck",
                test_fn="test_update_not_bound",
                src_body=(
                    "def rotate():\n"
                    "    return ['update ssl certKey ocr']\n"
                ),
                test_body=(
                    "def test_update_not_bound():\n"
                    "    assert any('bind' in c for c in rotate())\n"
                ),
                grep_pat="ssl certKey|bind ssl vserver|update ssl",
                grep_hit="src/ctx_ck.py:2: return ['update ssl certKey ocr']",
                fail_msg="AssertionError: certKey updated, vserver still old; bind missing",
                first_old="    return ['update ssl certKey ocr']",
                first_new="    return ['update ssl certKey ocr', 'sleep 30']",
                first_obs="patched sleep (still no bind)",
                still_msg="AssertionError: sleep cannot rebind ssl certkey to the vserver",
                reread_obs="Citrix ADC needs bind ssl vserver ocr-vs -certkeyName ocr after update",
                plan_change="vserver bind is netscaler-plat. Handoff CTX-CK-3.",
                fix_new="    return ['handoff CTX-CK-3']",
                fix_obs="ticket filed. still unbound",
                docs_url="https://docs.citrix.com/en-us/citrix-adc/current-release/ssl/ssl-certificates.html",
                docs_ok="Updating a certKey does not rebind it to SSL virtual servers.",
                docs_url2="https://docs.citrix.com/en-us/citrix-adc/current-release/ssl/ssl-certificates/bind-cert-key.html",
                docs_ok2="bind ssl vserver is netscaler-plat. Handoff CTX-CK-3. Not delete-create.",
                outcome="Still unbound; vserver bind is ADC — handoff CTX-CK-3.",
                domain="citrix-adc-ssl-certkey-update-vs-vserver-bind",
                stack="Citrix ADC ssl certKey",
                seed="citrix-adc-ssl-certkey-handoff",
                residual="Not delete-then-create secret.",
                ticket="CTX-CK-3",
                ticket_why="ssl vserver certkey bind owned by netscaler-plat",
                coverage=83,
            ),
        ),
    ],
    "search-index-rebuild-factory": [
        (
            _p(
                slug="pg-gin-tsvector-setweight",
                goal="Weight Postgres title A in the stored tsvector; do not rebuild via TRUNCATE.",
                plan="Read unweighted-to_tsvector, try simple config, then setweight title||body.",
                mod="pg_tsv",
                test_fn="test_title_weight_a",
                src_body=(
                    "def tsv(title, body):\n"
                    "    return f\"to_tsvector('simple', {body!r})\"\n"
                ),
                test_body=(
                    "def test_title_weight_a():\n"
                    "    sql = tsv('SKU-9', 'invoice body')\n"
                    "    assert 'setweight' in sql and \"'A'\" in sql\n"
                ),
                grep_pat="setweight|to_tsvector|TRUNCATE",
                grep_hit="src/pg_tsv.py:2: return f\"to_tsvector('simple', {body!r})\"",
                fail_msg="AssertionError: title SKU-9 not in weighted vector; body-only simple",
                first_old="    return f\"to_tsvector('simple', {body!r})\"",
                first_new="    return f\"to_tsvector('english', {body!r})\"",
                first_obs="patched english config (still no title weight)",
                still_msg="AssertionError: english stemmer still ignores title weight A",
                reread_obs="GIN on invoices.tsv; UPDATE tsv = setweight(title,'A') || setweight(body,'D')",
                plan_change="In-place UPDATE setweight. Do not TRUNCATE or DROP INDEX.",
                fix_new=(
                    "    return (\"setweight(to_tsvector('english', \" + repr(title) + \"), 'A') || \""
                    "setweight(to_tsvector('english', \" + repr(body) + \"), 'D')\")"
                ),
                fix_obs="patched setweight A||D",
                docs_url="https://www.postgresql.org/docs/current/textsearch-controls.html#TEXTSEARCH-PARSING-DOCUMENTS",
                docs_ok="setweight labels lexemes A-D; GIN follows the stored tsvector column.",
                docs_url2="https://www.postgresql.org/docs/current/textsearch-indexes.html",
                docs_ok2="UPDATE the generated column; do not TRUNCATE-then-reindex.",
                outcome="Title weight A ranked SKU-9 first. TRUNCATE unused (success).",
                domain="postgres-gin-tsvector-setweight-title-vs-body",
                stack="PostgreSQL GIN tsvector",
                seed="pg-gin-tsvector-setweight",
                residual="Not TRUNCATE-then-reindex. Left sir-r26 placeholder in raw.",
                coverage=87,
            ),
            _p(
                slug="hnswlib-save-vs-load-handoff",
                goal="Do not search an HNSWlib index that was never saveIndex'd.",
                plan="Read ram-as-disk, try pickle, then hand off saveIndex.",
                mod="hnsw_sv",
                test_fn="test_save_before_load",
                src_body=(
                    "def persist(idx, path):\n"
                    "    return path  # ram only\n"
                ),
                test_body=(
                    "def test_save_before_load():\n"
                    "    assert persist(idx, 'ocr.bin') == 'saved:ocr.bin'\n"
                ),
                grep_pat="saveIndex|loadIndex|pickle",
                grep_hit="src/hnsw_sv.py:2: return path  # ram only",
                fail_msg="AssertionError: loadIndex on empty path; knn empty after process restart",
                first_old="    return path  # ram only",
                first_new="    import pickle\n    pickle.dump(idx, open(path, 'wb'))\n    return path",
                first_obs="patched pickle (not hnswlib saveIndex format)",
                still_msg="AssertionError: pickle is not saveIndex; loadIndex fails magic",
                reread_obs="hnswlib needs saveIndex/loadIndex; pickle dumps Python wrapper only",
                plan_change="saveIndex is index-plat. Handoff HNSW-SAVE-2. Not TRUNCATE.",
                fix_new="    return 'handoff:HNSW-SAVE-2'",
                fix_obs="ticket filed. still ram-only",
                docs_url="https://github.com/nmslib/hnswlib#python-bindings-example",
                docs_ok="p.save_index / p.load_index persist the graph; pickle does not.",
                docs_url2="https://github.com/nmslib/hnswlib#api-description",
                docs_ok2="Persistence is index-plat. Handoff HNSW-SAVE-2. Not TRUNCATE-reindex.",
                outcome="Still ram-only; saveIndex is index-plat — handoff HNSW-SAVE-2.",
                domain="hnswlib-saveindex-vs-pickle-ram",
                stack="hnswlib Python bindings",
                seed="hnswlib-save-vs-load-handoff",
                residual="Not TRUNCATE-then-reindex.",
                ticket="HNSW-SAVE-2",
                ticket_why="saveIndex owned by index-plat",
                coverage=87,
            ),
        ),
        (
            _p(
                slug="duckdb-fts-porter-stemmer",
                goal="Build DuckDB FTS with porter stemmer; do not drop the table to 'rebuild'.",
                plan="Read unstemmed-match, try drop table, then create_fts_index stemmer=porter.",
                mod="duck_fts",
                test_fn="test_porter_not_drop",
                src_body=(
                    "def rebuild():\n"
                    "    return \"SELECT fts_main_invoices.match_bm25(id, 'invoices')\"\n"
                ),
                test_body=(
                    "def test_porter_not_drop():\n"
                    "    sql = rebuild()\n"
                    "    assert 'porter' in sql and 'DROP' not in sql\n"
                ),
                grep_pat="create_fts_index|stemmer|DROP TABLE",
                grep_hit="src/duck_fts.py:2: return \"SELECT fts_main_invoices.match_bm25(id, 'invoices')\"",
                fail_msg="AssertionError: 'invoice' query missed 'invoices'; stemmer absent",
                first_old="    return \"SELECT fts_main_invoices.match_bm25(id, 'invoices')\"",
                first_new="    return \"DROP TABLE invoices; SELECT fts_main_invoices.match_bm25(id, 'invoices')\"",
                first_obs="patched DROP TABLE (TRUNCATE-class rebuild; banned)",
                still_msg="AssertionError: DROP TABLE is not a stemmer; data gone",
                reread_obs="PRAGMA create_fts_index('invoices', 'id', 'body', stemmer='porter')",
                plan_change="create_fts_index stemmer=porter. Do not DROP/TRUNCATE.",
                fix_new=(
                    "    return \"PRAGMA create_fts_index('invoices', 'id', 'body',"
                    " stemmer='porter')\""
                ),
                fix_obs="patched porter stemmer",
                docs_url="https://duckdb.org/docs/extensions/full_text_search",
                docs_ok="create_fts_index accepts stemmer='porter'; dropping the table is not a rebuild.",
                docs_url2="https://duckdb.org/docs/guides/snippets/full_text_search",
                docs_ok2="match_bm25 uses the stemmer chosen at index create. Not TRUNCATE.",
                outcome="Porter stemmed invoice/invoices. DROP unused (success).",
                domain="duckdb-fts-porter-stemmer-vs-drop-table",
                stack="DuckDB FTS extension",
                seed="duckdb-fts-porter-stemmer",
                residual="Not TRUNCATE-then-reindex. Left sir-r26 placeholder in raw.",
                coverage=85,
            ),
            _p(
                slug="scann-serialize-handoff",
                goal="Do not mmap a ScaNN index that was never serialized.",
                plan="Read ram-as-mmap, try numpy save, then hand off serialize.",
                mod="scann_ser",
                test_fn="test_serialize_before_mmap",
                src_body=(
                    "def persist(searcher, path):\n"
                    "    return path\n"
                ),
                test_body=(
                    "def test_serialize_before_mmap():\n"
                    "    assert persist(s, 'ocr.scann') == 'serialized:ocr.scann'\n"
                ),
                grep_pat="serialize|numpy.save|mmap",
                grep_hit="src/scann_ser.py:2: return path",
                fail_msg="AssertionError: mmap empty dir; ScaNN artifacts never serialized",
                first_old="    return path",
                first_new="    import numpy as np\n    np.save(path, searcher)\n    return path",
                first_obs="patched numpy.save (not ScaNN serialize layout)",
                still_msg="AssertionError: np.save is not scann.serialize; mmap fails",
                reread_obs="ScaNN searcher.serialize(path) writes artifacts; mmap needs that tree",
                plan_change="serialize is index-plat. Handoff SCANN-SER-3. Not TRUNCATE.",
                fix_new="    return 'handoff:SCANN-SER-3'",
                fix_obs="ticket filed. still ram-only",
                docs_url="https://github.com/google-research/google-research/tree/master/scann",
                docs_ok="searcher.serialize writes the on-disk tree used by mmap.",
                docs_url2="https://github.com/google-research/google-research/blob/master/scann/docs/python.md",
                docs_ok2="Persistence is index-plat. Handoff SCANN-SER-3. Not TRUNCATE-reindex.",
                outcome="Still ram-only; serialize is index-plat — handoff SCANN-SER-3.",
                domain="scann-serialize-vs-numpy-save-mmap",
                stack="Google ScaNN",
                seed="scann-serialize-handoff",
                residual="Not TRUNCATE-then-reindex.",
                ticket="SCANN-SER-3",
                ticket_why="ScaNN serialize owned by index-plat",
                coverage=85,
            ),
        ),
        (
            _p(
                slug="pgroonga-query-vs-like",
                goal="Use PGroonga &@~ query; LIKE '%sku%' cannot use the Groonga index.",
                plan="Read LIKE-as-pgroonga, try ILIKE, then &@~ query.",
                mod="pgr_q",
                test_fn="test_query_not_like",
                src_body=(
                    "def sql(q):\n"
                    "    return f\"SELECT id FROM invoices WHERE body LIKE '%{q}%'\"\n"
                ),
                test_body=(
                    "def test_query_not_like():\n"
                    "    s = sql('SKU-9')\n"
                    "    assert '&@~' in s and 'LIKE' not in s\n"
                ),
                grep_pat="&@~|pgroonga|LIKE",
                grep_hit="src/pgr_q.py:2: return f\"SELECT id FROM invoices WHERE body LIKE '%{q}%'\"",
                fail_msg="AssertionError: seq scan LIKE; pgroonga index unused",
                first_old="    return f\"SELECT id FROM invoices WHERE body LIKE '%{q}%'\"",
                first_new="    return f\"SELECT id FROM invoices WHERE body ILIKE '%{q}%'\"",
                first_obs="patched ILIKE (still seq scan, still not Groonga)",
                still_msg="AssertionError: ILIKE still cannot use pgroonga; need &@~",
                reread_obs="CREATE INDEX ON invoices USING pgroonga (body); operator &@~",
                plan_change="WHERE body &@~ query. Do not TRUNCATE. LIKE is not Groonga.",
                fix_new="    return f\"SELECT id FROM invoices WHERE body &@~ {q!r}\"",
                fix_obs="patched &@~ query",
                docs_url="https://pgroonga.github.io/reference/operators/query-v2.html",
                docs_ok="&@~ is the PGroonga query operator that uses the Groonga index.",
                docs_url2="https://pgroonga.github.io/tutorial/",
                docs_ok2="LIKE/ILIKE are seq scans. Not TRUNCATE-then-reindex.",
                outcome="&@~ used the Groonga index. LIKE unused (success).",
                domain="pgroonga-query-operator-vs-like-seqscan",
                stack="PGroonga &@~",
                seed="pgroonga-query-vs-like",
                residual="Not TRUNCATE-then-reindex. Left sir-r26 placeholder in raw.",
                coverage=84,
            ),
            _p(
                slug="vald-agent-insert-handoff",
                goal="Do not search Vald gateway before the agent insert is committed.",
                plan="Read gateway-as-source, try sleep, then hand off agent insert.",
                mod="vald_ag",
                test_fn="test_insert_not_gateway_only",
                src_body=(
                    "def index(vec):\n"
                    "    return 'gateway.search(vec)'\n"
                ),
                test_body=(
                    "def test_insert_not_gateway_only():\n"
                    "    assert 'Insert' in index([0.1, 0.2])\n"
                ),
                grep_pat="Insert/Insert|gateway.search|vald",
                grep_hit="src/vald_ag.py:2: return 'gateway.search(vec)'",
                fail_msg="AssertionError: search empty; agent never got Insert",
                first_old="    return 'gateway.search(vec)'",
                first_new="    return 'sleep 5; gateway.search(vec)'",
                first_obs="patched sleep (still no Insert)",
                still_msg="AssertionError: sleep cannot insert into the Vald agent",
                reread_obs="Vald gateway search reads agent graphs; Insert must land first",
                plan_change="Agent Insert is vald-plat. Handoff VALD-INS-2. Not TRUNCATE.",
                fix_new="    return 'handoff VALD-INS-2'",
                fix_obs="ticket filed. still gateway-only",
                docs_url="https://vald.vdaas.org/docs/overview/about-vald/",
                docs_ok="Vald agent owns the graph; gateway search is a fan-out.",
                docs_url2="https://vald.vdaas.org/docs/tutorials/ingress-egress/",
                docs_ok2="Insert path is vald-plat. Handoff VALD-INS-2. Not TRUNCATE-reindex.",
                outcome="Still gateway-only; Insert is vald-plat — handoff VALD-INS-2.",
                domain="vald-agent-insert-vs-gateway-search",
                stack="Vald vdaas",
                seed="vald-agent-insert-handoff",
                residual="Not TRUNCATE-then-reindex.",
                ticket="VALD-INS-2",
                ticket_why="Vald agent Insert owned by vald-plat",
                coverage=84,
            ),
        ),
    ],
}


def all_pairs():
    rows = []
    for factory in CYCLE:
        for pair in PAIRS[factory]:
            rows.append((factory, pair[0], pair[1]))
    return rows
