"""Unique eval-harness leftover plants r294+. Not r50–r252 or r253–r293 clones."""

PAIRS = []


def _ok(**kwargs):
    kwargs["success"] = True
    kwargs.setdefault("tests_passed", 5)
    kwargs.setdefault("tests_failed_as_designed", 1)
    return kwargs


def _bad(**kwargs):
    kwargs["success"] = False
    kwargs.setdefault("tests_passed", 0)
    kwargs.setdefault("tests_failed_as_designed", 1)
    return kwargs


# ---------------------------------------------------------------------------
# r294 CI leftover / cache leftover — not r253 xdist, not r268 docker layer
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="gha-restore-keys-cache-x63e",
            domain="warranty-bot",
            kind="ci",
            avoided="r253 xdist cache race; r268 docker layer COPY .deepeval; r12 deepeval-cache-stale",
            goal=(
                "GitHub Actions actions/cache restore-keys leftover prefix eval- restores last "
                "week's .deepeval/ scores after goldens change. Hash only evals/**/*.py. Force "
                "cache key to include goldens and drop restore-keys. Fail-closed on stale scores."
            ),
            plan="Dump cache key, drop restore-keys, hash goldens+py, prove planted lifetime-warranty fail.",
            outcome=(
                "Cache key hashes evals/**/*.py and goldens/**. restore-keys removed. 5 golds pass, "
                "planted lifetime-warranty row 0.17 fail-closed. Residual: org reusable workflow "
                "still documents restore-keys eval- as optional."
            ),
            ticket=(
                "Title: nightly warranty eval still 0.94 after planting lifetime-warranty lie. "
                "GHA cache restore-keys: eval- leftover hit from last Tuesday."
            ),
            src="evals/warranty_eval.py",
            src_obs=(
                "measure() writes .deepeval/cache.json keyed on input+actual only.\n"
                "ci/eval.yml: key: eval-${{ hashFiles('evals/**/*.py') }}\n"
                "restore-keys: |\n  eval-\n"
            ),
            run="evals/warranty_eval.py",
            fail_obs=(
                "8 passed. planted lifetime-warranty still 0.94 from cache hit\n"
                "GHA: Cache restored from eval-2026-08-12"
            ),
            inspect=".github/workflows/eval.yml",
            inspect_obs=(
                "restore-keys leftover prefix eval- matches any prior eval- sha.\n"
                "hashFiles misses goldens/warranty.jsonl"
            ),
            first_path=".github/workflows/eval.yml",
            first_old="hashFiles('evals/**/*.py')",
            first_new="hashFiles('evals/**/*.py', 'goldens/**/*.jsonl')",
            first_obs="key includes goldens. restore-keys: eval- leftover still restores older sha",
            rate_tail="restore-keys still matched eval-2026-08-12; planted 0.94 leftover",
            still_after_429="restore-keys leftover; planted lifetime-warranty still 0.94",
            grep="restore-keys|hashFiles|.deepeval",
            grep_obs="drop restore-keys; fail the job if Cache restored without exact key",
            plan_change="delete restore-keys; exact key only; bust .deepeval on miss",
            fix_path=".github/workflows/eval.yml",
            fix_old="restore-keys: |\n  eval-\n",
            fix_new="# no restore-keys; stale .deepeval must not leak across goldens\n",
            fix_obs="exact key only. planted lifetime-warranty 0.17 fail-closed",
            retry_obs="502 then retry; 5 pass 1 fail planted lifetime-warranty 0.17",
            test="tests/test_gha_eval_cache.py",
            test_body="assert 'restore-keys' not in workflow; assert 'goldens' in hashFiles",
            test_obs="test_eval_cache_key_includes_goldens_no_restore_keys",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed. cache miss after golden edit",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed. cache miss after golden edit",
            diff_obs=" .github/workflows/eval.yml | 8+-\n tests/test_gha_eval_cache.py | 14++\n",
            residual="Org reusable workflow still documents restore-keys eval- as optional.",
        ),
        _bad(
            slug="turbo-hash-miss-goldens-y64f",
            domain="sla-desk",
            kind="ci",
            avoided="r253 xdist cache; r268 docker layer; r271 makefile stale goldens",
            goal=(
                "Turborepo eval task cache hashes only evals/*.py so leftover remote HIT skips "
                "re-eval after a planted next-business-day SLA golden. Include goldens in inputs "
                "and fail if turbo reports HIT when goldens changed."
            ),
            plan="Dump turbo.json inputs, add goldens, force miss, prove planted SLA fail.",
            outcome=(
                "Local turbo.json inputs include goldens/*.jsonl. Planted next-business-day row "
                "fails 0.21 locally. Handoff: Vercel remote turbo cache still has HIT for the "
                "old hash."
            ),
            ticket=(
                "Title: turbo run eval --cache HIT after adding goldens/sla_nbd.jsonl. "
                "Planted next-business-day lie still 0.91."
            ),
            src="evals/sla_eval.py",
            src_obs=(
                "turbo.json task eval inputs: [evals/*.py, src/**]\n"
                "outputs: [.deepeval/**]\n"
                "goldens/ not listed"
            ),
            run="evals/sla_eval.py",
            fail_obs=">>> FULL TURBO CACHE HIT (eval)\nplanted nbd still 0.91 leftover",
            inspect="turbo.json",
            inspect_obs="inputs omit goldens/*.jsonl. remote cache key leftover from yesterday",
            first_path="turbo.json",
            first_old='"evals/*.py", "src/**"',
            first_new='"evals/*.py", "src/**", "goldens/*.jsonl"',
            first_obs="local miss. remote still HIT because env TURBO_REMOTE leftover",
            rate_tail="remote HIT leftover; planted nbd 0.91",
            still_after_429="remote turbo HIT leftover; local inputs patched",
            grep="turbo|inputs|goldens",
            grep_obs="TURBO_REMOTE=false locally; cannot flush org remote",
            plan_change="local --force and goldens in inputs; document remote leftover handoff",
            fix_path="package.json",
            fix_old='"eval": "turbo run eval"',
            fix_new='"eval": "turbo run eval --force"',
            fix_obs="local --force miss. planted 0.21. remote HIT leftover HANDOFF",
            retry_obs="502 unused for remote. local 0.21 planted. Partial",
            test="tests/test_turbo_eval_inputs.py",
            test_body="assert 'goldens/*.jsonl' in turbo_inputs; xfail remote HIT",
            test_obs="remote cache HIT leftover. Partial",
            suite_obs="local --force planted fail. remote HIT leftover. Partial.",
            gate_obs="local --force planted fail. remote HIT leftover. Partial.",
            diff_obs=" turbo.json | 2+-\n package.json | 2+-\n HANDOFF remote turbo\n",
            residual="Vercel remote turbo cache still HIT for the pre-golden hash. Partial.",
        ),
    )
)

# ---------------------------------------------------------------------------
# r295 judge leftover — not GEval json_mode extra=forbid, not GEval temp/seed
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="outlines-schema-default-score-z65g",
            domain="billing-cancel",
            kind="judge",
            avoided="r254 GEval extra=forbid; r16 json_mode; r11 vacuous refund",
            goal=(
                "Outlines constrained decode leftover JSON schema sets score default 1.0 so the "
                "judge omits score and still emits 1.0 on a planted cancel-at-period-end lie. "
                "Make score required with no default; fail-closed if missing."
            ),
            plan="Dump schema, drop default, require score, prove planted cancel lie fails.",
            outcome=(
                "JudgeScore schema required=['score'] with no default. Gold cancels 0.9x; planted "
                "period-end lie 0.18. Residual: notebooks/ still import the old schema copy."
            ),
            ticket=(
                "Title: Outlines JudgeScore default 1.0; planted cancel-at-period-end still 1.0. "
                "Model omitted score; schema filled default."
            ),
            src="evals/judge_schema.py",
            src_obs=(
                "OUTLINES_JSON = {properties: {score: {type: number, default: 1.0}}, "
                "required: [reason]}\nscore not required"
            ),
            run="evals/cancel_eval.py",
            fail_obs="planted period-end 1.0. gold 0.93. schema default filled omitted score",
            inspect="evals/judge_schema.py",
            inspect_obs="default 1.0 leftover. required only reason. outlines fills default",
            first_path="evals/judge_schema.py",
            first_old='"default": 1.0',
            first_new='"minimum": 0, "maximum": 1',
            first_obs="default gone. score still optional; omitted score → outlines skip → 1.0 helper",
            rate_tail="score still optional; helper leftover returns 1.0 on KeyError",
            still_after_429="optional score; KeyError helper 1.0 leftover",
            grep="default|required|JudgeScore",
            grep_obs="require score; fail-closed if missing; no helper 1.0",
            plan_change="required score; no default; raise on missing instead of 1.0",
            fix_path="evals/judge_schema.py",
            fix_old='"required": ["reason"]',
            fix_new='"required": ["reason", "score"]',
            fix_obs="omitted score now ValidationError fail-closed. planted 0.18",
            retry_obs="502 then retry; 5 pass 1 fail planted period-end 0.18",
            test="tests/test_outlines_score_required.py",
            test_body="assert 'score' in required and 'default' not in score_schema",
            test_obs="test_outlines_score_required_no_default",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed. missing score raises",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed. missing score raises",
            diff_obs=" evals/judge_schema.py | 6+-\n tests/test_outlines_score_required.py | 12++\n",
            residual="notebooks/ still import the old schema copy with default 1.0.",
        ),
        _bad(
            slug="guidance-select-pass-first-a66h",
            domain="noshow-desk",
            kind="judge",
            avoided="r254 GEval extra=forbid; r16 json_mode; r11 vacuous GEval",
            goal=(
                "Guidance leftover select(['pass','fail']) plus a compiled program cache always "
                "picks pass on planted 2-hour no-show lies. Recompile with fail first and bust "
                "the leftover program cache."
            ),
            plan="Dump compiled program, reverse select, bust cache, prove planted no-show fail.",
            outcome=(
                "Local select is ['fail','pass'] and compile cache hashed. Planted 2-hour no-show "
                "fail. Handoff: prod still ships the leftover pass-first compiled program."
            ),
            ticket=(
                "Title: guidance select pass/fail leftover pass-first; compiled .guidance still "
                "picks pass on planted 2-hour no-show."
            ),
            src="evals/noshow_judge.py",
            src_obs="{{select 'label' options=['pass', 'fail']}}\ncompile_cache='.guidance/'",
            run="evals/noshow_judge.py",
            fail_obs="planted 2h no-show label=pass. compile_cache hit leftover program",
            inspect=".guidance/noshow.prog",
            inspect_obs="compiled token order pass then fail. cache mtime older than source",
            first_path="evals/noshow_judge.py",
            first_old="options=['pass', 'fail']",
            first_new="options=['fail', 'pass']",
            first_obs="source reversed. leftover .guidance/noshow.prog still pass-first",
            rate_tail="compiled leftover program still pass-first",
            still_after_429="compile cache leftover; planted still pass",
            grep="guidance|compile_cache|select",
            grep_obs="must delete .guidance/ and hash source into cache key",
            plan_change="bust compile cache; key includes source bytes; prod handoff leftover",
            fix_path="evals/noshow_judge.py",
            fix_old="compile_cache='.guidance/'",
            fix_new="compile_cache=None  # do not reuse leftover programs",
            fix_obs="local planted fail. prod image still COPY .guidance HANDOFF",
            retry_obs="502 unused. prod leftover compiled program. Partial",
            test="tests/test_guidance_select_order.py",
            test_body="xfail prod image COPY .guidance; local select fail-first",
            test_obs="prod compiled leftover. Partial",
            suite_obs="local fail-first. prod leftover program. Partial.",
            gate_obs="local fail-first. prod leftover program. Partial.",
            diff_obs=" evals/noshow_judge.py | 4+-\n HANDOFF .guidance in image\n",
            residual="Prod image still COPY leftover pass-first compiled program. Partial.",
        ),
    )
)

# ---------------------------------------------------------------------------
# r296 metric leftover — not Faithfulness empty-ctx, not instructor classname
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="task-completion-tools-alias-b67i",
            domain="refund-tools",
            kind="metric",
            avoided="r261 instructor tool classname; r6 toolcorrectness args; Faithfulness empty-ctx",
            goal=(
                "TaskCompletionMetric leftover still reads expected_outcome after the field was "
                "renamed to expected_tools. Empty expected yields 1.0 while the agent called "
                "ChargeCard instead of RefundCard. Pass expected_tools; fail if the field missing."
            ),
            plan="Dump metric kwargs, stop aliasing outcome, require expected_tools list.",
            outcome=(
                "Harness passes expected_tools=['RefundCard']. Planted ChargeCard 0.12 fail-closed. "
                "Missing field raises. Residual: old notebooks still construct expected_outcome."
            ),
            ticket=(
                "Title: TaskCompletion 1.0 on planted ChargeCard. expected_tools renamed; leftover "
                "expected_outcome=None treated as success."
            ),
            src="evals/task_completion.py",
            src_obs=(
                "TaskCompletionMetric().measure(tc)\n"
                "tc.expected_outcome leftover alias; expected_tools never set"
            ),
            run="evals/task_completion.py",
            fail_obs="planted ChargeCard vs gold RefundCard score=1.0 expected_outcome is None",
            inspect="evals/task_completion.py",
            inspect_obs="empty expected leftover → metric short-circuit 1.0",
            first_path="evals/task_completion.py",
            first_old="expected_outcome=gold.outcome",
            first_new="expected_outcome=gold.tools",
            first_obs="alias still a string; metric wants list of tool names; still 1.0",
            rate_tail="string alias leftover; metric still empty-list success",
            still_after_429="expected_tools still unset; 1.0 leftover",
            grep="expected_tools|expected_outcome|TaskCompletion",
            grep_obs="set expected_tools list; fail if missing",
            plan_change="pass expected_tools list; raise if neither field present",
            fix_path="evals/task_completion.py",
            fix_old="TaskCompletionMetric().measure(tc)",
            fix_new="TaskCompletionMetric().measure(tc) if tc.expected_tools else raise MissingTools()",
            fix_obs="planted ChargeCard 0.12. missing field raises",
            retry_obs="502 then retry; 5 pass 1 fail planted ChargeCard 0.12",
            test="tests/test_task_completion_expected_tools.py",
            test_body="assert metric sees expected_tools; missing raises MissingTools",
            test_obs="test_expected_tools_required_not_outcome_alias",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed ChargeCard",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed ChargeCard",
            diff_obs=" evals/task_completion.py | 8+-\n tests/test_task_completion_expected_tools.py | 16++\n",
            residual="Old notebooks still construct expected_outcome=None.",
        ),
        _bad(
            slug="json-correctness-addl-props-c68j",
            domain="ship-promise",
            kind="metric",
            avoided="r254 GEval extra=forbid; JsonCorrectness r01 additionalProperties; Faithfulness empty-ctx",
            goal=(
                "JsonCorrectnessMetric leftover schema additionalProperties true lets a planted "
                "expedite:true extra key pass. Pin additionalProperties false and fail extra keys."
            ),
            plan="Dump schema $id, forbid extra keys, prove planted expedite fail.",
            outcome=(
                "Local schema additionalProperties=false. Planted expedite extra key fails. "
                "Handoff: schema registry still publishes additionalProperties true."
            ),
            ticket=(
                "Title: JsonCorrectness 1.0 with extra expedite true. leftover additionalProperties "
                "true on shipping schema."
            ),
            src="evals/json_correctness.py",
            src_obs="schema additionalProperties: true  # leftover so unknown keys do not break old clients",
            run="evals/json_correctness.py",
            fail_obs="planted {window:'2h', expedite:true} score=1.0 extra key allowed",
            inspect="schemas/shipping_reply.json",
            inspect_obs="additionalProperties true leftover. $id shipping-reply-v3",
            first_path="schemas/shipping_reply.json",
            first_old='"additionalProperties": true',
            first_new='"additionalProperties": false',
            first_obs="local false. CI pulls schema registry v3 still true",
            rate_tail="registry leftover additionalProperties true",
            still_after_429="CI schema registry leftover true; planted still 1.0",
            grep="additionalProperties|shipping-reply",
            grep_obs="pin local file; registry still leftover true",
            plan_change="local file pin + fail extra keys; handoff registry",
            fix_path="evals/json_correctness.py",
            fix_old="schema = registry.get('shipping-reply-v3')",
            fix_new="schema = json.loads(Path('schemas/shipping_reply.json').read_text())",
            fix_obs="local planted fail. registry leftover true HANDOFF",
            retry_obs="502 unused. registry leftover. Partial",
            test="tests/test_json_correctness_extra_keys.py",
            test_body="xfail registry v3; local additionalProperties false",
            test_obs="registry leftover. Partial",
            suite_obs="local extra key fails. registry leftover true. Partial.",
            gate_obs="local extra key fails. registry leftover true. Partial.",
            diff_obs=" schemas/shipping_reply.json | 2+-\n evals/json_correctness.py | 4+-\n HANDOFF registry\n",
            residual="Schema registry still publishes additionalProperties true. Partial.",
        ),
    )
)

# ---------------------------------------------------------------------------
# r297 trace leftover — not r293 sample_rate, not r257 ended span
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="otel-baggage-score-overwrite-d69k",
            domain="tax-quote",
            kind="trace",
            avoided="r293 tracing sample_rate; r257 otel span already ended; r16 @observe sample",
            goal=(
                "Parent CI leftover OTEL baggage eval.score=1.0 is preferred by the exporter over "
                "the metric score 0.16 on a planted tax-exclusive quote. Ignore baggage; read "
                "metric attributes only; fail-closed on planted 0.16."
            ),
            plan="Dump baggage, stop preferring it, export metric.score, prove planted tax fail.",
            outcome=(
                "Exporter ignores baggage eval.score. Planted tax-exclusive 0.16 fail-closed. "
                "Residual: the lint job still injects leftover baggage for dashboards."
            ),
            ticket=(
                "Title: planted tax-exclusive quote metric 0.16 exported as 1.0. leftover baggage "
                "eval.score from parent GHA job."
            ),
            src="evals/otel_exporter.py",
            src_obs="score = baggage.get('eval.score') or span.attributes.get('metric.score')",
            run="evals/tax_quote_eval.py",
            fail_obs="metric.score=0.16 exported 1.0 baggage leftover eval.score=1.0",
            inspect="evals/otel_exporter.py",
            inspect_obs="baggage preferred leftover. parent job sets eval.score=1.0 for 'green dashboards'",
            first_path="evals/otel_exporter.py",
            first_old="baggage.get('eval.score') or span.attributes.get('metric.score')",
            first_new="span.attributes.get('metric.score') or baggage.get('eval.score')",
            first_obs="still falls back to leftover baggage when attribute missing on sampled spans",
            rate_tail="fallback leftover baggage 1.0 on unattributed spans",
            still_after_429="baggage fallback leftover; planted export 1.0",
            grep="baggage|eval.score|metric.score",
            grep_obs="never read baggage for scores; fail if attribute missing",
            plan_change="ignore baggage; require metric.score attribute; fail-closed if absent",
            fix_path="evals/otel_exporter.py",
            fix_old="span.attributes.get('metric.score') or baggage.get('eval.score')",
            fix_new="span.attributes['metric.score']  # KeyError fail-closed; ignore baggage",
            fix_obs="planted export 0.16. missing attribute fails the job",
            retry_obs="502 then retry; 5 pass 1 fail planted tax-exclusive 0.16",
            test="tests/test_otel_baggage_ignored.py",
            test_body="assert exporter ignores baggage; missing attribute raises",
            test_obs="test_exporter_ignores_eval_score_baggage",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed tax-exclusive",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed tax-exclusive",
            diff_obs=" evals/otel_exporter.py | 5+-\n tests/test_otel_baggage_ignored.py | 12++\n",
            residual="Lint job still injects leftover baggage eval.score=1.0 for dashboards.",
        ),
        _bad(
            slug="jaeger-service-rename-orphan-e70l",
            domain="appt-window",
            kind="trace",
            avoided="r293 tracing sample_rate; r257 otel ended span; r16 @observe",
            goal=(
                "After renaming the trace service to eval-harness, leftover Jaeger queries still "
                "filter service=deepeval-eval so planted appointment-window fail spans are "
                "invisible to the Grafana alert. Point the alert at the new service."
            ),
            plan="Dump service name, dual-write briefly, move alert, prove planted span visible.",
            outcome=(
                "Local exporter service=eval-harness. Planted 2-hour window span 0.19 visible in "
                "local Jaeger. Handoff: Grafana alert still filters leftover deepeval-eval."
            ),
            ticket=(
                "Title: Grafana eval alert never fires. leftover service name deepeval-eval after "
                "rename to eval-harness. planted appointment-window fail is on the new name."
            ),
            src="evals/tracing_service.py",
            src_obs="Resource.create({'service.name': os.getenv('OTEL_SERVICE_NAME', 'eval-harness')})",
            run="evals/appt_window_eval.py",
            fail_obs="spans on eval-harness. Grafana query service=deepeval-eval leftover 0 series",
            inspect="grafana/eval-alert.json",
            inspect_obs="expr: {service_name=\"deepeval-eval\"} leftover after rename",
            first_path="evals/tracing_service.py",
            first_old="os.getenv('OTEL_SERVICE_NAME', 'eval-harness')",
            first_new="os.getenv('OTEL_SERVICE_NAME', 'deepeval-eval')  # dual-write old name",
            first_obs="dual-write old name. Grafana still 0 series for planted because sampler leftover",
            rate_tail="alert still leftover deepeval-eval and sampler drops planted",
            still_after_429="Grafana leftover filter; planted invisible",
            grep="deepeval-eval|eval-harness|service.name",
            grep_obs="cannot edit org Grafana from this repo; local jaeger ok",
            plan_change="keep new service name; document Grafana leftover handoff",
            fix_path="evals/tracing_service.py",
            fix_old="os.getenv('OTEL_SERVICE_NAME', 'deepeval-eval')  # dual-write old name",
            fix_new="os.getenv('OTEL_SERVICE_NAME', 'eval-harness')",
            fix_obs="local jaeger shows planted 0.19. Grafana leftover HANDOFF",
            retry_obs="502 unused. Grafana leftover filter. Partial",
            test="tests/test_trace_service_name.py",
            test_body="assert service.name eval-harness; xfail grafana leftover",
            test_obs="Grafana leftover filter. Partial",
            suite_obs="local planted span visible. Grafana leftover. Partial.",
            gate_obs="local planted span visible. Grafana leftover. Partial.",
            diff_obs=" evals/tracing_service.py | 2+-\n HANDOFF grafana/eval-alert.json\n",
            residual="Grafana alert still filters leftover service deepeval-eval. Partial.",
        ),
    )
)
