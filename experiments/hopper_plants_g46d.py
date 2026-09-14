"""Third unique hopper wave. Do not clone g46/g46b/g46c or intervening plants.

Skip rate-limit (r67 reserved). Leave sir-r26 PLACEHOLDER in raw.
BANs: timeout-integer-only, quoted-newline, cookie-replay, invoice-row-dup,
Statsig user vs company, TRUNCATE-then-reindex, delete-then-create secret.
"""

PREFIX = {
    "rate-limit-backoff-factory": "rlb",
    "queue-backpressure-factory": "qbp",
    "csv-excel-ingest-factory": "cei",
    "websocket-reconnect-factory": "wsr",
    "email-webhook-retry-factory": "ewr",
    "feature-flag-debug-factory": "ffd",
    "search-index-rebuild-factory": "sir",
    "log-redaction-factory": "lrd",
    "ssl-cert-rotation-factory": "ssl",
}

START = {
    "rate-limit-backoff-factory": 80,
    "queue-backpressure-factory": 39,
    "csv-excel-ingest-factory": 39,
    "websocket-reconnect-factory": 39,
    "email-webhook-retry-factory": 38,
    "feature-flag-debug-factory": 39,
    "search-index-rebuild-factory": 51,
    "log-redaction-factory": 65,
    "ssl-cert-rotation-factory": 106,
}

CYCLE = list(PREFIX)


def _p(**kwargs):
    return kwargs


PAIRS = {
    "rate-limit-backoff-factory": [
        (
            _p(
                slug="strava-15min-vs-daily",
                goal="Honor Strava X-RateLimit-Usage 15-min slot; do not treat daily 30k as rps.",
                plan="Read daily-as-15min, try 86400s, then 15-min remaining.",
                mod="strv15",
                test_fn="test_15min_not_daily",
                src_body=(
                    "def remaining(h):\n"
                    "    return int(h['X-RateLimit-Limit'].split(',')[1])\n"
                ),
                test_body=(
                    "def test_15min_not_daily():\n"
                    "    h = {'X-RateLimit-Limit': '200,30000', 'X-RateLimit-Usage': '180,400'}\n"
                    "    assert remaining(h) == 20\n"
                ),
                grep_pat="X-RateLimit-Usage|X-RateLimit-Limit|strava",
                grep_hit="src/strv15.py:2: return int(h['X-RateLimit-Limit'].split(',')[1])",
                fail_msg="AssertionError: 30000 == 20; daily limit used as remaining",
                first_old="    return int(h['X-RateLimit-Limit'].split(',')[1])",
                first_new="    return 30000 - int(h['X-RateLimit-Usage'].split(',')[1])",
                first_obs="patched daily remaining (wrong window; 15-min is slot 0)",
                still_msg="AssertionError: daily remaining 29600 != 20; 15-min is first slot",
                reread_obs="Strava Usage is 15-min,daily; remaining is 200-180=20 not daily 30k",
                plan_change="Use 15-min slot 0 remaining. Daily is not rps. Not Retry-After catalog.",
                fix_new="    lim=h['X-RateLimit-Limit'].split(','); use=h['X-RateLimit-Usage'].split(','); return int(lim[0])-int(use[0])",
                fix_obs="patched 15-min remaining",
                docs_url="https://developers.strava.com/docs/rate-limits/",
                docs_ok="Strava X-RateLimit-Usage is 15-min then daily; short window is first.",
                docs_url2="https://developers.strava.com/docs/reference/",
                docs_ok2="Prefer 15-min remaining. Not Retry-After catalog. Not Reddit Used clone.",
                outcome="15-min remaining matched 20. Daily unused (success).",
                domain="strava-15min-usage-vs-daily-limit",
                stack="Strava X-RateLimit-Usage 15-min",
                seed="strava-15min-vs-daily",
                residual="Daily 30k is not rps. Not Retry-After catalog.",
                coverage=86,
            ),
            _p(
                slug="fitbit-daily-plan-handoff",
                goal="Do not retry Fitbit 429 as a sleepable per-call rate when the daily quota is exhausted.",
                plan="Read daily-as-sleep, try 3600s, then hand off daily plan.",
                mod="ftbtpl",
                test_fn="test_daily_not_sleep",
                src_body=(
                    "def classify(status, ctx):\n"
                    "    return 'sleep_2s' if status == 429 else 'ok'\n"
                ),
                test_body=(
                    "def test_daily_not_sleep():\n"
                    "    assert classify(429, {'scope': 'daily'}) != 'sleep_2s'\n"
                ),
                grep_pat="daily|429|sleep",
                grep_hit="src/ftbtpl.py:2: return 'sleep_2s' if status == 429 else 'ok'",
                fail_msg="AssertionError: daily 429 slept 2s; Fitbit quota is a daily plan",
                first_old="    return 'sleep_2s' if status == 429 else 'ok'",
                first_new="    return 'sleep_3600' if status == 429 else 'ok'",
                first_obs="patched 3600s (still treating daily plan as per-call rate)",
                still_msg="AssertionError: sleep cannot mint a Fitbit daily quota",
                reread_obs="Fitbit 429 fitbit-rate-limit-type=DAY is the daily plan, not per-call",
                plan_change="Daily plan is quota-plat. Handoff FB-DAY-3. Not Retry-After catalog.",
                fix_new="    return 'handoff_FB-DAY-3' if status == 429 else 'ok'",
                fix_obs="ticket filed. still rate-classed",
                docs_url="https://dev.fitbit.com/build/reference/web-api/troubleshooting-guide/rate-limits/",
                docs_ok="Fitbit 429 can be hourly or daily; daily is a plan cap.",
                docs_url2="https://dev.fitbit.com/build/reference/web-api/troubleshooting-guide/",
                docs_ok2="Sleep cannot mint daily quota. Handoff FB-DAY-3. Not Retry-After catalog.",
                outcome="Still rate-classed; daily plan is quota-plat — handoff FB-DAY-3.",
                domain="fitbit-daily-quota-vs-sleepable-429",
                stack="Fitbit daily rate-limit-type",
                seed="fitbit-daily-plan-handoff",
                residual="Sleep cannot mint a daily Fitbit plan.",
                ticket="FB-DAY-3",
                ticket_why="Fitbit daily quota owned by quota-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="monday-complexity-vs-rps",
                goal="Honor Monday.com GraphQL complexity budget; do not treat 429 as REST rps.",
                plan="Read rps-as-complexity, try 10 rps, then complexity remaining.",
                mod="moncmp",
                test_fn="test_complexity_not_rps",
                src_body=(
                    "def remaining(h):\n"
                    "    return int(h.get('X-RateLimit-Remaining') or 10)\n"
                ),
                test_body=(
                    "def test_complexity_not_rps():\n"
                    "    h = {'Complexity-Budget-Left': '1200', 'X-RateLimit-Remaining': '8'}\n"
                    "    assert remaining(h) == 1200\n"
                ),
                grep_pat="Complexity-Budget-Left|X-RateLimit-Remaining|monday",
                grep_hit="src/moncmp.py:2: return int(h.get('X-RateLimit-Remaining') or 10)",
                fail_msg="AssertionError: 8 == 1200; REST remaining used as GraphQL complexity",
                first_old="    return int(h.get('X-RateLimit-Remaining') or 10)",
                first_new="    return int(h.get('X-RateLimit-Remaining') or 10) * 100",
                first_obs="patched *100 (still REST remaining, not complexity)",
                still_msg="AssertionError: 800 != 1200; complexity is Complexity-Budget-Left",
                reread_obs="Monday GraphQL 429 is complexity budget, not REST rps",
                plan_change="Use Complexity-Budget-Left. REST remaining is not GraphQL. Not Retry-After catalog.",
                fix_new="    return int(h['Complexity-Budget-Left'])",
                fix_obs="patched complexity remaining",
                docs_url="https://developer.monday.com/api-reference/docs/rate-limits",
                docs_ok="Monday.com GraphQL uses a complexity budget, separate from REST rps.",
                docs_url2="https://developer.monday.com/api-reference/docs/error-codes",
                docs_ok2="Prefer Complexity-Budget-Left. Not Retry-After catalog. Not Shopify cost clone.",
                outcome="Complexity remaining matched 1200. REST rps unused (success).",
                domain="monday-graphql-complexity-vs-rest-rps",
                stack="Monday.com GraphQL complexity",
                seed="monday-complexity-vs-rps",
                residual="REST remaining is not complexity. Not Retry-After catalog.",
                coverage=85,
            ),
            _p(
                slug="airtable-formula-handoff",
                goal="Do not retry Airtable 422 formula compute as a sleepable 429 rps.",
                plan="Read formula-as-429, try 8s, then hand off formula compute.",
                mod="airfrm",
                test_fn="test_formula_not_rps",
                src_body=(
                    "def classify(status, err):\n"
                    "    return 'sleep_2s' if status in (429, 422) else 'ok'\n"
                ),
                test_body=(
                    "def test_formula_not_rps():\n"
                    "    assert classify(422, {'type': 'FORMULA_COMPUTE'}) != 'sleep_2s'\n"
                ),
                grep_pat="FORMULA_COMPUTE|429|sleep",
                grep_hit="src/airfrm.py:2: return 'sleep_2s' if status in (429, 422) else 'ok'",
                fail_msg="AssertionError: formula 422 slept as 429; compute is billing",
                first_old="    return 'sleep_2s' if status in (429, 422) else 'ok'",
                first_new="    return 'sleep_8s' if status in (429, 422) else 'ok'",
                first_obs="patched 8s (still treating formula compute as rps)",
                still_msg="AssertionError: sleep cannot mint Airtable formula compute quota",
                reread_obs="422 FORMULA_COMPUTE is a workspace compute cap, not REST rps",
                plan_change="Formula compute is billing. Handoff AT-FM-4. Not Retry-After catalog.",
                fix_new="    return 'handoff_AT-FM-4' if err.get('type')=='FORMULA_COMPUTE' else 'ok'",
                fix_obs="ticket filed. still rate-classed",
                docs_url="https://airtable.com/developers/web/api/rate-limits",
                docs_ok="Airtable formula compute errors are not the 5 rps REST bucket.",
                docs_url2="https://airtable.com/developers/web/api/errors",
                docs_ok2="Sleep cannot mint formula compute. Handoff AT-FM-4. Not Retry-After catalog.",
                outcome="Still rate-classed; formula compute is billing — handoff AT-FM-4.",
                domain="airtable-formula-compute-vs-rest-rps",
                stack="Airtable formula compute",
                seed="airtable-formula-handoff",
                residual="Sleep cannot mint formula compute.",
                ticket="AT-FM-4",
                ticket_why="Airtable formula compute owned by billing-plat",
                coverage=85,
            ),
        ),
    ],
    "queue-backpressure-factory": [
        (
            _p(
                slug="masstransit-prefetch-vs-timeout",
                goal="Bound MassTransit PrefetchCount; do not raise ReceiveTimeout to hide OCR lag.",
                plan="Read prefetch-as-timeout, try 90s, then PrefetchCount=16 plus ack.",
                mod="mt_pfc",
                test_fn="test_prefetch_not_receive",
                src_body=(
                    "def tune(lag):\n"
                    "    return {'receive_timeout_s': 30} if lag else {}\n"
                ),
                test_body=(
                    "def test_prefetch_not_receive():\n"
                    "    t = tune(True)\n"
                    "    assert t.get('PrefetchCount') == 16 and 'receive_timeout_s' not in t\n"
                ),
                grep_pat="receive_timeout_s|PrefetchCount|MassTransit",
                grep_hit="src/mt_pfc.py:2: return {'receive_timeout_s': 30} if lag else {}",
                fail_msg="AssertionError: lag stretched ReceiveTimeout; PrefetchCount still unbounded",
                first_old="    return {'receive_timeout_s': 30} if lag else {}",
                first_new="    return {'receive_timeout_s': 90} if lag else {}",
                first_obs="patched 90s (still a timeout integer)",
                still_msg="AssertionError: timeout integer cannot bound PrefetchCount",
                reread_obs="MassTransit default PrefetchCount is unbounded on OCR consumers",
                plan_change="PrefetchCount=16 plus ack. ReceiveTimeout is not a queue bound.",
                fix_new="    return {'PrefetchCount': 16, 'ack': True} if lag else {}",
                fix_obs="patched PrefetchCount=16",
                docs_url="https://masstransit.io/documentation/configuration/transports/rabbitmq",
                docs_ok="PrefetchCount bounds unacked deliveries; ReceiveTimeout is a clock.",
                docs_url2="https://masstransit.io/documentation/configuration/endpoint",
                docs_ok2="Use a finite prefetch, not a longer receive clock. Not Cloud Tasks. Not Camel SEDA.",
                outcome="Prefetch 16 plus ack drained lag. ReceiveTimeout unused (success).",
                domain="masstransit-prefetchcount-vs-receive-timeout",
                stack="MassTransit PrefetchCount",
                seed="masstransit-prefetch-vs-timeout",
                residual="ReceiveTimeout is not a queue bound. Not Camel/Taskiq clones.",
                coverage=86,
            ),
            _p(
                slug="storm-spout-pending-handoff",
                goal="Do not raise Apache Storm tuple timeout to hide a maxSpoutPending stall.",
                plan="Read pending-as-timeout, try 60s, then hand off maxSpoutPending.",
                mod="st_msp",
                test_fn="test_pending_not_timeout",
                src_body=(
                    "def tune(blocked):\n"
                    "    return {'tuple_timeout_s': 30} if blocked else {}\n"
                ),
                test_body=(
                    "def test_pending_not_timeout():\n"
                    "    assert 'tuple_timeout_s' not in tune(True)\n"
                ),
                grep_pat="tuple_timeout_s|maxSpoutPending|storm",
                grep_hit="src/st_msp.py:2: return {'tuple_timeout_s': 30} if blocked else {}",
                fail_msg="AssertionError: spout stall slept tuple timeout; maxSpoutPending still 0",
                first_old="    return {'tuple_timeout_s': 30} if blocked else {}",
                first_new="    return {'tuple_timeout_s': 60} if blocked else {}",
                first_obs="patched 60s (still a timeout integer)",
                still_msg="AssertionError: tuple timeout cannot mint topology.max.spout.pending",
                reread_obs="topology.max.spout.pending=0 is unbounded; OCR spout blocks",
                plan_change="maxSpoutPending is platform. Handoff ST-MSP-3.",
                fix_new="    return {'handoff': 'ST-MSP-3'} if blocked else {}",
                fix_obs="ticket filed. still timeout-classed",
                docs_url="https://storm.apache.org/releases/2.6.0/Configuration.html",
                docs_ok="max.spout.pending is topology credit, not tuple timeout.",
                docs_url2="https://storm.apache.org/releases/2.6.0/Guaranteeing-message-processing.html",
                docs_ok2="Timeout cannot mint spout pending. Handoff ST-MSP-3. Not Cloud Tasks. Not ZeroMQ HWM.",
                outcome="Still timeout-classed; maxSpoutPending is platform — handoff ST-MSP-3.",
                domain="storm-max-spout-pending-vs-tuple-timeout",
                stack="Apache Storm maxSpoutPending",
                seed="storm-spout-pending-handoff",
                residual="Tuple timeout is not spout credit.",
                ticket="ST-MSP-3",
                ticket_why="topology.max.spout.pending owned by stream-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="debezium-queue-size-vs-poll",
                goal="Bound Debezium max.queue.size; do not raise poll.interval.ms to hide CDC lag.",
                plan="Read queue-as-poll, try 2000ms, then max.queue.size=8192 plus pause.",
                mod="dbz_qs",
                test_fn="test_queue_not_poll",
                src_body=(
                    "def tune(lag):\n"
                    "    return {'poll.interval.ms': 500} if lag else {}\n"
                ),
                test_body=(
                    "def test_queue_not_poll():\n"
                    "    t = tune(True)\n"
                    "    assert t.get('max.queue.size') == 8192 and 'poll.interval.ms' not in t\n"
                ),
                grep_pat="poll.interval.ms|max.queue.size|debezium",
                grep_hit="src/dbz_qs.py:2: return {'poll.interval.ms': 500} if lag else {}",
                fail_msg="AssertionError: lag stretched poll.interval; max.queue.size still Integer.MAX",
                first_old="    return {'poll.interval.ms': 500} if lag else {}",
                first_new="    return {'poll.interval.ms': 2000} if lag else {}",
                first_obs="patched 2000ms (still a timeout integer)",
                still_msg="AssertionError: poll.interval.ms cannot bound max.queue.size",
                reread_obs="Debezium change-event queue default is unbounded vs OCR snapshot",
                plan_change="max.queue.size=8192 plus pause. Poll interval is not a queue bound.",
                fix_new="    return {'max.queue.size': 8192, 'pause': True} if lag else {}",
                fix_obs="patched max.queue.size=8192",
                docs_url="https://debezium.io/documentation/reference/stable/connectors/postgresql.html",
                docs_ok="max.queue.size bounds change events; poll.interval.ms is a clock.",
                docs_url2="https://debezium.io/documentation/reference/stable/configuration/signalling.html",
                docs_ok2="Use a finite queue, not a longer poll clock. Not Cloud Tasks. Not Camel SEDA.",
                outcome="Queue 8192 plus pause drained CDC lag. Poll unused (success).",
                domain="debezium-max-queue-size-vs-poll-interval",
                stack="Debezium max.queue.size",
                seed="debezium-queue-size-vs-poll",
                residual="poll.interval.ms is not a queue bound. Not Kafka max.poll clone.",
                coverage=85,
            ),
            _p(
                slug="hazelcast-iqueue-handoff",
                goal="Do not raise Hazelcast offer timeout to hide an IQueue remainingCapacity stall.",
                plan="Read capacity-as-timeout, try 15s, then hand off remainingCapacity.",
                mod="hz_iqc",
                test_fn="test_capacity_not_offer",
                src_body=(
                    "def tune(blocked):\n"
                    "    return {'offer_timeout_s': 5} if blocked else {}\n"
                ),
                test_body=(
                    "def test_capacity_not_offer():\n"
                    "    assert 'offer_timeout_s' not in tune(True)\n"
                ),
                grep_pat="offer_timeout_s|remainingCapacity|IQueue",
                grep_hit="src/hz_iqc.py:2: return {'offer_timeout_s': 5} if blocked else {}",
                fail_msg="AssertionError: IQueue stall slept offer timeout; capacity still Integer.MAX",
                first_old="    return {'offer_timeout_s': 5} if blocked else {}",
                first_new="    return {'offer_timeout_s': 15} if blocked else {}",
                first_obs="patched 15s (still a timeout integer)",
                still_msg="AssertionError: offer timeout cannot mint IQueue remainingCapacity",
                reread_obs="Hazelcast IQueue max-size=0 is unbounded; OCR publisher blocks",
                plan_change="IQueue max-size is platform. Handoff HZ-IQ-4.",
                fix_new="    return {'handoff': 'HZ-IQ-4'} if blocked else {}",
                fix_obs="ticket filed. still timeout-classed",
                docs_url="https://docs.hazelcast.com/hazelcast/latest/data-structures/queue",
                docs_ok="Queue max-size is cluster capacity, not offer timeout.",
                docs_url2="https://docs.hazelcast.com/hazelcast/latest/data-structures/queue#queue-configuration",
                docs_ok2="Timeout cannot mint remainingCapacity. Handoff HZ-IQ-4. Not Cloud Tasks. Not ZeroMQ HWM.",
                outcome="Still timeout-classed; IQueue max-size is platform — handoff HZ-IQ-4.",
                domain="hazelcast-iqueue-capacity-vs-offer-timeout",
                stack="Hazelcast IQueue max-size",
                seed="hazelcast-iqueue-handoff",
                residual="Offer timeout is not queue capacity.",
                ticket="HZ-IQ-4",
                ticket_why="IQueue max-size owned by cache-plat",
                coverage=85,
            ),
        ),
        (
            _p(
                slug="disruptor-buffer-vs-timeout",
                goal="Bound LMAX Disruptor bufferSize; do not raise wait timeout to hide OCR lag.",
                plan="Read buffer-as-timeout, try 5s, then bufferSize=1024 plus block.",
                mod="lmxdsr",
                test_fn="test_buffer_not_wait",
                src_body=(
                    "def tune(lag):\n"
                    "    return {'wait_timeout_s': 1} if lag else {}\n"
                ),
                test_body=(
                    "def test_buffer_not_wait():\n"
                    "    t = tune(True)\n"
                    "    assert t.get('bufferSize') == 1024 and 'wait_timeout_s' not in t\n"
                ),
                grep_pat="wait_timeout_s|bufferSize|disruptor",
                grep_hit="src/lmxdsr.py:2: return {'wait_timeout_s': 1} if lag else {}",
                fail_msg="AssertionError: lag stretched wait timeout; ring buffer still default",
                first_old="    return {'wait_timeout_s': 1} if lag else {}",
                first_new="    return {'wait_timeout_s': 5} if lag else {}",
                first_obs="patched 5s (still a timeout integer)",
                still_msg="AssertionError: timeout integer cannot bound Disruptor bufferSize",
                reread_obs="Disruptor default buffer is small; OCR publisher needs a finite 1024 ring",
                plan_change="bufferSize=1024 plus block. Wait timeout is not a queue bound.",
                fix_new="    return {'bufferSize': 1024, 'block': True} if lag else {}",
                fix_obs="patched bufferSize=1024",
                docs_url="https://lmax-exchange.github.io/disruptor/user-guide/index.html",
                docs_ok="bufferSize is the ring capacity; wait timeout is a sequencer clock.",
                docs_url2="https://github.com/LMAX-Exchange/disruptor/wiki/Getting-Started",
                docs_ok2="Use a finite power-of-two buffer, not a longer wait. Not Cloud Tasks. Not Camel SEDA.",
                outcome="Buffer 1024 plus block drained lag. Wait unused (success).",
                domain="lmax-disruptor-buffersize-vs-wait-timeout",
                stack="LMAX Disruptor bufferSize",
                seed="disruptor-buffer-vs-timeout",
                residual="Wait timeout is not a ring bound. Not Camel/MassTransit clones.",
                coverage=84,
            ),
            _p(
                slug="chronicle-cycle-handoff",
                goal="Do not raise Chronicle Queue cycle timeout to hide a roll-cycle stall.",
                plan="Read cycle-as-timeout, try 60s, then hand off roll cycle.",
                mod="chrqcy",
                test_fn="test_cycle_not_timeout",
                src_body=(
                    "def tune(blocked):\n"
                    "    return {'cycle_timeout_s': 10} if blocked else {}\n"
                ),
                test_body=(
                    "def test_cycle_not_timeout():\n"
                    "    assert 'cycle_timeout_s' not in tune(True)\n"
                ),
                grep_pat="cycle_timeout_s|rollCycle|chronicle",
                grep_hit="src/chrqcy.py:2: return {'cycle_timeout_s': 10} if blocked else {}",
                fail_msg="AssertionError: roll-cycle stall slept cycle timeout; HOURLY unused",
                first_old="    return {'cycle_timeout_s': 10} if blocked else {}",
                first_new="    return {'cycle_timeout_s': 60} if blocked else {}",
                first_obs="patched 60s (still a timeout integer)",
                still_msg="AssertionError: cycle timeout cannot mint Chronicle rollCycle",
                reread_obs="Chronicle Queue rollCycle is a store layout; timeout is not a cycle",
                plan_change="rollCycle is platform. Handoff CQ-RC-5.",
                fix_new="    return {'handoff': 'CQ-RC-5'} if blocked else {}",
                fix_obs="ticket filed. still timeout-classed",
                docs_url="https://github.com/OpenHFT/Chronicle-Queue",
                docs_ok="rollCycle is file layout, not a wait timeout.",
                docs_url2="https://github.com/OpenHFT/Chronicle-Queue/blob/ea/docs/FAQ.adoc",
                docs_ok2="Timeout cannot mint rollCycle. Handoff CQ-RC-5. Not Cloud Tasks. Not ZeroMQ HWM.",
                outcome="Still timeout-classed; rollCycle is platform — handoff CQ-RC-5.",
                domain="chronicle-queue-rollcycle-vs-cycle-timeout",
                stack="Chronicle Queue rollCycle",
                seed="chronicle-cycle-handoff",
                residual="Cycle timeout is not rollCycle.",
                ticket="CQ-RC-5",
                ticket_why="Chronicle rollCycle owned by persist-plat",
                coverage=84,
            ),
        ),
    ],
    "csv-excel-ingest-factory": [
        (
            _p(
                slug="xlsx-richvalue-vs-display",
                goal="Read rdrichvalue.xml cached invoice amounts, not the empty display cell.",
                plan="Read display-as-rich, try shared strings, then rdrichvalue.",
                mod="xlsxrv",
                test_fn="test_richvalue_not_display",
                src_body=(
                    "def amount(ws):\n"
                    "    return ws.cell('C4').display\n"
                ),
                test_body=(
                    "def test_richvalue_not_display():\n"
                    "    assert amount(ws) == '42.50'\n"
                ),
                grep_pat="rdrichvalue|display|richData",
                grep_hit="src/xlsxrv.py:2: return ws.cell('C4').display",
                fail_msg="AssertionError: '' == '42.50'; rich value lives in rdrichvalue.xml",
                first_old="    return ws.cell('C4').display",
                first_new="    return ws.cell('C4').sst or ''",
                first_obs="patched sst (still empty display, not rdrichvalue)",
                still_msg="AssertionError: sst still misses xl/richData/rdrichvalue.xml",
                reread_obs="xl/richData/rdrichvalue.xml stores amt=42.50; C4 is an empty rich stub",
                plan_change="Read rdrichvalue cache. Display cells are not the invoice.",
                fix_new="    return ws.rich_value('C4')",
                fix_obs="patched rdrichvalue cache",
                docs_url="https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/05d30343-285b-43a9-81c1-56c5731e6c6b",
                docs_ok="Rich Data parts hold typed values; display cells can be empty stubs.",
                docs_url2="https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/",
                docs_ok2="Invoice amt lives in rdrichvalue.xml. Not quoted-newline, not WPS .et, not queryTable.",
                outcome="rdrichvalue cache recovered 42.50. Display unused (success).",
                domain="xlsx-rdrichvalue-vs-display-cell",
                stack="OOXML rdrichvalue",
                seed="xlsx-richvalue-vs-display",
                residual="Not queryTable/customXml clones. Not Kingsoft .et.",
                coverage=87,
            ),
            _p(
                slug="originlab-opju-handoff",
                goal="Do not parse OriginLab .opju as xlsx ZIP.",
                plan="Read opju-as-xlsx, try zipfile, then hand off Origin reader.",
                mod="opjbin",
                test_fn="test_opju_not_xlsx",
                src_body=(
                    "def load(path):\n"
                    "    import zipfile\n"
                    "    return zipfile.ZipFile(path).namelist()\n"
                ),
                test_body=(
                    "def test_opju_not_xlsx():\n"
                    "    assert not str(load('invoices.opju')).startswith('xl/')\n"
                ),
                grep_pat="ZipFile|\\.opju|originlab",
                grep_hit="src/opjbin.py:3: return zipfile.ZipFile(path).namelist()",
                fail_msg="AssertionError: OriginLab magic opened as ZIP; BadZipFile swallowed",
                first_old="    return zipfile.ZipFile(path).namelist()",
                first_new="    return zipfile.ZipFile(path, mode='r').namelist() or ['xl/worksheets']",
                first_obs="patched default sheet (still ZIP, still not .opju)",
                still_msg="AssertionError: forcing xl/ paths cannot decode OriginLab OPJU",
                reread_obs="OPJU is OriginLab Unicode project; not OOXML",
                plan_change="Binary .opju is stats-plat. Handoff OPJ-BIN-5.",
                fix_new="    return {'handoff': 'OPJ-BIN-5'}",
                fix_obs="ticket filed. still zip-classed",
                docs_url="https://www.originlab.com/doc/Origin-Help/OPJU-File",
                docs_ok="Origin project files (.opju) are a proprietary container, not OOXML.",
                docs_url2="https://www.originlab.com/doc/Origin-Help/File-Types",
                docs_ok2="Need Origin reader. Handoff OPJ-BIN-5. Not Kingsoft .et. Not JMP/Minitab clones.",
                outcome="Still zip-classed; .opju is binary — handoff OPJ-BIN-5.",
                domain="originlab-opju-binary-vs-xlsx-zip",
                stack="OriginLab .opju",
                seed="originlab-opju-handoff",
                residual="Not JMP/Minitab/SAS clones.",
                ticket="OPJ-BIN-5",
                ticket_why=".opju binary ingest owned by stats-plat",
                coverage=87,
            ),
        ),
        (
            _p(
                slug="xlsx-valuemetadata-vs-cell",
                goal="Read metadata.xml valueMetadata for invoice types, not the untyped cell text.",
                plan="Read cell-as-meta, try number format, then valueMetadata.",
                mod="xlsxvm",
                test_fn="test_valuemeta_not_cell",
                src_body=(
                    "def kind(ws):\n"
                    "    return ws.cell('D1').text\n"
                ),
                test_body=(
                    "def test_valuemeta_not_cell():\n"
                    "    assert kind(ws) == 'InvoiceAmount'\n"
                ),
                grep_pat="valueMetadata|metadata.xml|numFmt",
                grep_hit="src/xlsxvm.py:2: return ws.cell('D1').text",
                fail_msg="AssertionError: '42.50' == 'InvoiceAmount'; type lives in valueMetadata",
                first_old="    return ws.cell('D1').text",
                first_new="    return ws.cell('D1').num_fmt or ''",
                first_obs="patched numFmt (still cell, not metadata.xml)",
                still_msg="AssertionError: numFmt is #,##0.00; type is valueMetadata",
                reread_obs="xl/metadata.xml valueMetadata maps D1 to InvoiceAmount rich type",
                plan_change="Read valueMetadata. Cell text is the untyped display.",
                fix_new="    return ws.value_metadata('D1')",
                fix_obs="patched valueMetadata",
                docs_url="https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/07d607ac-a8e7-4e1d-a8fb-0e1c2c4d0e4d",
                docs_ok="valueMetadata indexes rich types; cell text is untyped display.",
                docs_url2="https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/",
                docs_ok2="Invoice type lives in metadata.xml. Not quoted-newline, not WPS .et, not rdrichvalue clone.",
                outcome="valueMetadata recovered InvoiceAmount. Cell text unused (success).",
                domain="xlsx-valuemetadata-vs-untyped-cell",
                stack="OOXML valueMetadata",
                seed="xlsx-valuemetadata-vs-cell",
                residual="Not rdrichvalue/queryTable clones. Not Kingsoft .et.",
                coverage=86,
            ),
            _p(
                slug="sigmaplot-jnb-handoff",
                goal="Do not parse SigmaPlot .jnb as CSV.",
                plan="Read jnb-as-csv, try latin1, then hand off JNB reader.",
                mod="jnbbin",
                test_fn="test_jnb_not_csv",
                src_body=(
                    "def load(path):\n"
                    "    return open(path, newline='').read().split(',')\n"
                ),
                test_body=(
                    "def test_jnb_not_csv():\n"
                    "    assert load('invoices.jnb') != open('invoices.jnb').read().split(',')\n"
                ),
                grep_pat="\\.jnb|read\\(\\).*split|sigmaplot",
                grep_hit="src/jnbbin.py:2: return open(path, newline='').read().split(',')",
                fail_msg="AssertionError: JNB magic parsed as CSV; notebook header lost",
                first_old="    return open(path, newline='').read().split(',')",
                first_new="    return open(path, encoding='latin1').read().split(',')",
                first_obs="patched latin1 (still text split, still not .jnb)",
                still_msg="AssertionError: latin1 cannot decode SigmaPlot notebook",
                reread_obs="SigmaPlot .jnb is a binary notebook; need SigmaPlot reader",
                plan_change="Binary .jnb is stats-plat. Handoff JNB-BIN-6.",
                fix_new="    return {'handoff': 'JNB-BIN-6'}",
                fix_obs="ticket filed. still csv-split",
                docs_url="https://systatsoftware.com/products/sigmaplot/",
                docs_ok="SigmaPlot notebooks (.jnb) are binary, not CSV.",
                docs_url2="https://systatsoftware.com/products/sigmaplot/sigmaplot-file-formats/",
                docs_ok2="Need SigmaPlot reader. Handoff JNB-BIN-6. Not Kingsoft .et. Not Minitab clone.",
                outcome="Still csv-split; .jnb is binary — handoff JNB-BIN-6.",
                domain="sigmaplot-jnb-binary-vs-csv-text",
                stack="SigmaPlot .jnb",
                seed="sigmaplot-jnb-handoff",
                residual="latin1 is not a SigmaPlot reader. Not Minitab/JMP clones.",
                ticket="JNB-BIN-6",
                ticket_why=".jnb binary ingest owned by stats-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="xlsx-slicercache-vs-used",
                goal="Read slicerCache cached invoice filters, not the empty worksheet used range.",
                plan="Read used-as-slicer, try autofilter, then slicerCache.",
                mod="xlsxsl",
                test_fn="test_slicer_not_used",
                src_body=(
                    "def filters(ws):\n"
                    "    return ws.used_range\n"
                ),
                test_body=(
                    "def test_slicer_not_used():\n"
                    "    assert filters(ws) == 'slicerCache1'\n"
                ),
                grep_pat="slicerCache|used_range|autoFilter",
                grep_hit="src/xlsxsl.py:2: return ws.used_range",
                fail_msg="AssertionError: used range empty; invoice filters live in slicerCache",
                first_old="    return ws.used_range",
                first_new="    return ws.auto_filter",
                first_obs="patched autoFilter (still the sheet, not slicerCache)",
                still_msg="AssertionError: autoFilter is empty; cache is slicerCache1",
                reread_obs="xl/slicerCaches/slicerCache1.xml caches the invoice filter items",
                plan_change="Read slicerCache. Used range is the empty display.",
                fix_new="    return ws.slicer_cache('slicerCache1')",
                fix_obs="patched slicerCache",
                docs_url="https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/6f12b7e1-3e4a-4a7a-9d0e-1c0e8e0e0e0e",
                docs_ok="slicerCache holds filter items; UsedRange can be empty.",
                docs_url2="https://learn.microsoft.com/en-us/openspecs/office_standards/ms-xlsx/",
                docs_ok2="slicerCache1.xml holds invoice filters. Not quoted-newline, not queryTable clone.",
                outcome="slicerCache ingested invoice filters. Used range unused (success).",
                domain="xlsx-slicercache-vs-used-range",
                stack="OOXML slicerCache",
                seed="xlsx-slicercache-vs-used",
                residual="Not queryTable/richvalue clones. Not Kingsoft .et.",
                coverage=84,
            ),
            _p(
                slug="prism-pzfx-handoff",
                goal="Do not parse GraphPad Prism .pzfx as CSV.",
                plan="Read pzfx-as-csv, try xml, then hand off Prism reader.",
                mod="pzfxbn",
                test_fn="test_pzfx_not_csv",
                src_body=(
                    "def load(path):\n"
                    "    return open(path, newline='').read().split(',')\n"
                ),
                test_body=(
                    "def test_pzfx_not_csv():\n"
                    "    assert load('invoices.pzfx') != open('invoices.pzfx').read().split(',')\n"
                ),
                grep_pat="\\.pzfx|read\\(\\).*split|prism",
                grep_hit="src/pzfxbn.py:2: return open(path, newline='').read().split(',')",
                fail_msg="AssertionError: PZFX magic parsed as CSV; Prism table lost",
                first_old="    return open(path, newline='').read().split(',')",
                first_new="    return open(path, encoding='utf-8').read().split('<Table>')",
                first_obs="patched xml split (still text split, still not Prism tables)",
                still_msg="AssertionError: tag split cannot decode Prism .pzfx tables",
                reread_obs="GraphPad Prism .pzfx is a proprietary XML workbook; need Prism reader",
                plan_change="Prism .pzfx is stats-plat. Handoff PZFX-7.",
                fix_new="    return {'handoff': 'PZFX-7'}",
                fix_obs="ticket filed. still csv-split",
                docs_url="https://www.graphpad.com/guides/prism/latest/user-guide/using_prism_files.htm",
                docs_ok="Prism files (.pzfx) are a GraphPad workbook, not CSV.",
                docs_url2="https://www.graphpad.com/guides/prism/latest/user-guide/",
                docs_ok2="Need Prism reader. Handoff PZFX-7. Not Kingsoft .et. Not SigmaPlot clone.",
                outcome="Still csv-split; .pzfx is Prism — handoff PZFX-7.",
                domain="graphpad-prism-pzfx-vs-csv-text",
                stack="GraphPad Prism .pzfx",
                seed="prism-pzfx-handoff",
                residual="Tag split is not a Prism reader. Not SigmaPlot clone.",
                ticket="PZFX-7",
                ticket_why=".pzfx Prism ingest owned by stats-plat",
                coverage=84,
            ),
        ),
    ],
    "websocket-reconnect-factory": [
        (
            _p(
                slug="meteor-ddp-resume-token",
                goal="Resume Meteor DDP with resumeToken; do not open a second connect.",
                plan="Read connect-as-resume, try new session, then resumeToken.",
                mod="metddp",
                test_fn="test_token_not_reconnect",
                src_body=(
                    "def resume(sess):\n"
                    "    return {'connect': sess}\n"
                ),
                test_body=(
                    "def test_token_not_reconnect():\n"
                    "    assert 'resumeToken' in resume('inv')\n"
                ),
                grep_pat="resumeToken|connect|ddp",
                grep_hit="src/metddp.py:2: return {'connect': sess}",
                fail_msg="AssertionError: second connect created a new DDP session; token unused",
                first_old="    return {'connect': sess}",
                first_new="    return {'connect': sess, 'session': 'new'}",
                first_obs="patched new session (still a second connect)",
                still_msg="AssertionError: new session is not resumeToken",
                reread_obs="Meteor DDP connect with resumeToken restores the same session",
                plan_change="Pass resumeToken. A second connect is not resume. Not cookie-replay.",
                fix_new="    return {'resumeToken': sess}",
                fix_obs="patched resumeToken",
                docs_url="https://github.com/meteor/meteor/blob/devel/packages/ddp/DDP.md",
                docs_ok="DDP connect accepts a session/resume token; a bare connect is a new seat.",
                docs_url2="https://docs.meteor.com/api/connections.html",
                docs_ok2="Use resumeToken. Not cookie-replay. Not Colyseus reconnectionToken clone.",
                outcome="resumeToken restored the DDP session. Reconnect unused (success).",
                domain="meteor-ddp-resume-token-vs-second-connect",
                stack="Meteor DDP resumeToken",
                seed="meteor-ddp-resume-token",
                residual="Not cookie-replay. Not Colyseus clone.",
                coverage=86,
            ),
            _p(
                slug="supabase-realtime-timeout-handoff",
                goal="Do not treat Supabase Realtime server heartbeat timeout as a client ping miss.",
                plan="Read heartbeat-as-ping, try ping 10s, then hand off heartbeat timeout.",
                mod="sbrthb",
                test_fn="test_heartbeat_not_ping",
                src_body=(
                    "def tune(drop):\n"
                    "    return {'client_ping_s': 15} if drop else {}\n"
                ),
                test_body=(
                    "def test_heartbeat_not_ping():\n"
                    "    assert 'client_ping_s' not in tune(True)\n"
                ),
                grep_pat="heartbeat_interval|client_ping_s|supabase",
                grep_hit="src/sbrthb.py:2: return {'client_ping_s': 15} if drop else {}",
                fail_msg="AssertionError: Realtime heartbeat timeout dropped WS; client ping unused",
                first_old="    return {'client_ping_s': 15} if drop else {}",
                first_new="    return {'client_ping_s': 10} if drop else {}",
                first_obs="patched ping 10s (still client, not heartbeat)",
                still_msg="AssertionError: client ping cannot raise Realtime heartbeat_interval",
                reread_obs="Supabase Realtime heartbeat_interval is server-side; ping is not keep-channel",
                plan_change="Heartbeat timeout is Realtime. Handoff SB-HB-3.",
                fix_new="    return {'handoff': 'SB-HB-3'} if drop else {}",
                fix_obs="ticket filed. still ping-classed",
                docs_url="https://supabase.com/docs/guides/realtime/protocol",
                docs_ok="Realtime heartbeat is server configuration, not a client ping.",
                docs_url2="https://supabase.com/docs/guides/realtime/protocol#heartbeats",
                docs_ok2="Timeout is realtime-plat. Handoff SB-HB-3. Not cookie-replay. Not Janus clone.",
                outcome="Still ping-classed; heartbeat is Realtime — handoff SB-HB-3.",
                domain="supabase-realtime-heartbeat-vs-client-ping",
                stack="Supabase Realtime heartbeat",
                seed="supabase-realtime-timeout-handoff",
                residual="Ping cannot set Realtime heartbeat.",
                ticket="SB-HB-3",
                ticket_why="Realtime heartbeat_interval owned by realtime-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="anycable-restore-session",
                goal="Restore AnyCable with restore_session; do not open a second subscribe.",
                plan="Read subscribe-as-restore, try new identifier, then restore_session.",
                mod="anycbl",
                test_fn="test_restore_not_resub",
                src_body=(
                    "def resume(ch):\n"
                    "    return {'subscribe': ch}\n"
                ),
                test_body=(
                    "def test_restore_not_resub():\n"
                    "    assert 'restore_session' in resume('inv')\n"
                ),
                grep_pat="restore_session|subscribe|anycable",
                grep_hit="src/anycbl.py:2: return {'subscribe': ch}",
                fail_msg="AssertionError: second subscribe created a new stream; restore unused",
                first_old="    return {'subscribe': ch}",
                first_new="    return {'subscribe': ch, 'identifier': 'new'}",
                first_obs="patched new identifier (still a second subscribe)",
                still_msg="AssertionError: new identifier is not restore_session",
                reread_obs="AnyCable restore_session resumes the same Action Cable stream",
                plan_change="Pass restore_session. A second subscribe is not resume. Not cookie-replay.",
                fix_new="    return {'restore_session': ch}",
                fix_obs="patched restore_session",
                docs_url="https://docs.anycable.io/anycable-go/rpc",
                docs_ok="restore_session resumes the RPC session; subscribe() creates a new stream.",
                docs_url2="https://docs.anycable.io/anycable-go/rpc#restore_session",
                docs_ok2="Use restore_session. Not cookie-replay. Not Action Cable confirm clone.",
                outcome="restore_session restored the stream. Resubscribe unused (success).",
                domain="anycable-restore-session-vs-second-subscribe",
                stack="AnyCable restore_session",
                seed="anycable-restore-session",
                residual="Not cookie-replay. Not Action Cable confirm clone.",
                coverage=85,
            ),
            _p(
                slug="reverb-activity-timeout-handoff",
                goal="Do not treat Laravel Reverb activity timeout as a client ping miss.",
                plan="Read activity-as-ping, try ping 5s, then hand off activity timeout.",
                mod="lrvato",
                test_fn="test_activity_not_ping",
                src_body=(
                    "def tune(drop):\n"
                    "    return {'client_ping_s': 5} if drop else {}\n"
                ),
                test_body=(
                    "def test_activity_not_ping():\n"
                    "    assert 'client_ping_s' not in tune(True)\n"
                ),
                grep_pat="activity_timeout|client_ping_s|reverb",
                grep_hit="src/lrvato.py:2: return {'client_ping_s': 5} if drop else {}",
                fail_msg="AssertionError: Reverb activity timeout dropped WS; ping unused",
                first_old="    return {'client_ping_s': 5} if drop else {}",
                first_new="    return {'client_ping_s': 10} if drop else {}",
                first_obs="patched ping 10s (still client, not activity)",
                still_msg="AssertionError: client ping cannot raise Reverb activity_timeout",
                reread_obs="Reverb activity_timeout is server-side; ping is not keep-connection",
                plan_change="Activity timeout is Reverb. Handoff LR-AT-2.",
                fix_new="    return {'handoff': 'LR-AT-2'} if drop else {}",
                fix_obs="ticket filed. still ping-classed",
                docs_url="https://laravel.com/docs/reverb",
                docs_ok="Reverb activity timeout is server configuration, not a client ping.",
                docs_url2="https://laravel.com/docs/reverb#scaling",
                docs_ok2="Timeout is edge-plat. Handoff LR-AT-2. Not cookie-replay. Not PartyKit clone.",
                outcome="Still ping-classed; activity timeout is Reverb — handoff LR-AT-2.",
                domain="laravel-reverb-activity-timeout-vs-client-ping",
                stack="Laravel Reverb activity timeout",
                seed="reverb-activity-timeout-handoff",
                residual="Ping cannot set Reverb activity timeout.",
                ticket="LR-AT-2",
                ticket_why="Reverb activity_timeout owned by edge-plat",
                coverage=85,
            ),
        ),
    ],
    "email-webhook-retry-factory": [
        (
            _p(
                slug="mailtrap-id-plus-event",
                goal="Dedupe Mailtrap webhooks on (event_id, type), not recipient.",
                plan="Read rcpt-as-pk, try message_id only, then (event_id, type).",
                mod="mtpevt",
                test_fn="test_id_plus_type",
                src_body=(
                    "def pk(ev):\n"
                    "    return ev['recipient']\n"
                ),
                test_body=(
                    "def test_id_plus_type():\n"
                    "    assert pk({'event_id': 'e1', 'type': 'delivery', 'recipient': 'a@b'}) == ('e1', 'delivery')\n"
                ),
                grep_pat="event_id|recipient|type",
                grep_hit="src/mtpevt.py:2: return ev['recipient']",
                fail_msg="AssertionError: recipient PK collapsed two events for the same inbox",
                first_old="    return ev['recipient']",
                first_new="    return ev.get('message_id') or ev['recipient']",
                first_obs="patched message_id (still missing type; delivery+bounce collide)",
                still_msg="AssertionError: message_id without type still collides delivery vs bounce",
                reread_obs="Mailtrap webhook PK is (event_id, type); recipient is the inbox",
                plan_change="PK (event_id, type). Recipient is the inbox. Not invoice-row-dup.",
                fix_new="    return (ev['event_id'], ev['type'])",
                fix_obs="patched (event_id, type)",
                docs_url="https://help.mailtrap.io/article/123-webhooks",
                docs_ok="Mailtrap webhook events are unique on event_id plus type, not email.",
                docs_url2="https://api-docs.mailtrap.io/docs/mailtrap-api-docs/5b5e5e5e5e5e5e5e5e5e5e5e",
                docs_ok2="Do not key on recipient. Not invoice-row-dup. Not SMTP.com clone.",
                outcome="(event_id, type) deduped deliveries. Recipient unused (success).",
                domain="mailtrap-event-id-plus-type",
                stack="Mailtrap email webhooks",
                seed="mailtrap-id-plus-event",
                residual="Recipient is not PK. Not SMTP.com/MailPace clones.",
                coverage=86,
            ),
            _p(
                slug="aweber-broadcast-handoff",
                goal="Do not treat an AWeber broadcast_id as a unique email event.",
                plan="Read broadcast-as-event, try subscriber, then hand off broadcast grain.",
                mod="awbcst",
                test_fn="test_broadcast_not_event",
                src_body=(
                    "def pk(ev):\n"
                    "    return ev['broadcast_id']\n"
                ),
                test_body=(
                    "def test_broadcast_not_event():\n"
                    "    assert pk({'broadcast_id': 'b1', 'subscriber_id': 's1', 'type': 'open'}) != 'b1'\n"
                ),
                grep_pat="broadcast_id|subscriber_id|aweber",
                grep_hit="src/awbcst.py:2: return ev['broadcast_id']",
                fail_msg="AssertionError: broadcast_id collapsed every open in the send",
                first_old="    return ev['broadcast_id']",
                first_new="    return ev.get('subscriber_id') or ev['broadcast_id']",
                first_obs="patched subscriber (still not event grain; campaign unique)",
                still_msg="AssertionError: subscriber_id still shares the broadcast grain",
                reread_obs="AWeber broadcast_id is campaign grain; event ids are platform",
                plan_change="broadcast_id is campaign grain. Handoff AW-BC-4.",
                fix_new="    return {'handoff': 'AW-BC-4'}",
                fix_obs="ticket filed. still broadcast-classed",
                docs_url="https://api.aweber.com/#tag/Webhooks",
                docs_ok="broadcast_id identifies the send, not a unique tracking event.",
                docs_url2="https://api.aweber.com/#tag/Broadcasts",
                docs_ok2="Event grain is ESP-plat. Handoff AW-BC-4. Not invoice-row-dup. Not CiviCRM clone.",
                outcome="Still broadcast-classed; campaign grain is AWeber — handoff AW-BC-4.",
                domain="aweber-broadcast-id-vs-event-id",
                stack="AWeber broadcast webhooks",
                seed="aweber-broadcast-handoff",
                residual="broadcast_id is campaign grain.",
                ticket="AW-BC-4",
                ticket_why="AWeber broadcast event grain owned by esp-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="beehiiv-id-plus-event",
                goal="Dedupe Beehiiv webhooks on (id, event), not email address.",
                plan="Read email-as-pk, try post_id only, then (id, event).",
                mod="bheevt",
                test_fn="test_id_plus_event",
                src_body=(
                    "def pk(ev):\n"
                    "    return ev['email']\n"
                ),
                test_body=(
                    "def test_id_plus_event():\n"
                    "    assert pk({'id': 'w1', 'event': 'email.opened', 'email': 'a@b'}) == ('w1', 'email.opened')\n"
                ),
                grep_pat="email.opened|email'|post_id",
                grep_hit="src/bheevt.py:2: return ev['email']",
                fail_msg="AssertionError: email PK collapsed open and bounce for one subscriber",
                first_old="    return ev['email']",
                first_new="    return ev.get('post_id') or ev['email']",
                first_obs="patched post_id (still missing event; open+click collide)",
                still_msg="AssertionError: post_id without event still collides open vs click",
                reread_obs="Beehiiv webhook PK is (id, event); email is the subscriber",
                plan_change="PK (id, event). Email is the subscriber. Not invoice-row-dup.",
                fix_new="    return (ev['id'], ev['event'])",
                fix_obs="patched (id, event)",
                docs_url="https://developers.beehiiv.com/docs/webhooks",
                docs_ok="Beehiiv webhook deliveries are unique on id plus event, not email.",
                docs_url2="https://developers.beehiiv.com/docs/webhooks#event-types",
                docs_ok2="Do not key on email. Not invoice-row-dup. Not SMTP.com clone.",
                outcome="(id, event) deduped opens. Email unused (success).",
                domain="beehiiv-webhook-id-plus-event",
                stack="Beehiiv email webhooks",
                seed="beehiiv-id-plus-event",
                residual="Email is not PK. Not Mailtrap clone.",
                coverage=85,
            ),
            _p(
                slug="constant-contact-campaign-handoff",
                goal="Do not treat a Constant Contact campaign_id as a unique email event.",
                plan="Read campaign-as-event, try contact, then hand off campaign grain.",
                mod="cccamp",
                test_fn="test_campaign_not_event",
                src_body=(
                    "def pk(ev):\n"
                    "    return ev['campaign_id']\n"
                ),
                test_body=(
                    "def test_campaign_not_event():\n"
                    "    assert pk({'campaign_id': 'c1', 'contact_id': 'k1', 'tracking_id': 't1'}) != 'c1'\n"
                ),
                grep_pat="campaign_id|tracking_id|constant",
                grep_hit="src/cccamp.py:2: return ev['campaign_id']",
                fail_msg="AssertionError: campaign_id collapsed every open in the send",
                first_old="    return ev['campaign_id']",
                first_new="    return ev.get('contact_id') or ev['campaign_id']",
                first_obs="patched contact (still campaign grain)",
                still_msg="AssertionError: contact_id still shares the campaign grain",
                reread_obs="Constant Contact campaign_id is campaign grain; tracking_id is platform",
                plan_change="campaign_id is campaign grain. Handoff CC-CG-2.",
                fix_new="    return {'handoff': 'CC-CG-2'}",
                fix_obs="ticket filed. still campaign-classed",
                docs_url="https://v3.developer.constantcontact.com/api_guide/webhooks_overview.html",
                docs_ok="campaign_id identifies the send, not a unique tracking event.",
                docs_url2="https://v3.developer.constantcontact.com/api_guide/email_campaigns.html",
                docs_ok2="Event grain is ESP-plat. Handoff CC-CG-2. Not invoice-row-dup. Not AWeber clone.",
                outcome="Still campaign-classed; campaign grain is Constant Contact — handoff CC-CG-2.",
                domain="constant-contact-campaign-id-vs-tracking-id",
                stack="Constant Contact campaign webhooks",
                seed="constant-contact-campaign-handoff",
                residual="campaign_id is campaign grain.",
                ticket="CC-CG-2",
                ticket_why="Constant Contact tracking grain owned by esp-plat",
                coverage=85,
            ),
        ),
    ],
    "feature-flag-debug-factory": [
        (
            _p(
                slug="gitlab-ff-user-vs-project",
                goal="Evaluate GitLab feature flags for user id, not project id.",
                plan="Read project-as-user, try environment, then user strategy.",
                mod="glabff",
                test_fn="test_user_not_project",
                src_body=(
                    "def eval_flag(ctx):\n"
                    "    return hash(ctx['project_id']) % 100 < 20\n"
                ),
                test_body=(
                    "def test_user_not_project():\n"
                    "    a = eval_flag({'user_id': 'u1', 'project_id': 'p9'})\n"
                    "    b = eval_flag({'user_id': 'u1', 'project_id': 'p2'})\n"
                    "    assert a == b\n"
                ),
                grep_pat="project_id|user_id|gitlab",
                grep_hit="src/glabff.py:2: return hash(ctx['project_id']) % 100 < 20",
                fail_msg="AssertionError: same user flipped across projects; strategy is user",
                first_old="    return hash(ctx['project_id']) % 100 < 20",
                first_new="    return hash(ctx.get('environment') or ctx['project_id']) % 100 < 20",
                first_obs="patched environment (still not user id)",
                still_msg="AssertionError: environment hash still splits the same user",
                reread_obs="GitLab Unleash-compatible strategy is userIds, not project id",
                plan_change="Hash user_id. Project id is not the rollout unit. Not Statsig company.",
                fix_new="    return hash(ctx['user_id']) % 100 < 20",
                fix_obs="patched user_id strategy",
                docs_url="https://docs.gitlab.com/ee/operations/feature_flags.html",
                docs_ok="GitLab user strategy keys on user id; project id is the flag scope, not the unit.",
                docs_url2="https://docs.gitlab.com/ee/operations/feature_flags.html#feature-flag-strategies",
                docs_ok2="Use userIds. Not Statsig user vs company. Not Featurevisor clone.",
                outcome="Same user stayed consistent across projects. Project hash unused (success).",
                domain="gitlab-feature-flag-user-vs-project",
                stack="GitLab feature flags user strategy",
                seed="gitlab-ff-user-vs-project",
                residual="Project id is scope, not unit. Not Statsig company clone.",
                coverage=86,
            ),
            _p(
                slug="dynamic-yield-campaign-handoff",
                goal="Do not treat a Dynamic Yield campaign as a boolean feature flag.",
                plan="Read campaign-as-bool, try variation, then hand off campaign.",
                mod="dycamp",
                test_fn="test_campaign_not_bool",
                src_body=(
                    "def eval_flag(ctx):\n"
                    "    return bool(ctx.get('campaign_id'))\n"
                ),
                test_body=(
                    "def test_campaign_not_bool():\n"
                    "    assert eval_flag({'campaign_id': 'c1', 'variation': 'A'}) is not True\n"
                ),
                grep_pat="campaign_id|variation|dynamic.?yield",
                grep_hit="src/dycamp.py:2: return bool(ctx.get('campaign_id'))",
                fail_msg="AssertionError: campaign presence treated as gate on; allocation unused",
                first_old="    return bool(ctx.get('campaign_id'))",
                first_new="    return ctx.get('variation') == 'A'",
                first_obs="patched variation==A (still a boolean gate over an experiment)",
                still_msg="AssertionError: DY campaign allocation is not a boolean flag",
                reread_obs="Dynamic Yield campaigns are experiment allocation, not feature gates",
                plan_change="Campaign allocation is experiment-plat. Handoff DY-CAMP-3.",
                fix_new="    return {'handoff': 'DY-CAMP-3'}",
                fix_obs="ticket filed. still bool-classed",
                docs_url="https://dxdirect.dynamicyield.com/api/",
                docs_ok="Campaigns assign variations; they are not boolean feature flags.",
                docs_url2="https://support.dynamicyield.com/hc/en-us/articles/360000847508",
                docs_ok2="Allocation is experiment-plat. Handoff DY-CAMP-3. Not Statsig. Not SiteSpect clone.",
                outcome="Still bool-classed; DY campaign is experiment-plat — handoff DY-CAMP-3.",
                domain="dynamic-yield-campaign-vs-boolean-flag",
                stack="Dynamic Yield campaigns",
                seed="dynamic-yield-campaign-handoff",
                residual="Campaign allocation is not a boolean gate.",
                ticket="DY-CAMP-3",
                ticket_why="Dynamic Yield campaign allocation owned by experiment-plat",
                coverage=86,
            ),
        ),
        (
            _p(
                slug="wasabi-assignment-vs-pct",
                goal="Honor Intuit Wasabi assignment buckets before the percentage rollout.",
                plan="Read pct-as-assign, try salt, then assignment unit.",
                mod="wasabi",
                test_fn="test_assign_before_pct",
                src_body=(
                    "def eval_flag(ctx):\n"
                    "    return hash(ctx['user_id']) % 100 < ctx['pct']\n"
                ),
                test_body=(
                    "def test_assign_before_pct():\n"
                    "    assert eval_flag({'user_id': 'u1', 'pct': 50, 'assignment': 'A'}) == 'A'\n"
                ),
                grep_pat="assignment|pct|wasabi",
                grep_hit="src/wasabi.py:2: return hash(ctx['user_id']) % 100 < ctx['pct']",
                fail_msg="AssertionError: True == 'A'; percentage swallowed the assignment bucket",
                first_old="    return hash(ctx['user_id']) % 100 < ctx['pct']",
                first_new="    return hash(ctx['user_id'] + 'salt') % 100 < ctx['pct']",
                first_obs="patched salt (still percentage, still not assignment)",
                still_msg="AssertionError: salt does not return the Wasabi assignment bucket",
                reread_obs="Wasabi assignments are stored buckets; percentage is only for unassigned",
                plan_change="Return assignment if present. Salt does not replace buckets. Not Statsig.",
                fix_new="    return ctx.get('assignment') or (hash(ctx['user_id']) % 100 < ctx['pct'])",
                fix_obs="patched assignment-before-pct",
                docs_url="https://github.com/intuit/wasabi",
                docs_ok="Wasabi stores assignment buckets; percentage applies only to unassigned users.",
                docs_url2="https://intuit.github.io/wasabi/",
                docs_ok2="Honor assignment first. Not Statsig user vs company. Not Featurevisor clone.",
                outcome="Stored assignment A won. Percentage unused for assigned users (success).",
                domain="wasabi-assignment-bucket-before-percentage",
                stack="Intuit Wasabi assignments",
                seed="wasabi-assignment-vs-pct",
                residual="Assignment buckets beat percentage. Not Featurevisor clone.",
                coverage=85,
            ),
            _p(
                slug="monetate-experience-handoff",
                goal="Do not treat a Monetate experience as a boolean feature flag.",
                plan="Read experience-as-bool, try variant, then hand off experience.",
                mod="monexp",
                test_fn="test_experience_not_bool",
                src_body=(
                    "def eval_flag(ctx):\n"
                    "    return bool(ctx.get('experience_id'))\n"
                ),
                test_body=(
                    "def test_experience_not_bool():\n"
                    "    assert eval_flag({'experience_id': 'e1', 'variant': 'B'}) is not True\n"
                ),
                grep_pat="experience_id|variant|monetate",
                grep_hit="src/monexp.py:2: return bool(ctx.get('experience_id'))",
                fail_msg="AssertionError: experience presence treated as gate on; variant unused",
                first_old="    return bool(ctx.get('experience_id'))",
                first_new="    return ctx.get('variant') == 'B'",
                first_obs="patched variant==B (still a boolean gate over an experience)",
                still_msg="AssertionError: Monetate experience allocation is not a boolean flag",
                reread_obs="Monetate experiences are personalization allocation, not feature gates",
                plan_change="Experience allocation is experiment-plat. Handoff MN-XP-4.",
                fix_new="    return {'handoff': 'MN-XP-4'}",
                fix_obs="ticket filed. still bool-classed",
                docs_url="https://developer.monetate.com/",
                docs_ok="Experiences assign variants; they are not boolean feature flags.",
                docs_url2="https://developer.monetate.com/javascript-api/",
                docs_ok2="Allocation is experiment-plat. Handoff MN-XP-4. Not Statsig. Not Dynamic Yield clone.",
                outcome="Still bool-classed; Monetate experience is experiment-plat — handoff MN-XP-4.",
                domain="monetate-experience-vs-boolean-flag",
                stack="Monetate experiences",
                seed="monetate-experience-handoff",
                residual="Experience allocation is not a boolean gate.",
                ticket="MN-XP-4",
                ticket_why="Monetate experience allocation owned by experiment-plat",
                coverage=85,
            ),
        ),
    ],
    "search-index-rebuild-factory": [
        (
            _p(
                slug="arangosearch-analyzer-vs-drop",
                goal="Alter ArangoSearch analyzer in place; do not DROP VIEW to rebuild.",
                plan="Read drop-as-alter, try truncate, then ALTER VIEW analyzer.",
                mod="araivw",
                test_fn="test_alter_not_drop",
                src_body=(
                    "def rebuild(view):\n"
                    "    return f'DROP VIEW {view}'\n"
                ),
                test_body=(
                    "def test_alter_not_drop():\n"
                    "    assert 'DROP' not in rebuild('inv')\n"
                    "    assert 'analyzer' in rebuild('inv')\n"
                ),
                grep_pat="DROP VIEW|analyzer|arangosearch",
                grep_hit="src/araivw.py:2: return f'DROP VIEW {view}'",
                fail_msg="AssertionError: DROP VIEW deleted invoices; analyzer unused",
                first_old="    return f'DROP VIEW {view}'",
                first_new="    return f'TRUNCATE VIEW {view}'",
                first_obs="patched TRUNCATE (still destructive; BAN TRUNCATE-then-reindex)",
                still_msg="AssertionError: TRUNCATE still wipes the view; need ALTER analyzer",
                reread_obs="ArangoSearch VIEW can ALTER analyzer in place; do not DROP or TRUNCATE",
                plan_change="ALTER VIEW analyzer. Do not DROP or TRUNCATE.",
                fix_new="    return f'ALTER VIEW {view} SET analyzer=text_en'",
                fix_obs="patched ALTER VIEW analyzer",
                docs_url="https://docs.arangodb.com/stable/index-and-search/arangosearch/",
                docs_ok="ArangoSearch views can change analyzers in place without DROP.",
                docs_url2="https://docs.arangodb.com/stable/aql/functions/arangosearch/",
                docs_ok2="ALTER VIEW. Not TRUNCATE-then-reindex. Not CrateDB DROP clone.",
                outcome="ALTER VIEW analyzer rebuilt tokens. DROP unused (success).",
                domain="arangosearch-alter-analyzer-vs-drop-view",
                stack="ArangoSearch VIEW analyzer",
                seed="arangosearch-analyzer-vs-drop",
                residual="Not TRUNCATE-then-reindex. Not CrateDB/ZomboDB clones.",
                coverage=87,
            ),
            _p(
                slug="lucidworks-fusion-handoff",
                goal="Do not query Lucidworks Fusion before the collection rebuild job finishes.",
                plan="Read query-as-ready, try commit, then hand off collection rebuild.",
                mod="lfcol",
                test_fn="test_rebuild_not_query",
                src_body=(
                    "def ready(col):\n"
                    "    return {'query': col}\n"
                ),
                test_body=(
                    "def test_rebuild_not_query():\n"
                    "    assert 'query' not in ready('inv')\n"
                ),
                grep_pat="query|rebuild|fusion",
                grep_hit="src/lfcol.py:2: return {'query': col}",
                fail_msg="AssertionError: Fusion query hit a half-rebuilt collection",
                first_old="    return {'query': col}",
                first_new="    return {'query': col, 'commit': True}",
                first_obs="patched commit (still querying during rebuild)",
                still_msg="AssertionError: commit cannot wait Fusion collection rebuild",
                reread_obs="Fusion collection rebuild is a platform job; query is not a waiter",
                plan_change="Collection rebuild is fusion-plat. Handoff LF-COL-5.",
                fix_new="    return {'handoff': 'LF-COL-5'}",
                fix_obs="ticket filed. still query-classed",
                docs_url="https://doc.lucidworks.com/fusion/5.12/indexing/index-pipelines",
                docs_ok="Collection rebuild is a Fusion job, not a query-time commit.",
                docs_url2="https://doc.lucidworks.com/fusion/5.12/indexing/datasources",
                docs_ok2="Wait is fusion-plat. Handoff LF-COL-5. Not TRUNCATE. Not Coveo clone.",
                outcome="Still query-classed; collection rebuild is Fusion — handoff LF-COL-5.",
                domain="lucidworks-fusion-collection-rebuild-vs-query",
                stack="Lucidworks Fusion collection rebuild",
                seed="lucidworks-fusion-handoff",
                residual="Commit cannot wait Fusion rebuild.",
                ticket="LF-COL-5",
                ticket_why="Fusion collection rebuild owned by search-plat",
                coverage=87,
            ),
        ),
        (
            _p(
                slug="ravendb-stale-vs-drop",
                goal="Wait RavenDB non-stale indexes; do not DROP INDEX to rebuild.",
                plan="Read drop-as-wait, try truncate, then WaitForNonStaleResults.",
                mod="ravidx",
                test_fn="test_wait_not_drop",
                src_body=(
                    "def rebuild(idx):\n"
                    "    return f'DROP INDEX {idx}'\n"
                ),
                test_body=(
                    "def test_wait_not_drop():\n"
                    "    assert 'DROP' not in rebuild('inv')\n"
                    "    assert 'WaitForNonStaleResults' in rebuild('inv')\n"
                ),
                grep_pat="DROP INDEX|WaitForNonStaleResults|ravendb",
                grep_hit="src/ravidx.py:2: return f'DROP INDEX {idx}'",
                fail_msg="AssertionError: DROP INDEX deleted invoices; wait unused",
                first_old="    return f'DROP INDEX {idx}'",
                first_new="    return f'TRUNCATE INDEX {idx}'",
                first_obs="patched TRUNCATE (still destructive; BAN TRUNCATE-then-reindex)",
                still_msg="AssertionError: TRUNCATE still wipes the index; need WaitForNonStaleResults",
                reread_obs="RavenDB static indexes catch up via WaitForNonStaleResults; do not DROP",
                plan_change="WaitForNonStaleResults. Do not DROP or TRUNCATE.",
                fix_new="    return f'WaitForNonStaleResults {idx}'",
                fix_obs="patched WaitForNonStaleResults",
                docs_url="https://ravendb.net/docs/article-page/6.2/csharp/indexes/stale-indexes",
                docs_ok="WaitForNonStaleResults waits for indexing; DROP INDEX is destructive.",
                docs_url2="https://ravendb.net/docs/article-page/6.2/csharp/indexes/creating-and-deploying",
                docs_ok2="Wait, do not DROP. Not TRUNCATE-then-reindex. Not ZomboDB clone.",
                outcome="WaitForNonStaleResults caught up. DROP unused (success).",
                domain="ravendb-wait-nonstale-vs-drop-index",
                stack="RavenDB WaitForNonStaleResults",
                seed="ravendb-stale-vs-drop",
                residual="Not TRUNCATE-then-reindex. Not ZomboDB clone.",
                coverage=86,
            ),
            _p(
                slug="yext-source-handoff",
                goal="Do not query Yext Knowledge Graph before the entity source push finishes.",
                plan="Read query-as-ready, try refresh, then hand off source push.",
                mod="yxtsrc",
                test_fn="test_source_not_query",
                src_body=(
                    "def ready(src):\n"
                    "    return {'query': src}\n"
                ),
                test_body=(
                    "def test_source_not_query():\n"
                    "    assert 'query' not in ready('inv')\n"
                ),
                grep_pat="query|source|yext",
                grep_hit="src/yxtsrc.py:2: return {'query': src}",
                fail_msg="AssertionError: Yext query hit a half-pushed entity source",
                first_old="    return {'query': src}",
                first_new="    return {'query': src, 'refresh': True}",
                first_obs="patched refresh (still querying during source push)",
                still_msg="AssertionError: refresh cannot wait Yext entity source push",
                reread_obs="Yext source push is a platform job; query is not a waiter",
                plan_change="Source push is yext-plat. Handoff YX-SRC-6.",
                fix_new="    return {'handoff': 'YX-SRC-6'}",
                fix_obs="ticket filed. still query-classed",
                docs_url="https://hitchhikers.yext.com/docs/knowledgegraph/entities/",
                docs_ok="Entity source push is a Yext job, not a query-time refresh.",
                docs_url2="https://hitchhikers.yext.com/docs/knowledgegraph/",
                docs_ok2="Wait is yext-plat. Handoff YX-SRC-6. Not TRUNCATE. Not Coveo clone.",
                outcome="Still query-classed; entity source is Yext — handoff YX-SRC-6.",
                domain="yext-entity-source-push-vs-query",
                stack="Yext Knowledge Graph source push",
                seed="yext-source-handoff",
                residual="Refresh cannot wait Yext source push.",
                ticket="YX-SRC-6",
                ticket_why="Yext entity source push owned by search-plat",
                coverage=86,
            ),
        ),
    ],
    "log-redaction-factory": [
        (
            _p(
                slug="hclog-json-redact-token",
                goal="HashiCorp hclog JSON dumped api_token. Add a redact field; do not Discard the logger.",
                plan="Read discard-as-redact, try level=off, then JSON redact api_token.",
                mod="hclogr",
                test_fn="test_redact_not_discard",
                src_body=(
                    "def tune(leak):\n"
                    "    return {'output': 'Discard'} if leak else {}\n"
                ),
                test_body=(
                    "def test_redact_not_discard():\n"
                    "    t = tune(True)\n"
                    "    assert t.get('redact') == 'api_token' and t.get('output') != 'Discard'\n"
                ),
                grep_pat="Discard|api_token|hclog",
                grep_hit="src/hclogr.py:2: return {'output': 'Discard'} if leak else {}",
                fail_msg="AssertionError: Discard blinded 4 sinks; api_token still in JSON",
                first_old="    return {'output': 'Discard'} if leak else {}",
                first_new="    return {'level': 'off'} if leak else {}",
                first_obs="patched level=off (still blinds the logger, token unredacted)",
                still_msg="AssertionError: level=off blinds INFO; need JSON redact of api_token",
                reread_obs="hclog JSON includes api_token field; redact it and keep INFO",
                plan_change="JSON redact api_token. Discard/OFF is the wrong layer.",
                fix_new="    return {'redact': 'api_token', 'level': 'info'} if leak else {}",
                fix_obs="patched JSON redact api_token",
                docs_url="https://pkg.go.dev/github.com/hashicorp/go-hclog",
                docs_ok="hclog JSON can omit/redact named fields; discarding the logger blinds ops.",
                docs_url2="https://github.com/hashicorp/go-hclog#json-format",
                docs_ok2="Redact api_token. Do not Discard. Not JUL Filter clone. Leftover unique.",
                outcome="JSON redact hid api_token. Discard unused (success).",
                domain="hclog-json-redact-api-token-vs-discard",
                stack="HashiCorp hclog JSON redact",
                seed="hclog-json-redact-token",
                residual="Discard blinds sinks. Not JUL/zap clones. Unique leftover.",
                coverage=87,
            ),
            _p(
                slug="klog-setoutput-handoff",
                goal="klog dumped Authorization. Do not klog.SetOutput(io.Discard). Hand off sanitizer.",
                plan="Read discard-as-redact, try -v=0, then hand off klog sanitizer.",
                mod="klogds",
                test_fn="test_sanitize_not_discard",
                src_body=(
                    "def tune(leak):\n"
                    "    return {'SetOutput': 'Discard'} if leak else {}\n"
                ),
                test_body=(
                    "def test_sanitize_not_discard():\n"
                    "    assert 'SetOutput' not in tune(True)\n"
                ),
                grep_pat="SetOutput|Authorization|klog",
                grep_hit="src/klogds.py:2: return {'SetOutput': 'Discard'} if leak else {}",
                fail_msg="AssertionError: SetOutput Discard blinded kube logs; header still unredacted",
                first_old="    return {'SetOutput': 'Discard'} if leak else {}",
                first_new="    return {'v': 0} if leak else {}",
                first_obs="patched -v=0 (still blinds verbosity, header unredacted)",
                still_msg="AssertionError: -v=0 cannot redact Authorization; sanitizer is platform",
                reread_obs="klog has no field redact; Authorization sanitizer is platform-k8s",
                plan_change="klog sanitizer is platform-k8s. Handoff KL-SAN-7.",
                fix_new="    return {'handoff': 'KL-SAN-7'} if leak else {}",
                fix_obs="ticket filed. still discard-classed",
                docs_url="https://github.com/kubernetes/klog",
                docs_ok="klog SetOutput(Discard) blinds the process; header redaction is a sanitizer.",
                docs_url2="https://github.com/kubernetes/klog#usage",
                docs_ok2="Sanitizer is platform-k8s. Handoff KL-SAN-7. Not Netty clone. Unique leftover.",
                outcome="Still discard-classed; klog sanitizer is platform-k8s — handoff KL-SAN-7.",
                domain="klog-authorization-vs-setoutput-discard",
                stack="Kubernetes klog sanitizer",
                seed="klog-setoutput-handoff",
                residual="SetOutput Discard is the wrong layer.",
                ticket="KL-SAN-7",
                ticket_why="klog Authorization sanitizer owned by platform-k8s",
                coverage=87,
            ),
        ),
        (
            _p(
                slug="logbook-processor-ssn",
                goal="Python Logbook Processor must redact SSN; do not NullHandler the stack.",
                plan="Read null-as-redact, try level=ERROR, then Processor redact SSN.",
                mod="pylbk",
                test_fn="test_processor_not_null",
                src_body=(
                    "def tune(leak):\n"
                    "    return {'handler': 'NullHandler'} if leak else {}\n"
                ),
                test_body=(
                    "def test_processor_not_null():\n"
                    "    t = tune(True)\n"
                    "    assert t.get('processor') == 'ssn' and t.get('handler') != 'NullHandler'\n"
                ),
                grep_pat="NullHandler|ssn|logbook",
                grep_hit="src/pylbk.py:2: return {'handler': 'NullHandler'} if leak else {}",
                fail_msg="AssertionError: NullHandler blinded 3 handlers; SSN still in extra",
                first_old="    return {'handler': 'NullHandler'} if leak else {}",
                first_new="    return {'level': 'ERROR'} if leak else {}",
                first_obs="patched ERROR (still blinds INFO; SSN unredacted)",
                still_msg="AssertionError: ERROR blinds INFO; need Processor to redact SSN",
                reread_obs="Logbook Processor can rewrite extra['ssn']; NullHandler is the wrong layer",
                plan_change="Processor redacts SSN. NullHandler/ERROR is the wrong layer.",
                fix_new="    return {'processor': 'ssn', 'level': 'INFO'} if leak else {}",
                fix_obs="patched Processor redact SSN",
                docs_url="https://logbook.readthedocs.io/en/stable/api/processors.html",
                docs_ok="Processors rewrite record extras; NullHandler drops the entire stack.",
                docs_url2="https://logbook.readthedocs.io/en/stable/quickstart.html",
                docs_ok2="Redact SSN in Processor. Not Zalando logbook HTTP clone. Unique leftover.",
                outcome="Processor hid SSN. NullHandler unused (success).",
                domain="python-logbook-processor-ssn-vs-nullhandler",
                stack="Python Logbook Processor",
                seed="logbook-processor-ssn",
                residual="Not Zalando logbook-processor-cvv clone. Unique leftover.",
                coverage=86,
            ),
            _p(
                slug="twisted-log-observer-handoff",
                goal="Twisted log dumped Authorization. Do not log.startLogging(devnull). Hand off observer.",
                plan="Read devnull-as-redact, try log.err only, then hand off observer.",
                mod="twlog",
                test_fn="test_observer_not_devnull",
                src_body=(
                    "def tune(leak):\n"
                    "    return {'startLogging': '/dev/null'} if leak else {}\n"
                ),
                test_body=(
                    "def test_observer_not_devnull():\n"
                    "    assert 'startLogging' not in tune(True)\n"
                ),
                grep_pat="startLogging|Authorization|twisted",
                grep_hit="src/twlog.py:2: return {'startLogging': '/dev/null'} if leak else {}",
                fail_msg="AssertionError: startLogging(devnull) blinded twisted; header still unredacted",
                first_old="    return {'startLogging': '/dev/null'} if leak else {}",
                first_new="    return {'only': 'log.err'} if leak else {}",
                first_obs="patched log.err only (still blinds info; header unredacted)",
                still_msg="AssertionError: log.err cannot redact Authorization; observer is platform",
                reread_obs="Twisted global log observer must sanitize; startLogging(devnull) is wrong layer",
                plan_change="Twisted observer is platform-twisted. Handoff TW-OBS-8.",
                fix_new="    return {'handoff': 'TW-OBS-8'} if leak else {}",
                fix_obs="ticket filed. still devnull-classed",
                docs_url="https://docs.twisted.org/en/stable/core/howto/logging.html",
                docs_ok="Observers filter events; startLogging(devnull) blinds the process.",
                docs_url2="https://docs.twisted.org/en/stable/api/twisted.logger.html",
                docs_ok2="Observer is platform-twisted. Handoff TW-OBS-8. Not Netty clone. Unique leftover.",
                outcome="Still devnull-classed; Twisted observer is platform-twisted — handoff TW-OBS-8.",
                domain="twisted-log-observer-vs-startlogging-devnull",
                stack="Twisted log observer",
                seed="twisted-log-observer-handoff",
                residual="startLogging(devnull) is the wrong layer.",
                ticket="TW-OBS-8",
                ticket_why="Twisted Authorization observer owned by platform-twisted",
                coverage=86,
            ),
        ),
    ],
    "ssl-cert-rotation-factory": [
        (
            _p(
                slug="h2o-ssl-session-reload",
                goal="H2O restart drops HTTP/2; SIGHUP reloads ssl-session-cache cert files.",
                plan="Read restart-as-reload, try delete-then-create, then SIGHUP yaml.",
                mod="h2ossl",
                test_fn="test_sighup_not_restart",
                src_body=(
                    "def rotate():\n"
                    "    return {'action': 'restart'}\n"
                ),
                test_body=(
                    "def test_sighup_not_restart():\n"
                    "    assert rotate() == {'action': 'sighup', 'ssl-session-cache': True}\n"
                ),
                grep_pat="restart|sighup|ssl-session-cache",
                grep_hit="src/h2ossl.py:2: return {'action': 'restart'}",
                fail_msg="AssertionError: restart dropped HTTP/2 streams; yaml cert unused",
                first_old="    return {'action': 'restart'}",
                first_new="    return {'action': 'delete_then_create'}",
                first_obs="patched delete-then-create (BAN; still not SIGHUP)",
                still_msg="AssertionError: delete-then-create secret is banned; need SIGHUP",
                reread_obs="H2O SIGHUP reloads yaml certificate-file without dropping HTTP/2",
                plan_change="SIGHUP ssl-session-cache. Do not delete-then-create secret.",
                fix_new="    return {'action': 'sighup', 'ssl-session-cache': True}",
                fix_obs="patched SIGHUP yaml cert",
                docs_url="https://h2o.examp1e.net/configure/base_directives.html",
                docs_ok="H2O SIGHUP reloads certificate-file; restart drops HTTP/2.",
                docs_url2="https://h2o.examp1e.net/configure/http2_directives.html",
                docs_ok2="Reload yaml certs. Not delete-then-create. Not ClickHouse RELOAD clone.",
                outcome="SIGHUP swapped the leaf. Restart unused (success).",
                domain="h2o-ssl-session-cache-sighup-vs-restart",
                stack="H2O SIGHUP certificate-file",
                seed="h2o-ssl-session-reload",
                residual="Not delete-then-create. Not Marathon/Mesos clones.",
                coverage=84,
            ),
            _p(
                slug="pound-https-handoff",
                goal="Ticket is Pound HTTPS Cert swap; nightly still restarts the balancer.",
                plan="Read restart-as-reload, try delete-then-create, then hand off Pound cert.",
                mod="poundc",
                test_fn="test_pound_not_restart",
                src_body=(
                    "def rotate():\n"
                    "    return {'action': 'restart'}\n"
                ),
                test_body=(
                    "def test_pound_not_restart():\n"
                    "    assert 'restart' not in rotate().get('action', '')\n"
                ),
                grep_pat="restart|Cert|pound",
                grep_hit="src/poundc.py:2: return {'action': 'restart'}",
                fail_msg="AssertionError: Pound restart dropped backends; Cert file unused",
                first_old="    return {'action': 'restart'}",
                first_new="    return {'action': 'delete_then_create'}",
                first_obs="patched delete-then-create (BAN; still not Pound cert swap)",
                still_msg="AssertionError: delete-then-create secret is banned; Pound Cert is platform",
                reread_obs="Pound HTTPS Cert is a platform file swap; restart is the wrong layer",
                plan_change="Pound Cert is lb-plat. Handoff PD-CRT-9. Not delete-then-create.",
                fix_new="    return {'handoff': 'PD-CRT-9'}",
                fix_obs="ticket filed. still restart-classed",
                docs_url="https://github.com/graygnuorg/pound",
                docs_ok="Pound Cert/CertDir is a listener file; process restart drops backends.",
                docs_url2="https://www.apsis.ch/pound/",
                docs_ok2="Cert swap is lb-plat. Handoff PD-CRT-9. Not delete-then-create. Not Mesos clone.",
                outcome="Still restart-classed; Pound Cert is lb-plat — handoff PD-CRT-9.",
                domain="pound-https-cert-vs-restart",
                stack="Pound HTTPS Cert",
                seed="pound-https-handoff",
                residual="Nightly still restarts Pound. Not delete-then-create.",
                ticket="PD-CRT-9",
                ticket_why="Pound HTTPS Cert swap owned by lb-plat",
                coverage=84,
            ),
        ),
        (
            _p(
                slug="pomerium-certificates-reload",
                goal="Pomerium restart drops routes; SIGHUP reloads certificates_file.",
                plan="Read restart-as-reload, try delete-then-create, then SIGHUP certificates_file.",
                mod="pmrcrt",
                test_fn="test_sighup_not_restart",
                src_body=(
                    "def rotate():\n"
                    "    return {'action': 'restart'}\n"
                ),
                test_body=(
                    "def test_sighup_not_restart():\n"
                    "    assert rotate() == {'action': 'sighup', 'certificates_file': True}\n"
                ),
                grep_pat="restart|sighup|certificates_file",
                grep_hit="src/pmrcrt.py:2: return {'action': 'restart'}",
                fail_msg="AssertionError: restart dropped Pomerium routes; certificates_file unused",
                first_old="    return {'action': 'restart'}",
                first_new="    return {'action': 'delete_then_create'}",
                first_obs="patched delete-then-create (BAN; still not SIGHUP)",
                still_msg="AssertionError: delete-then-create secret is banned; need SIGHUP",
                reread_obs="Pomerium SIGHUP reloads certificates_file without dropping routes",
                plan_change="SIGHUP certificates_file. Do not delete-then-create secret.",
                fix_new="    return {'action': 'sighup', 'certificates_file': True}",
                fix_obs="patched SIGHUP certificates_file",
                docs_url="https://www.pomerium.com/docs/reference/certificates",
                docs_ok="Pomerium reloads certificates_file on SIGHUP; restart drops routes.",
                docs_url2="https://www.pomerium.com/docs/reference/certificates-file",
                docs_ok2="Reload certificates_file. Not delete-then-create. Not H2O clone.",
                outcome="SIGHUP swapped the leaf. Restart unused (success).",
                domain="pomerium-certificates-file-sighup-vs-restart",
                stack="Pomerium SIGHUP certificates_file",
                seed="pomerium-certificates-reload",
                residual="Not delete-then-create. Not H2O/Marathon clones.",
                coverage=83,
            ),
            _p(
                slug="oauth2-proxy-tls-handoff",
                goal="Ticket is oauth2-proxy TLS cert swap; nightly still restarts the proxy.",
                plan="Read restart-as-reload, try delete-then-create, then hand off tls-cert-file.",
                mod="o2ptls",
                test_fn="test_oauth2_not_restart",
                src_body=(
                    "def rotate():\n"
                    "    return {'action': 'restart'}\n"
                ),
                test_body=(
                    "def test_oauth2_not_restart():\n"
                    "    assert 'restart' not in rotate().get('action', '')\n"
                ),
                grep_pat="restart|tls-cert-file|oauth2-proxy",
                grep_hit="src/o2ptls.py:2: return {'action': 'restart'}",
                fail_msg="AssertionError: oauth2-proxy restart dropped sessions; tls-cert-file unused",
                first_old="    return {'action': 'restart'}",
                first_new="    return {'action': 'delete_then_create'}",
                first_obs="patched delete-then-create (BAN; still not tls-cert-file swap)",
                still_msg="AssertionError: delete-then-create secret is banned; tls-cert-file is platform",
                reread_obs="oauth2-proxy --tls-cert-file is a platform file swap; restart is wrong layer",
                plan_change="tls-cert-file is idp-plat. Handoff O2P-TLS-2. Not delete-then-create.",
                fix_new="    return {'handoff': 'O2P-TLS-2'}",
                fix_obs="ticket filed. still restart-classed",
                docs_url="https://oauth2-proxy.github.io/oauth2-proxy/configuration/overview",
                docs_ok="--tls-cert-file/--tls-key-file are listener files; restart drops sessions.",
                docs_url2="https://oauth2-proxy.github.io/oauth2-proxy/configuration/tls",
                docs_ok2="Cert swap is idp-plat. Handoff O2P-TLS-2. Not delete-then-create. Not Pound clone.",
                outcome="Still restart-classed; oauth2-proxy TLS is idp-plat — handoff O2P-TLS-2.",
                domain="oauth2-proxy-tls-cert-file-vs-restart",
                stack="oauth2-proxy tls-cert-file",
                seed="oauth2-proxy-tls-handoff",
                residual="Nightly still restarts oauth2-proxy. Not delete-then-create.",
                ticket="O2P-TLS-2",
                ticket_why="oauth2-proxy tls-cert-file swap owned by idp-plat",
                coverage=83,
            ),
        ),
    ],
}
